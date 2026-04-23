import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..\src')))

from docx import Document
from lxml import etree

def debug_q73_xml():
    doc = Document('Test-03_Class-XI+XII_AITS_NEET 2026.docx')
    found = False
    for p in doc.paragraphs:
        if 'Both (A) and (R) are correct but (R) is not the correct explanation of (A)' in p.text:
            print(f"Found Option block: {repr(p.text)}")
            print(etree.tostring(p._element, encoding='unicode', pretty_print=True))
            found = True
            break
    if not found:
        print("Could not find Q73 options")

if __name__ == "__main__":
    debug_q73_xml()
