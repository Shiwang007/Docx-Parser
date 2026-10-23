import os
import shutil
import uuid
import json
import math
import zipfile
import tempfile
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
from pypdf import PdfReader, PdfWriter

from scripts.pipeline import run_preview_pipeline, finalize_existing_json
from scripts.legacy_transformer import transform_to_legacy
from scripts.legacy_pipeline import run_legacy_pipeline

app = FastAPI(title="Medjeex Exam Studio API")

# Setup directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
WEB_DIR = os.path.join(BASE_DIR, "web")

for d in [DATA_DIR, OUTPUT_DIR, WEB_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

# Serve static files from /web and /output
app.mount("/web", StaticFiles(directory=WEB_DIR), name="web")
app.mount("/output", StaticFiles(directory=OUTPUT_DIR), name="output")

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(WEB_DIR, "index.html"))

@app.post("/api/upload")
async def upload_files(
    question_doc: UploadFile = File(...),
    answer_doc: Optional[UploadFile] = File(None)
):
    try:
        # Save question doc
        q_ext = os.path.splitext(question_doc.filename)[1]
        q_id = f"upload_{uuid.uuid4().hex[:8]}"
        q_path = os.path.join(DATA_DIR, f"{q_id}{q_ext}")
        
        with open(q_path, "wb") as buffer:
            shutil.copyfileobj(question_doc.file, buffer)
            
        a_path = None
        if answer_doc and answer_doc.filename:
            a_ext = os.path.splitext(answer_doc.filename)[1]
            a_path = os.path.join(DATA_DIR, f"{q_id}_key{a_ext}")
            with open(a_path, "wb") as buffer:
                shutil.copyfileobj(answer_doc.file, buffer)
        
        return {
            "success": True,
            "q_path": q_path,
            "a_path": a_path,
            "original_name": os.path.splitext(question_doc.filename)[0]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/process")
async def process_exam(
    q_path: str = Form(...),
    a_path: Optional[str] = Form(None),
    title: str = Form(...)
):
    try:
        # Use sanitized title for filename if possible, or just the original name
        clean_title = "".join(c for c in title if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')
        
        preview_json_path = run_preview_pipeline(q_path, clean_title, a_path)
        
        return {
            "success": True,
            "preview_file": os.path.basename(preview_json_path),
            "title": title
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/api/finalize")
async def finalize_exam(filename: str = Form(...)):
    try:
        # Resolve path
        intermediate_path = os.path.join(OUTPUT_DIR, filename)
        if not os.path.exists(intermediate_path):
            raise Exception("Preview file not found")
            
        final_json_path = finalize_existing_json(intermediate_path)
        
        return {
            "success": True,
            "final_file": os.path.basename(final_json_path)
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/api/finalize/legacy")
async def finalize_legacy_exam(
    filename: str = Form(...),
    paper_type: Optional[str] = Form("normal")
):
    try:
        # Resolve path
        intermediate_path = os.path.join(OUTPUT_DIR, filename)
        if not os.path.exists(intermediate_path):
            raise Exception("Preview file not found")
            
        legacy_questions = transform_to_legacy(intermediate_path, paper_type=paper_type)
        
        # Save legacy file for posterity/download
        legacy_filename = f"legacy_{filename}"
        legacy_path = os.path.join(OUTPUT_DIR, legacy_filename)
        with open(legacy_path, 'w', encoding='utf-8') as f:
            json.dump(legacy_questions, f, indent=2, ensure_ascii=False)
            
        return {
            "success": True,
            "final_file": legacy_filename,
            "questions": legacy_questions
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

# --- PDF Toolbox Endpoints ---

@app.post("/api/pdf/process")
async def process_pdf(
    pdf_file: UploadFile = File(...),
    mode: str = Form(...), # 'split' or 'compress'
    value: int = Form(60)   # Quality for compress, Chunk Size for split
):
    try:
        # Save uploaded PDF to a temporary location
        temp_id = uuid.uuid4().hex[:8]
        input_filename = pdf_file.filename
        input_name_root = os.path.splitext(input_filename)[0]
        temp_input_path = os.path.join(DATA_DIR, f"pdf_{temp_id}.pdf")
        
        with open(temp_input_path, "wb") as buffer:
            shutil.copyfileobj(pdf_file.file, buffer)

        reader = PdfReader(temp_input_path)
        total_pages = len(reader.pages)

        if mode == 'split':
            chunk_size = value
            num_chunks = math.ceil(total_pages / chunk_size)
            zip_filename = f"{input_name_root}_split.zip"
            zip_path = os.path.join(OUTPUT_DIR, zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for i in range(num_chunks):
                    writer = PdfWriter()
                    start = i * chunk_size
                    end = min(start + chunk_size, total_pages)
                    for pg_num in range(start, end):
                        writer.add_page(reader.pages[pg_num])
                    
                    chunk_name = f"{input_name_root}_chunk_{i+1:02d}.pdf"
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_chunk:
                        temp_chunk_path = temp_chunk.name
                    
                    writer.write(temp_chunk_path)
                    zipf.write(temp_chunk_path, chunk_name)
                    if os.path.exists(temp_chunk_path):
                        os.unlink(temp_chunk_path)

            return {
                "success": True,
                "message": f"Split into {num_chunks} chunks",
                "download_file": zip_filename,
                "mode": "split"
            }

        elif mode == 'compress':
            quality = value
            output_filename = f"{input_name_root}_compressed.pdf"
            output_path = os.path.join(OUTPUT_DIR, output_filename)
            
            writer = PdfWriter(clone_from=temp_input_path)
            
            # Lossless structural compression
            for page in writer.pages:
                try: page.compress_content_streams()
                except: pass
            
            # Image optimization
            for page in writer.pages:
                for img in page.images:
                    try: img.replace(img.image, quality=quality)
                    except: pass
            
            with open(output_path, "wb") as f:
                writer.write(f)

            reduction_val = 0
            try:
                orig_size = os.path.getsize(temp_input_path)
                new_size = os.path.getsize(output_path)
                reduction_val = ((orig_size - new_size)/orig_size*100)
            except: pass

            return {
                "success": True,
                "message": "Compression successful",
                "download_file": output_filename,
                "mode": "compress",
                "reduction": f"{reduction_val:.1f}%"
            }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )
# --- Emergency Legacy Bridge ---

@app.get("/legacy")
async def read_legacy():
    return FileResponse(os.path.join(WEB_DIR, "legacy.html"))

@app.post("/api/legacy/convert")
async def convert_legacy_docx(docx_file: UploadFile = File(...)):
    try:
        # Save temp file
        temp_id = uuid.uuid4().hex[:8]
        temp_path = os.path.join(DATA_DIR, f"legacy_{temp_id}.docx")
        
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(docx_file.file, buffer)
            
        # Run Legacy Pipeline
        questions = run_legacy_pipeline(temp_path)
        
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)
            
        subject = questions[0]["subject"] if questions else "Unknown"
        
        return {
            "success": True,
            "questions": questions,
            "subject": subject,
            "count": len(questions)
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

if __name__ == "__main__":
    print("[*] Starting Medjeex Exam Studio at http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)
