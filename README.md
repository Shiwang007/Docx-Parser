# Docx-Parser

A comprehensive utility for parsing exam documents, calculating scores (NEET/JEE), and generating professional digital scorecards.

## Features
- **Docx Parsing**: Extracts question data and metadata from standard assessment documents.
- **Score Calculation**: Automated scoring logic for competitive exams (e.g., NEET +4/-1 rule).
- **Report Generation**: Generates stylized, data-rich HTML scorecards for students.
- **Answer Key Management**: Handles master answer keys and student attempt mapping.

## Structure
- `src/`: Core parsing and scoring logic.
- `web/`: Frontend components for the scorecard viewer.
- `scripts/`: Maintenance and patch utilities.
- `score_calculator.py`: The main scoring engine.

## Usage
1. Prepare your answer key and student attempt data.
2. Run the scorecard generator:
   ```bash
   python score_calculator.py
   ```

## Requirements
- Python 3.7+
- BeautifulSoup4
- Jinja2
- (See requirements.txt for full list)

---
Built by Shiwang007.
