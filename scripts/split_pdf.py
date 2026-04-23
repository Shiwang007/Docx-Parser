import os
import argparse
import math
from pypdf import PdfReader, PdfWriter

def split_pdf(input_path, mode, value):
    """
    Splits a PDF based on the specified mode and value.
    Memory-efficient by only holding necessary pages/writers in scope.
    """
    if not os.path.exists(input_path):
        print(f"Error: File '{input_path}' not found.")
        return

    reader = PdfReader(input_path)
    total_pages = len(reader.pages)
    filename = os.path.splitext(os.path.basename(input_path))[0]
    output_dir = os.path.join(os.path.dirname(input_path), f"{filename}_split")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"[*] Created output directory: {output_dir}")

    print(f"[*] Processing: {input_path} ({total_pages} pages)")
    print(f"[*] Mode: {mode}, Value: {value}")

    if mode == 'page':
        # Every page becomes a separate file
        for i in range(total_pages):
            writer = PdfWriter()
            writer.add_page(reader.pages[i])
            output_name = os.path.join(output_dir, f"{filename}_pg_{i+1:03d}.pdf")
            with open(output_name, "wb") as f:
                writer.write(f)
            if (i + 1) % 10 == 0 or i == total_pages - 1:
                print(f"    [+] Created {i+1}/{total_pages} pages...")

    elif mode == 'chunk':
        # Every 'value' pages become a separate file
        chunk_size = int(value)
        num_chunks = math.ceil(total_pages / chunk_size)
        
        for i in range(num_chunks):
            writer = PdfWriter()
            start = i * chunk_size
            end = min(start + chunk_size, total_pages)
            
            for pg_num in range(start, end):
                writer.add_page(reader.pages[pg_num])
            
            output_name = os.path.join(output_dir, f"{filename}_chunk_{i+1:02d}.pdf")
            with open(output_name, "wb") as f:
                writer.write(f)
            print(f"    [+] Created chunk {i+1}/{num_chunks} (Pages {start+1}-{end})")

    elif mode == 'part':
        # Split into 'value' equal parts
        num_parts = int(value)
        pages_per_part = math.ceil(total_pages / num_parts)
        
        for i in range(num_parts):
            start = i * pages_per_part
            if start >= total_pages: break
            
            end = min(start + pages_per_part, total_pages)
            writer = PdfWriter()
            
            for pg_num in range(start, end):
                writer.add_page(reader.pages[pg_num])
            
            output_name = os.path.join(output_dir, f"{filename}_part_{i+1:02d}.pdf")
            with open(output_name, "wb") as f:
                writer.write(f)
            print(f"    [+] Created part {i+1}/{num_parts} (Pages {start+1}-{end})")

    print(f"\n[DONE] Successfully split PDF into {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Memory-efficient PDF Splitter")
    parser.add_argument("input", help="Path to the input PDF file")
    parser.add_argument("--mode", choices=['page', 'chunk', 'part'], default='chunk', 
                        help="Split mode: 'page' (each pg), 'chunk' (N pgs per file), 'part' (N total files)")
    parser.add_argument("--value", type=int, default=50, 
                        help="Value associated with the mode (chunk size or number of parts)")

    args = parser.parse_args()
    
    try:
        split_pdf(args.input, args.mode, args.value)
    except Exception as e:
        print(f"An error occurred: {e}")
