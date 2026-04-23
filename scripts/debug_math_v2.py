import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..\src')))

import os
from lxml import etree

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

def debug():
    try:
        omml = etree.fromstring(omml_text.encode('utf-8'))
        xslt_doc = etree.parse("omml2tex.xsl")
        xslt = etree.XSLT(xslt_doc)
        result = xslt(omml)
        print(f"Result: '{str(result)}'")
    except Exception as e:
        print(f"Error during XSLT: {e}")

if __name__ == "__main__":
    debug()
