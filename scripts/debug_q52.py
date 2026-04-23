import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..\src')))

from docx import Document
from lxml import etree

def debug_q52():
    doc = Document('Test-03_Class-XI+XII_AITS_NEET 2026.docx')
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    
    found = False
    for p in doc.paragraphs:
        if 'r = k' in p.text:
            print(f"Found Paragraph: {p.text}")
            xml = p._element.xml
            tree = etree.fromstring(xml)
            for sym in tree.xpath('.//w:sym', namespaces=ns):
                 char = sym.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}char')
                 font = sym.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}font')
                 print(f"Symbol found: char='{char}', font='{font}'")
            found = True
            
    if not found:
        print("Could not find paragraph with r = k")

if __name__ == "__main__":
    debug_q52()
