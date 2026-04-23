import os
import argparse
from pypdf import PdfReader, PdfWriter

def compress_pdf(input_path, quality=60):
    """
    Compresses a PDF by reducing image quality and deduplicating objects.
    Targets file size reduction for large scanned PDFs or image-heavy lectures.
    """
    if not os.path.exists(input_path):
        print(f"Error: File '{input_path}' not found.")
        return

    print(f"[*] Loading: {input_path}")
    reader = PdfReader(input_path)
    total_pages = len(reader.pages)
    
    # Initialize writer from the reader
    writer = PdfWriter(clone_from=input_path)
    
    filename = os.path.splitext(os.path.basename(input_path))[0]
    output_path = os.path.join(os.path.dirname(input_path), f"{filename}_compressed.pdf")

    print(f"[*] Starting compression (Quality: {quality}%, Pages: {total_pages})")
    print("[*] Level 1: Stream compression (lossless)...")
    
    # Apply lossless structural compression first
    for page in writer.pages:
        try:
            page.compress_content_streams()
        except:
            pass
    
    print("[*] Level 2: Re-sampling images (this takes time for large files)...")
    
    image_count = 0
    pages_processed = 0
    
    for i, page in enumerate(writer.pages):
        # We access the images property on the PageObject
        for img in page.images:
            try:
                # Replace the current image with a compressed version
                # pypdf's replace() with quality requires Pillow internally
                img.replace(img.image, quality=quality)
                image_count += 1
            except Exception as e:
                # Skip if an image format is unsupported or already highly compressed
                pass
        
        pages_processed += 1
        if pages_processed % 5 == 0 or pages_processed == total_pages:
            print(f"    [+] Processed {pages_processed}/{total_pages} pages ({image_count} images optimized)...")

    print(f"[*] Writing compressed file: {output_path}")
    with open(output_path, "wb") as f:
        writer.write(f)

    # Calculate reduction
    orig_size = os.path.getsize(input_path) / (1024 * 1024)
    new_size = os.path.getsize(output_path) / (1024 * 1024)
    reduction = ((orig_size - new_size) / orig_size) * 100

    print(f"\n[DONE] Compression Complete!")
    print(f"    Size: {orig_size:.2f} MB -> {new_size:.2f} MB")
    print(f"    Reduction: {reduction:.1f}%")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Large PDF Compressor (Structural & Image-level)")
    parser.add_argument("input", help="Path to the input PDF file")
    parser.add_argument("--quality", type=int, default=60, help="JPEG quality level (1-100), default 60")

    args = parser.parse_args()
    
    try:
        compress_pdf(args.input, args.quality)
    except Exception as e:
        print(f"An error occurred during compression: {e}")
