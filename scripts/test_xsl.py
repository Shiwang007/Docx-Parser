import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..\src')))

from lxml import etree

def test_xsl():
    omml_str = """<m:oMath xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><m:m><m:mr><m:e><m:r><m:t>1</m:t></m:r></m:e><m:e><m:r><m:t>2</m:t></m:r></m:e></m:mr><m:mr><m:e><m:r><m:t>3</m:t></m:r></m:e><m:e><m:r><m:t>4</m:t></m:r></m:e></m:mr></m:m></m:oMath>"""
    xsl_content = open('omml2tex.xsl', 'r', encoding='utf-8').read()
    
    xslt_root = etree.XML(xsl_content.encode('utf-8'))
    transform = etree.XSLT(xslt_root)
    
    omml_node = etree.fromstring(omml_str.encode('utf-8'))
    result = transform(omml_node)
    print(f"Result: {repr(str(result))}")

if __name__ == "__main__":
    test_xsl()
