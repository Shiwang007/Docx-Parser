import os
import sys
import json
import traceback

# Add project root to sys path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.parser_engine import DocxParser
from scripts.merge_answers import merge_answers
from scripts.finalize_for_db import finalize_for_db

def run_preview_pipeline(docx_path, output_base_name, answer_key_path=None):
    """
    Step 1: Extraction and optional Answer Merging.
    Returns the path to the PREVIEWable JSON.
    """
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    raw_json = os.path.join(output_dir, f"{output_base_name}.json")
    
    try:
        # Step 1: Extraction
        print(f"[*] Extracting structure from: {docx_path}")
        parser = DocxParser(docx_path)
        ir_data = parser.parse()
        
        output_data = ir_data.model_dump() if hasattr(ir_data, 'model_dump') else ir_data.dict()
        
        with open(raw_json, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
            
        current_source = raw_json
        
        # Step 2: Key Integration (if provided)
        if answer_key_path and os.path.exists(answer_key_path):
            print(f"[*] Merging answers from: {answer_key_path}")
            merged_json = os.path.join(output_dir, f"{output_base_name}_with_answers.json")
            merge_answers(raw_json, answer_key_path, merged_json)
            current_source = merged_json
            
        # Update Manifest for the Preview
        update_manifest(output_base_name, current_source)
        
        print(f"[+] Preview generated! File: {current_source}")
        return current_source
        
    except Exception as e:
        print(f"[!] Pipeline Error in run_preview_pipeline: {e}")
        import traceback
        traceback.print_exc()
        raise e

def finalize_existing_json(intermediate_json_path):
    """
    Step 2: DB Finalization.
    Converts a checked intermediate JSON to a DB-ready one.
    """
    final_json = intermediate_json_path.replace('.json', '_dbready.json')
    print(f"[*] Finalizing {intermediate_json_path} for DB...")
    finalize_for_db(intermediate_json_path, final_json)
    print(f"[+] Final file created: {final_json}")
    return final_json

def update_manifest(title, filename):
    manifest_path = "output/manifest.json"
    files = []
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r', encoding='utf-8') as f:
            try:
                files = json.load(f)
            except:
                files = []
                
    # Avoid duplicates
    base_filename = os.path.basename(filename)
    # We only show the primary (not dbready) versions in the sidebar
    if "_dbready" in base_filename:
        return

    files = [f for f in files if f.get('filename') != base_filename]
    
    files.insert(0, {
        "title": f"{title}",
        "filename": base_filename
    })
    
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(files, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Medjeex Docx Pipeline")
    parser.add_argument("docx_path", help="Path to the input DOCX file")
    parser.add_argument("output_base_name", help="Base name for the output JSON")
    parser.add_argument("--key", help="Path to the answer key DOCX (optional)")
    
    args = parser.parse_args()
    run_preview_pipeline(args.docx_path, args.output_base_name, args.key)
