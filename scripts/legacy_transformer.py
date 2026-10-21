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

def extract_answer_labels(raw_answers):
    """Normalize and split correct answers into clean individual labels."""
    if not raw_answers:
        return []
    if isinstance(raw_answers, (str, int, float)):
        items = [str(raw_answers)]
    elif isinstance(raw_answers, list):
        items = [str(x) for x in raw_answers]
    else:
        items = [str(raw_answers)]

    labels = []
    for item in items:
        parts = re.split(r'[,;/|]|\band\b|\bor\b|&', item, flags=re.IGNORECASE)
        for part in parts:
            cleaned = part.strip()
            cleaned = re.sub(r'^[(\[\{]+|[)\]\}]+$', '', cleaned).strip().rstrip('.').strip()
            if not cleaned:
                continue
            if len(cleaned) > 1 and cleaned.isalpha() and all(c.upper() in 'ABCD' for c in cleaned):
                labels.extend([c.upper() for c in cleaned])
            else:
                labels.append(cleaned)
    return labels

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
            raw_correct = q.get("correctAnswer", [])
            correct_labels = extract_answer_labels(raw_correct)
            legacy_answers = []
            
            # Check if this is an MCQ (has options) or integer type
            options = q.get("options", [])
            has_options = len(options) > 0
            
            for label in correct_labels:
                if has_options:
                    norm_label = re.sub(r'[^a-zA-Z0-9]', '', label).upper()
                    found_opt = next(
                        (o for o in options if re.sub(r'[^a-zA-Z0-9]', '', o.get("label", "")).upper() == norm_label),
                        None
                    )
                    # Support 1-based index mapping if numeric (e.g. 1 -> option 0)
                    if not found_opt and norm_label.isdigit():
                        idx = int(norm_label) - 1
                        if 0 <= idx < len(options):
                            found_opt = options[idx]

                    if found_opt:
                        legacy_answers.append(resolve_placeholders(found_opt["text"], placeholders))
                    else:
                        legacy_answers.append(label)
                else:
                    legacy_answers.append(label)

            # Determine Question Type
            if not has_options:
                q_type = "integer"
            elif len(legacy_answers) > 1 or len(correct_labels) > 1 or q.get("type") == "multi-correct" or q.get("questionType") == "multi-correct":
                q_type = "multi-correct"
            else:
                q_type = "single-correct"

            
            legacy_questions.append({
                "questionId": "",
                "questionType": q_type,
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
