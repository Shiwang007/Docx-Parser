import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..\src')))

import os
from lxml import etree

# Sample OMML with m:rad and m:acc
omml_text = """<m:oMath xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<m:acc>
  <m:accPr><m:chr m:val="?"/></m:accPr>
  <m:e><m:r><m:t>B</m:t></m:r></m:e>
</m:acc>
<m:rad>
  <m:radPr><m:degHide m:val="1"/></m:radPr>
  <m:deg/>
  <m:e><m:r><m:t>2</m:t></m:r></m:e>
</m:rad>
</m:oMath>"""

def test_xslt():
    try:
        xslt_doc = etree.parse("omml2tex.xsl")
        transform = etree.XSLT(xslt_doc)
        
        omml_root = etree.fromstring(omml_text)
        result = transform(omml_root)
        
        print("--- Input OMML ---")
        print(omml_text)
        print("\n--- Output LaTeX ---")
        print(str(result))
        
        if not str(result).strip():
            print("\nWARNING: Output is empty!")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_xslt()
