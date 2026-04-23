import docx
import re

class AnswerKeyParser:
    def __init__(self, docx_path):
        self.doc = docx.Document(docx_path)
        self.answers = {}

    def parse(self):
        """
        Parses tables where even rows are question numbers and odd rows are answers.
        """
        for table in self.doc.tables:
            for i in range(0, len(table.rows) - 1, 2):
                num_row = table.rows[i]
                ans_row = table.rows[i+1]
                
                num_cells = [c.text.strip() for c in num_row.cells]
                ans_cells = [c.text.strip() for c in ans_row.cells]
                
                for q_num, q_ans in zip(num_cells, ans_cells):
                    if q_num and q_ans:
                        # Normalize question number (it might be '1' or 'Q1')
                        clean_num = re.sub(r'[^\d]', '', q_num)
                        if clean_num:
                            # We store as a list to match the Mongoose schema correctAnswer: [String]
                            self.answers[clean_num] = [q_ans.upper()]
                            
        return self.answers

if __name__ == "__main__":
    import sys
    import json
    if len(sys.argv) > 1:
        parser = AnswerKeyParser(sys.argv[1])
        results = parser.parse()
        print(json.dumps(results, indent=2))
