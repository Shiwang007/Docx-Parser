import os
import io
import json
import base64
import re
import uuid
import docx
from docx import Document
import matplotlib.pyplot as plt
from matplotlib import mathtext
from lxml import etree

# Constants for subject detection
SUBJECT_DATABASE = {
    "Physics": ["physics", "kinematics", "thermodynamics", "optics", "magnetism", "electrostatics", "force", "energy", "ph", "physics"],
    "Chemistry": ["chemistry", "organic", "inorganic", "molecular", "reaction", "acid", "base", "atom", "molecule", "bond", "ch"],
    "Biology": ["biology", "botany", "zoology", "anatomy", "cell", "tissue", "gene", "bi", "bo", "zo"],
    "Mathematics": ["mathematics", "calculus", "integration", "geometry", "algebra", "trigonometry", "matrix", "vector", "ma"]
}

def render_latex_to_base64(latex_str):
    """Renders a LaTeX string to a base64 encoded PNG using Matplotlib."""
    try:
        # Wrap in $ if not already
        if not latex_str.startswith('$'):
            latex_str = f'${latex_str}$'
        
        # Headless Agg backend
        plt.switch_backend('Agg')
        
        fig = plt.figure(figsize=(0.1, 0.1))
        fig.text(0, 0, latex_str, fontsize=15, color='white') # White text for dark mode viewer
        
        # Auto-sizing
        buf = io.BytesIO()
        fig.savefig(buf, format='png', transparent=True, bbox_inches='tight', pad_inches=0.05)
        plt.close(fig)
        
        buf.seek(0)
        return f"data:image/png;base64,{base64.b64encode(buf.read()).decode('utf-8')}"
    except Exception as e:
        print(f"[!] Rendering error: {e}")
        return None

def detect_subject(text_sample):
    """Detects the subject based on keyword density."""
    sample_lower = text_sample.lower()
    scores = {s: 0 for s in SUBJECT_DATABASE}
    
    for subject, keywords in SUBJECT_DATABASE.items():
        for kw in keywords:
            if kw in sample_lower:
                scores[subject] += sample_lower.count(kw)
    
    # Return highest score subject, default to Physics as a fallback
    detected = max(scores, key=scores.get)
    return detected if scores[detected] > 0 else "Physics"

def get_text_with_formatting(paragraph):
    """Processes a paragraph and returns text with sub/superscript HTML tags."""
    html_text = ""
    for run in paragraph.runs:
        text = run.text
        if run.font.subscript:
            html_text += f"<sub>{text}</sub>"
        elif run.font.superscript:
            html_text += f"<sup>{text}</sup>"
        else:
            html_text += text
    return html_text

def run_legacy_pipeline(docx_path):
    """Main pipeline to convert Docx to the exact JSON format needed by parseDppFile.js."""
    doc = Document(docx_path)
    
    # 1. Full Text for Subject Detection
    full_text_sample = "\n".join([p.text for p in doc.paragraphs[:20]])
    subject = detect_subject(full_text_sample)
    print(f"[*] Detected Subject: {subject}")

    questions = []
    current_q = None
    
    # Simple regex-based splitting for this legacy tool (Modeled after parseDppFile.js logic)
    # This tool assumes standard @, ~, $ markers for simplicity.
    
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text: continue

        # Permissive Question Start Detection
        # Searches for markers anywhere in the line to handle 'Q1: @@' etc.
        q_type_search = re.search(r'(@@|~~|\$\$)', text)
        if q_type_search:
            if current_q: questions.append(current_q)
            
            marker = q_type_search.group(1)
            q_type = "single-correct"
            if marker == "~~": q_type = "multi-correct"
            elif marker == "$$": q_type = "integer"
            
            # Clean text: remove the marker and everything before it if it looks like a prefix
            # e.g. "Question 1: @@ This is text" -> "This is text"
            cleaned_question_line = get_text_with_formatting(para)
            cleaned_question_line = re.sub(r'^.*?' + re.escape(marker), "", cleaned_question_line).strip()

            current_q = {
                "questionId": f"{uuid.uuid4().hex[:8]}_{len(questions)}",
                "questionType": q_type,
                "testPaperId": "LEGACY_CONVERSION",
                "questionFormat": "text",
                "question": cleaned_question_line,
                "options": [],
                "marks": "4",
                "negativeMarks": "1",
                "subject": subject,
                "correctAnswer": [],
                "metadata": {"accessType": "premium"}
            }
        
        elif text.startswith("-") and current_q:
            # Option
            current_q["options"].append({
                "value": get_text_with_formatting(para).replace("-", "", 1).strip(),
                "format": "text"
            })
            
        elif text.startswith("#") and current_q:
            # Answer
            current_q["correctAnswer"].append(text.replace("#", "", 1).strip())
            
        elif current_q:
            # Append to question body
            current_q["question"] += " " + get_text_with_formatting(para)

    if current_q: questions.append(current_q)

    # 3. Post-Process Math rendering
    # Simple logic: detect anything that looks like latex in the text (e.g. between $)
    for q in questions:
        # Check Question Text
        q["question"] = render_math_in_string(q["question"])
        # Check Options
        for opt in q["options"]:
            opt["value"] = render_math_in_string(opt["value"])

    return questions

def render_math_in_string(text):
    """Finds latex patterns and replaces them with <img> tags."""
    # Look for common latex wrappers or if none, assume anything with \ is math
    # For now, let's look for $...$
    def replace_math(match):
        latex = match.group(1)
        b64 = render_latex_to_base64(latex)
        if b64:
            return f'<img src="{b64}" class="inline-formula" alt="formula">'
        return match.group(0)

    return re.sub(r'\$(.*?)\$', replace_math, text)

# Mock endpoint logic for testing
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        res = run_legacy_pipeline(sys.argv[1])
        print(json.dumps(res, indent=2))
