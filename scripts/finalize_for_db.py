import json
import re
import os
import sys

def transform_text_to_tags(text, all_placeholders, used_placeholders):
    """
    Replaces {{img_1}} with <med_img id='img_1' placement='...' /> 
    and tracks used placeholders.
    """
    if not text:
        return ""
    
    def replacer(match):
        pid = match.group(1)
        if pid not in all_placeholders:
            return match.group(0) # Keep original if not found
        
        p_info = all_placeholders[pid]
        category = p_info.get('category', 'image' if pid.startswith('img') else 'formula' if pid.startswith('formula') else 'table')
        placement = p_info.get('placement', 'inline')
        
        # Track for the question's local asset map
        # Carry over ONLY relevant fields based on category
        if category == 'formula':
            # Formulas don't need placement, data, unsupported, etc.
            used_placeholders[pid] = {
                "pid": pid,
                "category": category,
                "latex": p_info.get('latex'),
                "is_display": p_info.get('is_display', False)
            }
        elif category == 'image':
            used_placeholders[pid] = {
                "pid": pid,
                "category": category,
                "placement": placement,
                "data": p_info.get('data')
            }
        else: # Table or other
            used_placeholders[pid] = {
                "pid": pid,
                "category": category,
                "placement": placement
            }
            # Copy all extra data for tables (like 'rows')
            for k, v in p_info.items():
                if k not in ['pid', 'category', 'placement', 'is_unsupported', 'error_msg']:
                    used_placeholders[pid][k] = v
        
        # Create tag
        tag_name = f"med_{category}"
        return f"<{tag_name} id='{pid}' placement='{placement}' />"

    # Regex for {{img_1}}, {{formula_1}}, {{table_1}}
    return re.sub(r'\{\{(img_\d+|formula_\d+|table_\d+)\}\}', replacer, text)

def finalize_for_db(json_path, output_path):
    print(f"Reading from: {json_path}")
    with open(json_path, 'r', encoding='utf-8') as f:
        doc_data = json.load(f)
    
    all_placeholders = doc_data.get('placeholders', {})
    db_ready_questions = []

    for section in doc_data.get('sections', []):
        # Extract subject from section name (e.g., "Physics Minor Test" -> "Physics")
        raw_subject = section.get('name', 'Unspecified')
        subject = raw_subject.split()[0] if raw_subject else "General"
        
        # Valid subjects from Mongoose enum
        valid_subjects = ["Physics", "Chemistry", "Mathematics", "Botany", "Science", "Zoology", "Biology", "English", "Social Science", "Mental Ability"]
        if subject not in valid_subjects:
            # Try to match case-insensitively
            found = False
            for vs in valid_subjects:
                if subject.lower() == vs.lower():
                    subject = vs
                    found = True
                    break
            if not found:
                subject = "Science" # Default fallback
                
        print(f"Processing Section: {raw_subject} -> Subject: {subject}")

        for q in section.get('questions', []):
            used_placeholders = {}
            
            # 1. Transform text and options and create a lookup for labels
            transformed_question_text = transform_text_to_tags(q.get('text', ''), all_placeholders, used_placeholders)
            
            label_to_value = {}
            transformed_options = []
            for opt in q.get('options', []):
                label = opt.get('label', '')
                opt_text = transform_text_to_tags(opt.get('text', ''), all_placeholders, used_placeholders)
                transformed_options.append({
                    "value": opt_text,
                    "format": "text"
                })
                if label:
                    label_to_value[label] = opt_text
            
            # 2. Handle Correct Answers (Map Label -> Exact Value) and Type
            correct_labels = q.get('correctAnswer', [])
            correct_values = []
            for label in correct_labels:
                if label in label_to_value:
                    correct_values.append(label_to_value[label])
                else:
                    # Fallback if label is missing or doesn't match (keep label as backup)
                    correct_values.append(label)

            q_type = "multi-correct" if len(correct_values) > 1 else "single-correct"
            
            # 3. Build Mongoose-Ready Object
            db_q = {
                "questionType": q_type,
                "questionFormat": "text",
                "question": transformed_question_text,
                "options": transformed_options,
                "marks": "4",
                "negativeMarks": "1",
                "subject": subject,
                "correctAnswer": correct_values,
                "placeholders": used_placeholders
            }
            
            db_ready_questions.append(db_q)
            
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(db_ready_questions, f, indent=2, ensure_ascii=False)
    
    print(f"\nTransformation complete!")
    print(f"Total questions processed: {len(db_ready_questions)}")
    print(f"Saved to: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/finalize_for_db.py <input_json> [output_json]")
        sys.exit(1)
        
    in_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else in_path.replace('.json', '_dbready.json')
    finalize_for_db(in_path, out_path)
