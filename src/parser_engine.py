import re
from typing import List, Dict, Any, Optional
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from lxml import etree
from src.processor import ContentProcessor
from src.models import ParsedDocument, Section, Question, Option, PlaceholderData

# Common mappings for the 'Symbol' font used in Word
SYMBOL_MAP = {
    '61': 'α', '62': 'β', '67': 'γ', '64': 'δ', '65': 'ε', '66': 'φ', '68': 'η', 
    '69': 'ι', '6B': 'κ', '6C': 'λ', '6D': 'μ', '6E': 'ν', '6F': 'ο', '70': 'π', 
    '71': 'θ', '72': 'ρ', '73': 'σ', '74': 'τ', '75': 'υ', '77': 'ω', '78': 'ξ', 
    '79': 'ψ', '7A': 'ζ',
    '41': 'Α', '42': 'Β', '47': 'Γ', '44': 'Δ', '45': 'Ε', '5A': 'Ζ', '48': 'Η', '51': 'Θ', 
    '4C': 'Λ', '4D': 'Μ', '4E': 'Ν', '58': 'Ξ', '4F': 'Ο', '50': 'Π', 
    '52': 'Ρ', '53': 'Σ', '54': 'Τ', '55': 'Υ', '46': 'Φ', '59': 'Ψ', '57': 'Ω',
    'B1': '±', 'D7': '×', 'B8': '÷', 'BE': '∞', 'D6': '√', 'B6': '∂', 'B4': '×',
    'B9': '≠', 'A3': '≤', 'B3': '≥', 'AA': '×',
    'AB': '⇌', 'D4': '→', 'C4': '→', 'E0': '→', 'F0': '→', 'AE': '→',
    '3D': '=', '2B': '+', '44': 'Δ', 'B0': '°', '21': '!', 'A2': '·',
    'BA': '≡', '2D': '−', 'AD': '−'
}

