import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..\src')))

from docx import Document
from lxml import etree

def debug_symbols():
    doc = Document('Test-03_Class-XI+XII_AITS_NEET 2026.docx')
    
    for p in doc.paragraphs:
        if 'H2O(s)' in p.text:
            print(f"Found Paragraph: {p.text}")
            # The XML string of the paragraph
            xml = p._element.xml
            tree = etree.fromstring(xml)
            # Find symbols using lxml directly with the correct namespace
            ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            symbols = tree.xpath('.//w:sym', namespaces=ns)
            for sym in symbols:
                 char = sym.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}char')
                 font = sym.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}font')
                 print(f"Symbol found: char='{char}', font='{font}'")
            break

if __name__ == "__main__":
    debug_symbols()
