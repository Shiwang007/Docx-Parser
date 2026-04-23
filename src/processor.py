import os
import base64
from typing import Dict, Any, List, Optional
from lxml import etree
from src.models import PlaceholderData

class ContentProcessor:
    def __init__(self):
        self.image_counter = 0
        self.formula_counter = 0
        self.namespaces = {
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
            'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math',
            'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
        }
        self.placeholders = {}

    def process_image(self, rels: Any, rel_id: str, width: Optional[int] = None, height: Optional[int] = None, placement: str = "inline") -> str:
        """Extracts an image from DOCX relationship and returns a placeholder."""
        try:
            rel = rels[rel_id]
            image_part = rel.target_part
            image_bytes = image_part.blob
            ext = os.path.splitext(image_part.partname)[1][1:].lower()
            
            # Use base64 for embedding directly
            encoded = base64.b64encode(image_bytes).decode('utf-8')
            mime = f"image/{ext}" if ext != 'wmf' else "image/x-wmf"
            base64_src = f"data:{mime};base64,{encoded}"
            
            self.image_counter += 1
            placeholder = f"img_{self.image_counter}"
            
            is_unsupported = ext in ['emf', 'wmf']
            
            # Store in the registry
            self.placeholders[placeholder] = PlaceholderData(
                category="image",
                placement=placement,
                data={
                    "base64": base64_src,
                    "width": width,
                    "height": height,
                    "is_unsupported": is_unsupported,
                    "error_msg": "Unsupported Format (EMF/WMF)" if is_unsupported else None
                }
            )
            
            return f"{{{{{placeholder}}}}}"
        except Exception as e:
            print(f"Error processing image: {e}")
            return "[IMAGE_ERROR]"

    def process_formula(self, omml_node: etree._Element, is_display: bool = False) -> str:
        """Converts OMML node to LaTeX string and returns a placeholder."""
        self.formula_counter += 1
        placeholder = f"formula_{self.formula_counter}"
        
        # Native Python recursive conversion from OMML to LaTeX
        latex_str = self._omml_to_latex(omml_node).strip()
        omml_str = etree.tostring(omml_node, encoding='unicode')
        
        # Determine wrapping based on display mode
        # If display mode is requested, use $$ wrapping and add \displaystyle to ensure proper sizing
        if is_display:
            latex_val = f"$$\\displaystyle {latex_str}$$"
        else:
            latex_val = f"${latex_str}$"

        # Store in the registry
        self.placeholders[placeholder] = PlaceholderData(
            category="formula",
            latex=latex_val if latex_str else "",
            raw_omml=omml_str,
            is_display=is_display
        )
        
        return f"{{{{{placeholder}}}}}"

    def get_formula_data(self, omml_node: etree._Element, is_display: bool = False) -> PlaceholderData:
        """Returns the full data for a formula placeholder."""
        omml_str = etree.tostring(omml_node, encoding='unicode')
        latex_str = self._omml_to_latex(omml_node).strip()
        
        if is_display:
            latex_val = f"$$\\displaystyle {latex_str}$$"
        else:
            latex_val = f"${latex_str}$"

        return PlaceholderData(
            category="formula",
            latex=latex_val if latex_str else "",
            raw_omml=omml_str,
            is_display=is_display
        )

    def _omml_to_latex(self, node: etree._Element) -> str:
        """Recursive conversion of OMML tags to LaTeX."""
        if node is None:
            return ""
        
        tag = node.tag.split('}')[-1]
        
        # 1. Base elements that contain math content
        if tag in ["oMath", "oMathPara", "e", "num", "den", "deg", "lim"]:
            return "".join([self._omml_to_latex(c) for c in node])
            
        # 2. Text elements
        elif tag == "t":
            return node.text if node.text else ""
            
        # 3. Fractions (m:f)
        elif tag == "f":
            num = self._find_math_child(node, "num")
            den = self._find_math_child(node, "den")
            return f"\\frac{{{self._omml_to_latex(num)}}}{{{self._omml_to_latex(den)}}}"
            
        # 4. Radicals (m:rad - Square root, etc.)
        elif tag == "rad":
            radPr = self._find_math_child(node, "radPr")
            degHide = "0"
            if radPr is not None:
                degHide_node = self._find_math_child(radPr, "degHide")
                if degHide_node is not None:
                    degHide = degHide_node.get("{http://schemas.openxmlformats.org/officeDocument/2006/math}val", "0")
            
            deg = self._find_math_child(node, "deg")
            e = self._find_math_child(node, "e")
            
            if degHide == "1" or deg is None or not self._omml_to_latex(deg).strip():
                return f"\\sqrt{{{self._omml_to_latex(e)}}}"
            else:
                return f"\\sqrt[{self._omml_to_latex(deg)}]{{{self._omml_to_latex(e)}}}"
                
        # 5. Superscript (m:sSup)
        elif tag == "sSup":
            e = self._find_math_child(node, "e")
            sup = self._find_math_child(node, "sup")
            return f"{self._omml_to_latex(e)}^{{{self._omml_to_latex(sup)}}}"
            
        # 6. Subscript (m:sSub)
        elif tag == "sSub":
            e = self._find_math_child(node, "e")
            sub = self._find_math_child(node, "sub")
            return f"{self._omml_to_latex(e)}_{{{self._omml_to_latex(sub)}}}"
            
        # 7. Sub-Superscript (m:sSubSup)
        elif tag == "sSubSup":
            e = self._find_math_child(node, "e")
            sub = self._find_math_child(node, "sub")
            sup = self._find_math_child(node, "sup")
            return f"{self._omml_to_latex(e)}_{{{self._omml_to_latex(sub)}}}^{{{self._omml_to_latex(sup)}}}"

        # 8. Matrix (m:m)
        elif tag == "m":
            rows = []
            # Find mr (matrix rows)
            for row_node in node:
                if row_node.tag.endswith("mr"):
                    row_elements = []
                    # Find e (elements in the row)
                    for e_node in row_node:
                        if e_node.tag.endswith("e"):
                            row_elements.append(self._omml_to_latex(e_node))
                    rows.append(" & ".join(row_elements))
            row_str = " \\\\ ".join(rows)
            return f"\\begin{{matrix}}{row_str}\\end{{matrix}}"

        # 8. Accents (m:acc - arrows, vectors, dots)
        elif tag == "acc":
            accPr = self._find_math_child(node, "accPr")
            chr_val = "?"
            if accPr is not None:
                chr_node = self._find_math_child(accPr, "chr")
                if chr_node is not None:
                    chr_val = chr_node.get("{http://schemas.openxmlformats.org/officeDocument/2006/math}val", "?")
            
            e = self._find_math_child(node, "e")
            content = self._omml_to_latex(e)
            
            if chr_val in ["\u20d7", "\u2192", "?"]: # Typical vector arrow codes
                return f"\\vec{{{content}}}"
            elif chr_val == "\u0304" or chr_val == "-":
                return f"\\bar{{{content}}}"
            elif chr_val == "^":
                return f"\\hat{{{content}}}"
            else:
                return f"\\tilde{{{content}}}"

        # 9. Delimiters (m:d - brackets)
        elif tag == "d":
            dPr = self._find_math_child(node, "dPr")
            beg = "("
            end = ")"
            if dPr is not None:
                beg_node = self._find_math_child(dPr, "begChr")
                end_node = self._find_math_child(dPr, "endChr")
                if beg_node is not None: beg = beg_node.get("{http://schemas.openxmlformats.org/officeDocument/2006/math}val", "(")
                if end_node is not None: end = end_node.get("{http://schemas.openxmlformats.org/officeDocument/2006/math}val", ")")
            
            e = self._find_math_child(node, "e")
            
            # Cases detection (Piecewise): Opening brace with internal matrix
            if beg == "{" and (not end or end.strip() == ""):
                matrix_node = self._find_math_child(e, "m")
                if matrix_node is not None:
                    rows = []
                    for row_node in matrix_node:
                        if row_node.tag.endswith("mr"):
                            row_elements = []
                            for e_node in row_node:
                                if e_node.tag.endswith("e"):
                                    row_elements.append(self._omml_to_latex(e_node))
                            rows.append(" & ".join(row_elements))
                    rows_joined = ' \\\\ '.join(rows)
                    return f"\\begin{{cases}} {rows_joined} \\end{{cases}}"

            # Map Word brackets to LaTeX
            beg_map = {"(": "\\left(", "[": "\\left[", "{": "\\left\\{", "|": "\\left|"}
            end_map = {")": "\\right)", "]": "\\right]", "}": "\\right\\}", "|": "\\right|"}
            
            left_bracket = beg_map.get(beg, '\\left(' if not beg else f'\\left{beg}')
            right_bracket = end_map.get(end, '\\right)' if not end else f'\\right{end}')
            
            return f"{left_bracket}{self._omml_to_latex(e)}{right_bracket}"

        # 10. n-Ary Operators (m:nary - Summations, Integrals)
        elif tag == "nary":
            naryPr = self._find_math_child(node, "naryPr")
            chr_val = "∑"
            if naryPr is not None:
                chr_node = self._find_math_child(naryPr, "chr")
                if chr_node is not None:
                    chr_val = chr_node.get("{http://schemas.openxmlformats.org/officeDocument/2006/math}val", "∑")
            
            nary_map = {
                "∑": "\\sum", "∫": "\\int", "∬": "\\iint", "∭": "\\iiint",
                "∮": "\\oint", "∏": "\\prod", "∐": "\\coprod", "⋂": "\\bigcap",
                "⋃": "\\bigcup", "⋁": "\\bigvee", "⋀": "\\bigwedge"
            }
            operator = nary_map.get(chr_val, f"\\text{{{chr_val}}}")
            
            sub = self._find_math_child(node, "sub")
            sup = self._find_math_child(node, "sup")
            e = self._find_math_child(node, "e")
            
            latex = operator
            if sub is not None:
                latex += f"_{{{self._omml_to_latex(sub)}}}"
            if sup is not None:
                latex += f"^{{{self._omml_to_latex(sup)}}}"
            if e is not None:
                latex += f"{{{self._omml_to_latex(e)}}}"
            return latex

        # 11. Limits (m:limLow, m:limUpp)
        elif tag == "limLow":
            e = self._find_math_child(node, "e")
            lim = self._find_math_child(node, "lim")
            base = self._omml_to_latex(e).strip()
            if base.lower() == "lim":
                return f"\\lim_{{{self._omml_to_latex(lim)}}} "
            else:
                return f"{{{base}}}_{{{self._omml_to_latex(lim)}}} "

        elif tag == "limUpp":
            e = self._find_math_child(node, "e")
            lim = self._find_math_child(node, "lim")
            return f"{{{self._omml_to_latex(e)}}}^{{{self._omml_to_latex(lim)}}} "

        # 12. Normal Runs (m:r)
        elif tag == "r":
            return "".join([self._omml_to_latex(c) for c in node])

        # 13. Group Characters (m:groupChr)
        elif tag == "groupChr":
            e = self._find_math_child(node, "e")
            gPr = self._find_math_child(node, "groupChrPr")
            chr_val = "→"
            if gPr is not None:
                chr_node = self._find_math_child(gPr, "chr")
                if chr_node is not None:
                    chr_val = chr_node.get("{http://schemas.openxmlformats.org/officeDocument/2006/math}val", "→")
            
            content = self._omml_to_latex(e).strip()
            if chr_val == "→":
                return f"\\xrightarrow{{{content}}}"
            else:
                return f"\\overbrace{{{content}}}"

        # 14. Equation Arrays (m:eqArr)
        elif tag == "eqArr":
            rows = []
            for row in node:
                if row.tag.endswith("e"):
                    rows.append(self._omml_to_latex(row))
            rows_joined = ' \\\\ '.join(rows)
            return f"\\begin{{aligned}} {rows_joined} \\end{{aligned}}"

        # Default: Process children but don't add specific formatting
        return "".join([self._omml_to_latex(c) for c in node])

    def _find_math_child(self, node: etree._Element, tag_name: str) -> Optional[etree._Element]:
        """Heper to find common math children with or without namespace prefix."""
        for child in node:
            if child.tag.endswith(tag_name):
                return child
        return None