class DocxParser:
    def __init__(self, docx_path: str):
        self.docx_path = docx_path
        self.doc = Document(docx_path)
        self.processor = ContentProcessor()
        self.namespaces = {
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
            'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math',
            'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
        }
        
        # Regex for question splitting (captures leading images/formulas)
        self.re_question_marker = re.compile(r'^((?:{{.*?}}\s*)*)(\d+)\.\s*(.*)', re.DOTALL)
        self._next_option_expected = 'A'
        self._table_counter = 0

    def parse(self) -> ParsedDocument:
        """Structured scan of the document into Sections, Questions, and Options."""
        doc_data = ParsedDocument(title="AITS NEET - 2026")
        self.doc_data = doc_data # Store for internal access
        
        current_section = None
        current_question = None
        last_context = None # State tracker: 'section', 'question', 'options'
        
        # Regular expressions for detection
        re_section = re.compile(r'(PHYSICS|CHEMISTRY|BIOLOGY|BIO|MATHEMATICS|MATHS|MATH)', re.IGNORECASE)
        re_sub_section = re.compile(r'^SECTION-[AB]$', re.IGNORECASE)
        re_option_marker = re.compile(r'\(([A-D])\)')

        # 0. Global Priority Sweep for Subject Header
        doc_data.sections = []
        global_subject = self._find_subject_globally(re_section)
        current_section = None
        if global_subject:
            print(f"[*] GLOBAL SUBJECT DETECTED: {global_subject}")
            current_section = Section(name=global_subject)
            doc_data.sections.append(current_section)

        for element in self.doc.element.body:
            content = None
            is_text = False
            
            if isinstance(element, CT_P):
                para = Paragraph(element, self.doc)
                content = self._process_paragraph(para)
                is_text = True
            elif isinstance(element, CT_Tbl):
                table = Table(element, self.doc)
                content = self._process_table(table, re_section)
                is_text = True

            if not content:
                continue

            # 1. Check for Section Headers
            if is_text:
                clean_text = self._get_text_recursive(element).strip()
                s_match = re_section.search(clean_text)
                if s_match:
                    section_name = s_match.group(1).upper()
                    if section_name == "BIO": section_name = "Biology"
                    elif section_name == "BIOLOGY": section_name = "Biology"
                    elif section_name in ["MATHS", "MATH", "MATHEMATICS"]: section_name = "Mathematics"
                    elif section_name == "PHYSICS": section_name = "Physics"
                    elif section_name == "CHEMISTRY": section_name = "Chemistry"
                    elif section_name == "BOTANY": section_name = "Botany"
                    elif section_name == "SCIENCE": section_name = "Science"
                    elif section_name == "ZOOLOGY": section_name = "Zoology"
                    elif section_name == "ENGLISH": section_name = "English"
                    elif section_name == "SOCIAL SCIENCE": section_name = "Social Science"
                    elif section_name == "MENTAL ABILITY": section_name = "Mental Ability"
                    elif section_name == "COMBINED": section_name = "Combined"
                    else: section_name = section_name.capitalize()
                    
                    # Dedup: If we already have a section and it matches the global one, skip
                    if current_section and current_section.name == section_name:
                        continue
                    
                    current_section = Section(name=section_name)
                    doc_data.sections.append(current_section)
                    current_question = None
                    last_context = 'section'
                    continue
                
                if re_sub_section.match(clean_text):
                    if current_section:
                        current_section.name = f"{current_section.name} ({clean_text})"
                        last_context = 'section'
                    continue

            # 2. Check for Question Starters
            if is_text:
                q_match = self.re_question_marker.match(content)
                if q_match:
                    prefix = q_match.group(1)
                    q_num = int(q_match.group(2))
                    q_text = prefix + q_match.group(3).strip()
                    current_question = Question(number=q_num, text=q_text)
                    self._next_option_expected = 'A' # Reset state for new question
                    
                    if not current_section:
                        # Fallback: Try to guess subject from filename before defaulting
                        fname = os.path.basename(getattr(self, 'docx_path', '')).upper()
                        guessed_name = "GENERAL"
                        if "PHYSICS" in fname: guessed_name = "Physics"
                        elif "CHEMISTRY" in fname: guessed_name = "Chemistry"
                        elif "BIOLOGY" in fname or "BIO" in fname: guessed_name = "Biology"
                        elif "MATH" in fname: guessed_name = "Mathematics"
                        
                        # Only create a new section if we truly have nothing
                        current_section = Section(name=guessed_name)
                        doc_data.sections.append(current_section)
                    elif current_section.name == "GENERAL":
                        # If we have a fallback 'GENERAL' section but now we are assigning questions,
                        # and we found a better subject globally, we should have already used it.
                        # This block ensures we don't accidentally create a SECOND section later.
                        pass
                    
                    current_section.questions.append(current_question)
                    last_context = 'question'
                    continue

            # 3. Check for Options
            if is_text and re_option_marker.search(content):
                if current_question:
                    self._parse_options_into_question(content, current_question)
                    last_context = 'options'
                    continue

            # 4. Append as generic content to the current context
            if current_question:
                # If we were just parsing options, multiline content belongs to the LAST option
                if last_context == 'options' and current_question.options:
                    current_question.options[-1].text += f" {content.strip()}"
                else:
                    current_question.text += f"\n\n{content}"
            elif current_section:
                doc_data.metadata.setdefault("section_info", []).append(content)
            else:
                doc_data.metadata.setdefault("header_info", []).append(content)

        # Final placeholders are already in self.processor.placeholders
        doc_data.placeholders = self.processor.placeholders
        return doc_data

    def _parse_options_into_question(self, text: str, question: Question):
        """Splits a text block containing (A), (B), etc. into Option objects."""
        # 1. Detect all potential marker matches
        potential_markers = list(re.finditer(r'\(([A-D])\)', text))
        
        if not potential_markers:
            question.text += f"\n\n{text}"
            return

        # 2. Filter for strictly sequential structural markers
        valid_markers = []
        
        for match in potential_markers:
            label = match.group(1)
            
            # For Option A, we have extra checks to avoid matching "Assertion (A)"
            if label == 'A' and self._next_option_expected == 'A':
                pos = match.start()
                prefix = text[:pos].strip().lower()
                # Skip if it's "Assertion (A)" or "Reason (A)"
                if prefix and any(kw in [p.strip() for p in prefix.split()] for kw in ['assertion', 'reason']):
                    continue
                
                # Check structural start (newline, tab, or start of string)
                is_structural = pos == 0 or text[pos-1] in ['\n', '\t', ' '] 
                valid_markers.append(match)
                self._next_option_expected = 'B'
            
            elif label == self._next_option_expected:
                # Structural check for B, C, D
                pos = match.start()
                prev_char = text[pos-1] if pos > 0 else ''
                
                is_valid = False
                if pos == 0 or prev_char in ['\n', '\t']:
                    is_valid = True
                elif pos >= 2 and text[pos-2:pos] == '  ':
                    is_valid = True
                elif pos >= 1 and text[pos-1] == ' ':
                    # Lenient check for multi-column if we strictly expect this letter
                    is_valid = True
                
                if is_valid:
                    valid_markers.append(match)
                    # Increment next expected label globally
                    self._next_option_expected = chr(ord(self._next_option_expected) + 1)
                    if self._next_option_expected > 'D':
                        # Optionally reset if we hit D, but new question will handle it anyway
                        pass 

        if not valid_markers:
            # Smart merging: if we already have options, this text likely belongs to the last one
            if question.options:
                question.options[-1].text += f" {text.strip()}"
            else:
                question.text += f"\n\n{text}"
            return

        # 3. Final splitting and mapping
        # If there is text BEFORE the first valid marker in this block, merge it
        first_marker_start = valid_markers[0].start()
        if first_marker_start > 0:
            prefix_text = text[:first_marker_start].strip()
            if prefix_text:
                if question.options:
                    question.options[-1].text += f" {prefix_text}"
                else:
                    question.text += f"\n\n{prefix_text}"

        for i in range(len(valid_markers)):
            label = valid_markers[i].group(1)
            start = valid_markers[i].end()
            end = valid_markers[i+1].start() if i + 1 < len(valid_markers) else len(text)
            
            option_text = text[start:end].strip()
            
            # Deduplication
            if not any(opt.label == label for opt in question.options):
                question.options.append(Option(label=label, text=option_text))
            else:
                for opt in question.options:
                    if opt.label == label:
                        opt.text += f" {option_text}"

    def _process_paragraph(self, paragraph: Paragraph) -> str:
        """Processes a paragraph, following Word formatting for sub/sup and symbols."""
        para_elements = []
        trailing_elements = []
        para_images = []
        
        for child in paragraph._element:
            tag = child.tag
            
            # Handle standard runs
            if tag.endswith('}r'):
                # Check for subscript/superscript formatting in rPr
                rPr = child.find('.//w:rPr', namespaces=self.namespaces)
                vertAlign = None
                if rPr is not None:
                    va = rPr.find('.//w:vertAlign', namespaces=self.namespaces)
                    if va is not None:
                        vertAlign = va.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                
                run_xml = etree.fromstring(etree.tostring(child))
                for run_child in run_xml:
                    r_tag = run_child.tag
                    
                    if r_tag.endswith('}t'):
                        raw = run_child.text if run_child.text else ""
                        if vertAlign == 'subscript':
                            para_elements.append(f"<sub>{raw}</sub>")
                        elif vertAlign == 'superscript':
                            para_elements.append(f"<sup>{raw}</sup>")
                        else:
                            para_elements.append(raw)
                    
                    elif r_tag.endswith('}sym'):
                        char_code = run_child.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}char')
                        if char_code:
                            code = char_code.upper()
                            if code.startswith('F0'): code = code[2:]
                            para_elements.append(SYMBOL_MAP.get(code, "▯"))
                    
                    elif r_tag.endswith('}br'):
                        para_elements.append("\n")
                    
                    elif r_tag.endswith('}tab'):
                        para_elements.append("\t")
                    
                    elif r_tag.endswith('}drawing') or r_tag.endswith('}pict'):
                        blip_ids = run_child.xpath('.//a:blip/@r:embed | .//v:imagedata/@r:id', 
                                               namespaces={**self.namespaces, 
                                                          'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
                                                          'v': 'urn:schemas-microsoft-com:vml'})
                        if blip_ids:
                            # 1. Extract Width/Height and Placement Type
                            width, height = None, None
                            is_anchor = False
                            drawing_ns = {'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'}
                            extent = run_child.xpath('.//wp:extent', namespaces=drawing_ns)
                            if extent:
                                width = int(extent[0].get('cx', 0))
                                height = int(extent[0].get('cy', 0))
                            
                            if run_child.xpath('.//wp:anchor', namespaces=drawing_ns):
                                is_anchor = True
 
                            # Image logic: 
                            # 1. Width > ~2.5 inches is considered "Large"
                            # 2. Anchored (floating/wrapped) is standalone
                            # 3. Isolated (only thing in paragraph) is standalone (Check at end)
                            is_large = width and width > 2300000 
                            
                            # Initial guess based on obvious properties
                            init_standalone = is_large or is_anchor
                            placement = "standalone" if init_standalone else "inline"
                            
                            placeholder = self.processor.process_image(
                                self.doc.part.rels, blip_ids[0], width, height, placement=placement
                            )
                            
                            # Decide where to place the image:
                            if init_standalone:
                                # Ensure we have a newline before trailing images
                                if not trailing_elements:
                                    trailing_elements.append("\n")
                                trailing_elements.append(placeholder)
                                trailing_elements.append("\n") 
                            else:
                                para_elements.append(placeholder)
                                # Keep track of recently added "inline" placeholders that might be isolated
                                para_images.append(placeholder)

            # Handle Math

            # Handle Math
            elif tag.endswith('}oMath') or tag.endswith('}oMathPara'):
                is_display = tag.endswith('}oMathPara')
                nodes = child.xpath('.//m:oMath', namespaces=self.namespaces) if is_display else [child]
                for m_node in nodes:
                    para_elements.append(self.processor.process_formula(m_node, is_display=is_display))
        
        # Combine inline content with trailing (large/anchored) images
        inline_content = "".join(para_elements).strip()
        trailing_content = "".join(trailing_elements).strip()
        
        # HEURISTIC: If the paragraph is ONLY images (no significant text), promote them to standalone
        # This catches diagrams that are 'inline' in Word but intended as standalone figures.
        if para_images:
            actual_text = inline_content
            for p in para_images:
                actual_text = actual_text.replace(p, "")
            
            if not actual_text.strip():
                # This was a diagram paragraph. Promote all images in it to standalone.
                for p in para_images:
                    # Extract ID from {{img_N}}
                    p_id = p.strip("{}")
                    if p_id in self.processor.placeholders:
                        self.processor.placeholders[p_id].placement = "standalone"

        if trailing_content:
            combined = f"{inline_content}\n\n{trailing_content}"
        else:
            combined = inline_content
            
        return combined if combined or not paragraph.text.strip() else paragraph.text.strip()

    def _process_table(self, table: Table, re_section: re.Pattern) -> str:
        """Processes a native Word table, preserving cell content and checking for subjects."""
        from src.models import TableRow, TableData, PlaceholderData
        
        rows = []
        found_subject = None
        
        for row in table.rows:
            cells = []
            for cell in row.cells:
                # A cell can contain multiple paragraphs
                cell_content_list = []
                for para in cell.paragraphs:
                    para_text = self._process_paragraph(para)
                    cell_content_list.append(para_text)
                    
                    # Check for subject match inside the cell
                    s_match = re_section.search(para_text)
                    if s_match and not found_subject:
                        found_subject = s_match.group(1)

                cells.append("\n".join(cell_content_list).strip())
            rows.append(TableRow(cells=cells))
        
        self._table_counter += 1
        placeholder = f"table_{self._table_counter}"
        
        table_data = TableData(rows=rows)
        self.processor.placeholders[placeholder] = PlaceholderData(
            category="table",
            data=table_data.dict()
        )
        
        # If we found a subject in the table, prepend it to the placeholder
        # so the main loop can detect it as a section header.
        if found_subject:
            return f"{found_subject}\n\n{{{{{placeholder}}}}}"
            
        return f"\n{{{{{placeholder}}}}}\n"

    def _get_text_recursive(self, element) -> str:
        """Deep harvesting of all text nodes within an element, including hidden ones."""
        # Using .iter() is more robust against nested schemas like AlternateContent
        return "".join([node.text for node in element.iter() if node.tag.endswith('}t') and node.text])

    def _find_subject_globally(self, re_section: re.Pattern) -> Optional[str]:
        """A truly global top-level sweep across the entire document XML blob."""
        try:
            # We use the raw XML part to ensure we hit AlternateContent, headers, etc.
            root = etree.fromstring(self.doc._part.blob)
            for node in root.iter():
                if node.tag.endswith('}t') and node.text:
                    s_match = re_section.search(node.text.strip())
                    if s_match:
                        section_name = s_match.group(1).upper()
                        if section_name == "BIO": return "BIOLOGY"
                        if section_name in ["MATHS", "MATH"]: return "MATHEMATICS"
                        return section_name
        except:
            pass
        return None
