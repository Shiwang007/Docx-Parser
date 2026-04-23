import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..\src')))

from docx import Document
from lxml import etree

def debug_matrices():
    doc = Document('DPP-01_Matrices_Maths_Nishant Sir.docx')
    for i, p in enumerate(doc.paragraphs[:30]):
        print(f"P[{i}] text: {repr(p.text)}")
        if '<m:oMath' in p._element.xml:
             print(f"--- P[{i}] contains Math ---")
             # Print a snippet of the math XML
             print(etree.tostring(p._element, encoding='unicode', pretty_print=True)[:2000])

if __name__ == "__main__":
    debug_matrices()
