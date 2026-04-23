import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..\src')))

import json

def audit():
    with open('AITS_NEET_2026_Structured.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    for section in data['sections']:
        for q in section['questions']:
            if not q['options']:
                print(f"Question {q['number']} ({section['name']}) has NO options.")
                print(f"Text snippet: {q['text'][:100]}...")
                print("-" * 20)

if __name__ == "__main__":
    audit()
