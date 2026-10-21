import os
import sys
import json
import time
from typing import List, Dict

# Add project root to path to import src modules
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.parser_engine import DocxParser

def batch_process():
    input_dir = "data"
    output_dir = "output"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Scant for docx files
    docx_files = [f for f in os.listdir(input_dir) if f.endswith('.docx')]
    
    manifest: List[Dict[str, str]] = []
    
    print(f"[*] Found {len(docx_files)} documents to process.")
    
    for filename in docx_files:
        input_path = os.path.join(input_dir, filename)
        output_filename = filename.replace('.docx', '.json').replace(' ', '_')
        output_path = os.path.join(output_dir, output_filename)
        
        print(f"[*] Processing: {filename}...")
        start_time = time.time()
        
        try:
            parser = DocxParser(input_path)
            ir_data = parser.parse()
            
            # Convert to dict
            try:
                output_data = ir_data.model_dump()
            except AttributeError:
                output_data = ir_data.dict()
            
            # Write JSON
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            # Determine a nice title for the manifest
            # Use metadata header if available, otherwise filename
            title = None
            if output_data.get('metadata', {}).get('header_info'):
                header_list = output_data['metadata']['header_info']
                if header_list and len(header_list) > 0:
                    title = header_list[0].split('\n')[0].strip()
            
            if not title:
                title = filename.replace('.docx', '').replace('_', ' ')
            
            manifest.append({
                "title": title,
                "filename": output_filename
            })
            
            print(f"[+] Done in {time.time() - start_time:.2f}s -> {output_filename}")
            
        except Exception as e:
            print(f"[!] Error processing {filename}: {e}")

    # Generate Manifest
    manifest_path = os.path.join(output_dir, "manifest.json")
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        
    print(f"\n[!] Batch processing complete. Manifest saved to {manifest_path}")

if __name__ == "__main__":
    batch_process()
