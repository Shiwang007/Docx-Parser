import sys
import json
import argparse
from parser_engine import DocxParser

def main():
    parser = argparse.ArgumentParser(description="DOCX Structured Content Parser")
    parser.add_argument("input", help="Path to the input .docx file")
    parser.add_argument("--output", help="Path to save the JSON output", default="output/output.json")
    
    args = parser.parse_args()
    
    try:
        print(f"[*] Parsing document: {args.input}...")
        docx_parser = DocxParser(args.input)
        ir_data = docx_parser.parse()
        
        # Convert Pydantic model to dict for JSON serialization
        try:
            output_data = ir_data.model_dump()
        except AttributeError:
            output_data = ir_data.dict()
        
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
            
        print(f"[+] Successfully parsed and saved to {args.output}")
        
    except Exception as e:
        print(f"[!] Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
