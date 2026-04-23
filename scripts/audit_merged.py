import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..\src')))

import json
import re

def audit_merged():
    with open('AITS_NEET_2026_Structured.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    for section in data['sections']:
        for q in section['questions']:
            # Check if text contains another question number (e.g., "\n2. ")
            if re.search(r'\n\d+\.\s', q['text']):
                print(f"Question {q['number']} ({section['name']}) seems to have MERGED questions!")
                print(f"Snippet: {q['text'][:200]}...")
                print("-" * 20)
            
            # Check if text contains an option marker (A) that wasn't split
            if re.search(r'\s\([A-D]\)\s', q['text']):
                print(f"Question {q['number']} ({section['name']}) has UNSPLIT options in text!")
                print(f"Snippet: {q['text'][:200]}...")
                print("-" * 20)

if __name__ == "__main__":
    audit_merged()
