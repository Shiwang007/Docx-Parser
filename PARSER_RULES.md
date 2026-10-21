# 📝 Medjeex Exam Studio - DOCX Formatting Rules

This document outlines the layout and formatting requirements for `.docx` files to ensure they are parsed accurately by the **Medjeex Exam Studio** parsing engine. Following these guidelines will guarantee flawless conversion of sections, questions, options, formulas, and diagrams into structured digital formats.

---

## 1. 📂 Document Structure

A standard test booklet should flow in this chronological order:
1. **Header Info**: Title, instructions, and general metadata.
2. **Subject Sections**: Standalone headers for subjects.
3. **Subsections**: Optional Section-A or Section-B.
4. **Questions**: Numbered list of questions.

---

## 2. 🏷️ Subject & Section Headers

Subject sections group your questions. The parser detects sections by matching specific keywords in paragraphs.

* **Formatting Rules**:
  * Write the subject name as a standalone paragraph (e.g. `PHYSICS`, `CHEMISTRY`, `BIOLOGY`, `MATHEMATICS`, `BOTANY`, `ZOOLOGY`).
  * Case-insensitive, but keep it clean (e.g., `PHYSICS` or `Physics`).
* **Subsections**:
  * Declare sub-sections using `SECTION-A` or `SECTION-B` as a standalone paragraph directly beneath the subject header.

### 👍 Dos & 👎 Don'ts:
| 👍 Do | 👎 Don't |
| :--- | :--- |
| **Do** place the subject name in its own standalone line/paragraph.<br>*(e.g., `CHEMISTRY`)* | **Don't** combine it with other text on the same line.<br>*(e.g., `CHEMISTRY - SECTION 1`)* |
| **Do** use standard subjects that the parser recognizes.<br>*(e.g., `Physics`, `Chemistry`, `Biology`, `Mathematics`)* | **Don't** create obscure subject names that could be missed.<br>*(e.g., `Phy. Part A`)* |

---

## 3. ❓ Question Formatting

Questions are identified by sequential numerical markers at the start of a paragraph.

* **Rules for Question Text**:
  * Always start the question paragraph with the question number followed by a **dot (`.`)** and a **space** (e.g. `1. `, `52. `).
  * Do **not** use double dots (e.g. `1.. `) or other punctuation like parentheses (e.g. `1) `) for the primary question number.
  * The question text can span multiple paragraphs. Any text under a question that is *not* an option or another question will be appended to the question body.

### 👍 Dos & 👎 Don'ts:
| 👍 Do | 👎 Don't |
| :--- | :--- |
| **Do** start with a number, dot, and space.<br>*(e.g., `12. Find the value of...`)* | **Don't** use brackets, parentheses, or prefixes.<br>*(e.g., `Q12.`, `12)`, `[12].`)* |
| **Do** start a new paragraph for each new question. | **Don't** combine multiple questions inside the same paragraph. |
| **Do** put multi-paragraph questions on subsequent lines. They will automatically merge into the question body. | **Don't** insert unrelated headers or lines inside a question's body. |

---

## 4. 🎛️ Options Formatting (MCQs) & Assertion-Reason

Multiple-choice options are parsed by matching option markers.

* **Rules for Options**:
  * Use standard alphabet uppercase markers wrapped in parentheses: `(A)`, `(B)`, `(C)`, `(D)`.
  * **Option A Check**: To avoid matching inline text like `"Assertion (A)"` or `"Reason (A)"`, option `(A)` is only matched if it is structurally separated (starts the line, follows a tab, or follows a space after other content).
  * You can place options on the **same line** separated by tabs/spaces, or on **new lines**.
  * Multi-line option contents are automatically appended to the option they belong to.

* **Examples**:
  * *Single-line options*:
    ```text
    (A) 10 m/s    (B) 20 m/s    (C) 30 m/s    (D) 40 m/s
    ```
  * *Multi-line/Stacked options*:
    ```text
    (A) 10 m/s
    (B) 20 m/s
    (C) 30 m/s
    (D) 40 m/s
    ```

* **Assertion-Reason Formatting**:
  * Write the Assertion and Reason text clearly using `Assertion (A):` and `Reason (R):` (or `Reason (A):`).
  * The parser will automatically ignore the `(A)` in `"Assertion (A)"` so it does not get treated as the MCQ option A.
  * The actual MCQ options `(A)`, `(B)`, `(C)`, `(D)` should follow on their own lines (or tab-separated) as usual.

