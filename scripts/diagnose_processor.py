import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from processor import ContentProcessor
from lxml import etree

def test():
    p = ContentProcessor()
    # Mocking formula 22 part
    omml = """<m:oMath xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
        <m:r><m:t>2</m:t></m:r>
        <m:d>
            <m:dPr><m:begChr m:val="["/><m:endChr m:val="]"/></m:dPr>
            <m:e>
                <m:m>
                    <m:mr>
                        <m:e><m:r><m:t>x</m:t></m:r></m:e>
                        <m:e><m:r><m:t>1</m:t></m:r></m:e>
                    </m:mr>
                    <m:mr>
                        <m:e><m:r><m:t>0</m:t></m:r></m:e>
                        <m:e><m:r><m:t>3</m:t></m:r></m:e>
                    </m:mr>
                </m:m>
            </m:e>
        </m:d>
    </m:oMath>"""
    
    node = etree.fromstring(omml)
    result = p._omml_to_latex(node)
    print(f"DEBUG: result = {result}")
    
    # Check if 'm' is in the internal dispatch
    print(f"DEBUG: tags handled = {p}")

if __name__ == "__main__":
    test()
