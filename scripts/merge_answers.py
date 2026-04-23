import json
import sys
import os

# Add root directory to sys.path to allow importing from src
sys.path.append(os.getcwd())

from src.answer_parser import AnswerKeyParser

def merge_answers(json_path, docx_path, output_path):
    print(f"Loading questions from: {json_path}")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    print(f"Parsing answer key from: {docx_path}")
    parser = AnswerKeyParser(docx_path)
    answer_map = parser.parse()
    
    merged_count = 0
    missing_count = 0
    
    # Iterate through all questions in all sections
    for section in data.get('sections', []):
        for q in section.get('questions', []):
            q_num_str = str(q.get('number'))
            if q_num_str in answer_map:
                q['correctAnswer'] = answer_map[q_num_str]
                merged_count += 1
            else:
                q['correctAnswer'] = []
                missing_count += 1
                
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    print(f"\nMerging complete!")
    print(f"Successfully merged: {merged_count} answers")
    print(f"Questions missing answers: {missing_count}")
    print(f"Saved final data to: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scripts/merge_answers.py <questions_json> <answer_key_docx> [output_json]")
        sys.exit(1)
        
    json_in = sys.argv[1]
    docx_in = sys.argv[2]
    json_out = sys.argv[3] if len(sys.argv) > 3 else json_in.replace('.json', '_with_answers.json')
    
    merge_answers(json_in, docx_in, json_out)