### 👍 Dos & 👎 Don't for MCQs:
| 👍 Do | 👎 Don't |
| :--- | :--- |
| **Do** use uppercase letters inside parentheses.<br>*(e.g., `(A)`, `(B)`, `(C)`, `(D)`)* | **Don't** use lowercase or standard dots.<br>*(e.g., `(a)`, `A.`, `B.`, `[A]`)* |
| **Do** prefix Assertion-Reason lines explicitly with the keyword **"Assertion"** or **"Reason"**.<br>*(e.g., `Assertion (A):`)* | **Don't** write `(A)` raw in the middle of a sentence without the keyword prefix, or it will be parsed as Option A.<br>*(e.g., `Statement: (A) is correct.` ❌)* |
| **Do** space out options clearly on the same line using tabs or multiple spaces. | **Don't** write options right next to each other.<br>*(e.g., `(A)10(B)20` ❌)* |

---

## 5. 🔢 Integer & Numerical Questions

If a question does **not** have options (no matching `(A)`, `(B)`, etc. markers in its body), the parser automatically classifies it as an **Integer Type** (`questionType: "integer"`).

* **Example**:
  ```text
  22. Find the value of dy/dx, if y = (x - 1)(2x + 5) at x = 1.
  ```
  *(Since this question has no option markers, it will render as a text input query for numerical answers).*

---

## 6. 📐 Math & Formula Rendering

Formulas must be written using **Word's native Equation Editor** (OMML).

* **Best Practices**:
  * Use **Insert ➔ Equation** (or `Alt + =`) to write all formulas.
  * Native symbols like integrals (`∫`), summations (`∑`), fractions, superscripts/subscripts, matrices, limits, and Greek symbols ($\alpha$, $\beta$, $\theta$, etc.) are fully supported and converted to high-quality LaTeX/KaTeX.
  * If you type symbols via the standard keyboard inside a text block (like `x ∈ A ∩ B`), use standard Unicode characters. The parser will automatically map them to standard LaTeX tags so they render cleanly without showing up as blank boxes.

### 👍 Dos & 👎 Don'ts:
| 👍 Do | 👎 Don't |
| :--- | :--- |
| **Do** use the Word Equation Editor (`Alt + =`) for equations, variables, and math operators. | **Don't** use pictures/screenshots of formulas, as they cannot be parsed as text. |
| **Do** use standard Unicode math symbols for simple inline text relationships.<br>*(e.g., `∈`, `∉`, `∩`, `∪`, `⊆`, `∞`, `×`, `÷`, `±`, `°`, `Å`)* | **Don't** use custom third-party font files or obscure symbol encodings not standard to MS Word. |
| **Do** write integrals using Word's built-in integral template. The parser will automatically format it as `\int`. | **Don't** draw integral lines manually using Word shapes. |

---

## 7. 📊 Tables

Tables are extracted as structured 2D grids and rendered dynamically.

* **Rules for Tables**:
  * Use Word's **Insert ➔ Table** feature.
  * Avoid nested tables or merged cells where possible to preserve clean alignments.
  * Formulas and formatted text inside table cells are fully processed and preserved.

---

## 8. 🎨 Images & Diagrams

The system extracts images and attaches them to questions as inline or standalone diagrams.

* **Supported Formats**:
  * **Standard Images**: PNG, JPEG, and WebP are fully optimized and converted to base64 automatically.
* **Unsupported Formats**:
  * Avoid vector formats like **EMF** or **WMF**. Convert them to PNG/JPEG before inserting them into Word, otherwise they will be flagged as unsupported since standard web browsers cannot render EMF/WMF vectors directly.
* **Layout Positioning**:
  * Images placed inside a question paragraph will be displayed **inline** (next to the text).
  * Large figures or diagrams placed on their own standalone paragraph will be promoted to **standalone** (centered above or below the question).

### 👍 Dos & 👎 Don'ts:
| 👍 Do | 👎 Don't |
| :--- | :--- |
| **Do** export vector drawings (from programs like CorelDraw or ChemDraw) to **PNG/JPEG** before inserting them into Word. | **Don't** insert diagrams directly as vector objects or copy-paste them as **EMF/WMF** files. |
| **Do** put standalone diagrams in a paragraph by themselves to keep them centered and correctly sized. | **Don't** place text on the same line as a large diagram if you want it centered. |

---

## 9. 🔑 Answer Keys (Optional)

You can upload a separate **Answer Key** document along with the test booklet.

* **Formatting Rules**:
  * Write the key as a simple table or list where each line contains the **question number** and the **correct option(s)**.
  * Multi-correct answers can be separated by commas (e.g. `1. A, B` or `5. B, C, D`).
  * The parser will automatically match the question numbers and merge keys into the main JSON structure.
