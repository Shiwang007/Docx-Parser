import docx
import re


class AnswerKeyParser:
    def __init__(self, docx_path):
        self.doc = docx.Document(docx_path)
        self.answers = {}

    def _store_answer(self, question_number, answer_text):
        """Normalize and store one answer key entry."""
        clean_num = re.sub(r'[^\d]', '', question_number)
        answer_text = answer_text.strip().upper()
        if not clean_num or not answer_text:
            return

        # Split only letter-option answers such as A,C or A/C.
        # Numeric answers such as 42 or 6 must remain a single value.
        if re.fullmatch(r'[A-D](?:\s*[,/]\s*[A-D])*', answer_text):
            correct_options = [
                option.strip().upper()
                for option in re.split(r'[,/]', answer_text)
                if option.strip()
            ]
        else:
            correct_options = [answer_text]

        self.answers[clean_num] = correct_options

    def parse(self):
        """
        Extracts answer keys from both:
        1. Tables where alternating rows contain question numbers and answers.
        2. Paragraph text such as '1. (C) 2. (D) 5. (A,C,D)'.

        Multi-correct letter answers separated by commas or slashes are split
        into separate list items. Numeric answers such as (42) remain intact.
        """
        self.answers = {}

        # Pattern for inline answer keys in paragraphs.
        # Accepts letter choices, comma/slash-separated choices, and numeric answers.
        answer_pattern = re.compile(
            r'(?<!\d)(\d{1,3})\s*[.)]?\s*\(\s*'
            r'([A-D](?:\s*[,/]\s*[A-D])*|\d+)\s*\)',
            re.IGNORECASE,
        )

        for paragraph in self.doc.paragraphs:
            text = paragraph.text
            for match in answer_pattern.finditer(text):
                self._store_answer(match.group(1), match.group(2))

        # Preserve support for answer keys represented as alternating table rows.
        for table in self.doc.tables:
            for i in range(0, len(table.rows) - 1, 2):
                num_row = table.rows[i]
                ans_row = table.rows[i + 1]

                num_cells = [cell.text.strip() for cell in num_row.cells]
                ans_cells = [cell.text.strip() for cell in ans_row.cells]

                for question_number, answer_text in zip(num_cells, ans_cells):
                    if question_number and answer_text:
                        # Table cells may include labels like 'Q1' and '(A,C)'.
                        q_match = re.search(r'\d+', question_number)
                        if not q_match:
                            continue
                        answer_match = re.fullmatch(
                            r'\(?\s*([A-D](?:\s*[,/]\s*[A-D])*|\d+)\s*\)?',
                            answer_text,
                            re.IGNORECASE,
                        )
                        if answer_match:
                            self._store_answer(q_match.group(0), answer_match.group(1))

        return self.answers


if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) > 1:
        parser = AnswerKeyParser(sys.argv[1])
        results = parser.parse()
        print(json.dumps(results, indent=2))
