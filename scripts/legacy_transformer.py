import os
import io
import json
import base64
import re
import uuid
import matplotlib.pyplot as plt
from matplotlib import mathtext

def render_latex_to_base64(latex_str):
    """Renders a LaTeX string to a base64 encoded PNG using Matplotlib."""
    try:
        # Wrap in $ if not already
        if not latex_str.startswith('$'):
            latex_str = f'${latex_str}$'
        
        # Headless Agg backend for server use
        plt.switch_backend('Agg')
        
        fig = plt.figure(figsize=(0.1, 0.1))
        # Use white text for formulas to stand out on potentially dark backgrounds, 
        # or black if preferred. Standard is black for legacy prints.
        fig.text(0, 0, latex_str, fontsize=15, color='black') 
        
        buf = io.BytesIO()
        fig.savefig(buf, format='png', transparent=True, bbox_inches='tight', pad_inches=0.05)
        plt.close(fig)
        
        buf.seek(0)
        return f"data:image/png;base64,{base64.b64encode(buf.read()).decode('utf-8')}"
    except Exception as e:
        print(f"[!] Rendering error: {e}")
        return None

def resolve_placeholders(text, placeholders):
    """Replaces placeholders with inlined <img> tags."""
    if not text: return ""
    result = text

    # Handle Formulas (Math Rendering)
    def replace_formula(match):
        pid = match.group(1)
        data = placeholders.get(f"formula_{pid}")
        if data and data.get("latex"):
            b64 = render_latex_to_base64(data["latex"])
            if b64:
                return f'<img src="{b64}" class="inline-formula" alt="formula">'
        return match.group(0)

    result = re.sub(r'\{\{formula_(\d+)\}\}', replace_formula, result)

    # Handle Images (Original Docx Images)
    def replace_img(match):
        pid = match.group(1)
        data = placeholders.get(f"img_{pid}")
        if data and data.get("data") and data["data"].get("base64"):
            b64 = data["data"]["base64"]
            return f'<img src="{b64}" class="docx-image" alt="diagram">'
        return match.group(0)

    result = re.sub(r'\{\{img_(\d+)\}\}', replace_img, result)

    return result

def transform_to_legacy(input_json_path):
    """Main transformer to bridge Studio JSON to Legacy DPP JSON."""
    with open(input_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    placeholders = data.get("placeholders", {})
    sections = data.get("sections", [])
    
    # Flatten sections into one list of questions
    legacy_questions = []
    
    for section in sections:
        sec_name = section.get("name", "Unknown")
        
        for q in section.get("questions", []):
            # Resolve Question Text
            q_text = resolve_placeholders(q["text"], placeholders)
            
            # Resolve Options
            legacy_options = []
            for opt in q.get("options", []):
                opt_text = resolve_placeholders(opt["text"], placeholders)
                legacy_options.append({
                    "value": opt_text,
                    "format": "text"
                })
            
            # Resolve Correct Answers
            # Map labels (A, B, C) back to option values as required by legacy schema
            correct_labels = q.get("correctAnswer", [])
            legacy_answers = []
            for label in correct_labels:
                # Find the option with this label
                found_opt = next((o for o in q.get("options", []) if o["label"] == label), None)
                if found_opt:
                    legacy_answers.append(resolve_placeholders(found_opt["text"], placeholders))

            # Final Legacy Object
            legacy_questions.append({
                "questionId": "",
                "questionType": q.get("type", "single-correct"),
                "testPaperId": "",
                "questionFormat": "text",
                "question": q_text,
                "options": legacy_options,
                "marks": "4",
                "negativeMarks": "1",
                "subject": sec_name, # Use section name as subject fallback
                "correctAnswer": legacy_answers
            })

    return legacy_questions

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
        output_data = transform_to_legacy(input_path)
        output_path = input_path.replace('.json', '_legacy.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"[*] Transformed to: {output_path}")
