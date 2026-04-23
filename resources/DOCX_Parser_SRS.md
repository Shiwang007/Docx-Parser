# 📄 Software Requirements Specification (SRS)

## 📌 Project Title
**DOCX Structured Content Parser & Converter System**

---

# 1. 🧠 Introduction

## 1.1 Purpose
This document defines the requirements for a system that:

- Reads Microsoft Word (`.docx`) files
- Extracts structured content:
  - Text
  - Tables
  - Images
  - Formulas
- Converts content into a **custom structured JSON format**
- Uses **placeholders** to represent non-text elements inside text

---

## 1.2 Scope

The system will:

- Parse `.docx` files using Python
- Preserve **document flow (order of elements)**
- Replace non-text elements with placeholders
- Store actual content separately
- Support future extensibility (e.g., formula rendering, editing UI)

---

## 1.3 Definitions

| Term | Meaning |
|------|--------|
| DOCX | Microsoft Word document format |
| OMML | Office Math Markup Language |
| IR | Intermediate Representation (custom JSON format) |
| Placeholder | Token representing non-text content (e.g., `{{img_1}}`) |

---

# 2. 🏗️ System Overview

## 2.1 High-Level Architecture

```
DOCX File
   ↓
Parser Engine (Python)
   ↓
Structured JSON (IR)
   ↓
Database Storage
   ↓
Frontend Renderer (React)
```

---

## 2.2 System Components

### 1. DOCX Parser
- Reads `.docx` file
- Extracts XML + media

### 2. Content Processor
- Identifies elements:
  - Paragraphs
  - Tables
  - Images
  - Formulas

### 3. Placeholder Engine
- Inserts placeholders into text
- Maintains mapping

### 4. Formula Parser (Future)
- Converts OMML → LaTeX / Image

### 5. Output Generator
- Produces final JSON (IR)

---

# 3. ⚙️ Functional Requirements

## 3.1 File Input

### FR-1
- System shall accept `.docx` files as input

### FR-2
- System shall validate file format before processing

---

## 3.2 Document Parsing

### FR-3
- System shall extract document structure in correct order

### FR-4
- System shall process:
  - Paragraphs (`<w:p>`)
  - Tables (`<w:tbl>`)
  - Runs (`<w:r>`)

---

## 3.3 Text Extraction

### FR-5
- System shall extract plain text from paragraphs

### FR-6
- System shall preserve inline structure (runs)

---

## 3.4 Placeholder System

### FR-7
- System shall replace non-text elements with placeholders

#### Placeholder Format:
```
{{type_index}}
```

Examples:
- `{{img_1}}`
- `{{table_1}}`
- `{{formula_1}}`

---

### FR-8
- System shall maintain a mapping:

```json
{
  "placeholder_id": {
    "type": "...",
    "data": ...
  }
}
```

---

## 3.5 Image Extraction

### FR-9
- System shall extract images from `/word/media/`

### FR-10
- System shall store images with unique identifiers

### FR-11
- System shall insert image placeholders in text at correct positions

---

## 3.6 Table Extraction

### FR-12
- System shall extract tables as 2D arrays

```json
[
  ["A1", "B1"],
  ["A2", "B2"]
]
```

### FR-13
- System shall insert table placeholders in correct document order

---

## 3.7 Formula Detection (Phase 2)

### FR-14
- System shall detect formulas:
  - `<m:oMath>`
  - `<m:oMathPara>`

### FR-15
- System shall insert formula placeholders

---

## 3.8 Formula Conversion (Phase 3)

### FR-16
- System shall convert OMML → LaTeX using rule-based parser

### FR-17
- System shall optionally convert formulas to images

---

## 3.9 Output Format

### FR-18
- System shall generate JSON output:

```json
{
  "question": "...",
  "placeholders": {}
}
```

---

# 4. 🧱 Non-Functional Requirements

## 4.1 Performance
- Should process a document (<5MB) in <2 seconds
- Should handle 100+ elements efficiently

---

## 4.2 Scalability
- System should support batch processing
- Should handle concurrent requests (if API-based)

---

## 4.3 Maintainability
- Modular code structure
- Separate parsing and rendering logic

---

## 4.4 Extensibility
- Easy to add new element types:
  - Charts
  - SmartArt
  - Equations

---

## 4.5 Reliability
- Should not crash on malformed documents
- Should log parsing errors

---

# 5. 🧩 Data Design

## 5.1 Intermediate Representation (IR)

```json
{
  "question": "Solve {{formula_1}} using {{table_1}}",
  "placeholders": {
    "formula_1": {
      "type": "formula",
      "latex": "x^2 + y^2"
    },
    "table_1": {
      "type": "table",
      "data": [...]
    }
  }
}
```

---

## 5.2 Database Schema (MongoDB)

### Collection: `documents`

```json
{
  "_id": "...",
  "question": "...",
  "placeholders": {},
  "createdAt": "...",
  "updatedAt": "..."
}
```

---

# 6. 🧪 Edge Cases

- Multiple images in same paragraph
- Nested tables
- Empty paragraphs
- Mixed content (text + image + formula)
- Malformed XML

---

# 7. 🔐 Security Considerations

- Validate file type (avoid malicious uploads)
- Limit file size
- Sanitize extracted content

---

# 8. 🚀 Future Enhancements

## Phase 2
- Formula detection

## Phase 3
- Formula → LaTeX parser

## Phase 4
- React-based editor

## Phase 5
- AI-assisted content structuring

---

# 9. 🛠️ Technology Stack

## Backend
- Python
  - python-docx
  - lxml
  - zipfile

## Database
- MongoDB

## Frontend
- React
- MathJax / KaTeX (future)

---

# 10. 📊 Success Criteria

- Correct placeholder placement
- Accurate table/image extraction
- Structured JSON output
- Easy rendering in frontend

---

# 🏁 Final Thoughts

This system is essentially:

> A **document-to-structured-data compiler**

You are:
- Parsing a complex format (DOCX)
- Converting it into a controlled representation (IR)
- Preparing it for rendering/storage
