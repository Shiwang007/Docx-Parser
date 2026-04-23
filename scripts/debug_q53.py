import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..\src')))

from docx import Document
from lxml import etree
import os

def debug_q53_xml():
    doc = Document('Test-03_Class-XI+XII_AITS_NEET 2026.docx')
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
          'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math'}
    
    with open('q53_debug.xml', 'w', encoding='utf-8') as f:
        for p in doc.paragraphs:
            if 'In the sequence of reactions' in p.text:
                xml_str = etree.tostring(p._element, encoding='unicode', pretty_print=True)
                f.write(xml_str)
                print("Wrote Q53 XML to q53_debug.xml")
                break

if __name__ == "__main__":
    debug_q53_xml()
