"""
PDF to Markdown Extraction Script
Extracts text from government manual PDFs and saves as Markdown chunks.
This is a one-time build script, NOT used at runtime.

Usage:
    python scripts/extract_manual_pdf.py --input <pdf_path> --output <output_dir>
"""
import argparse
import os
import re
import json
from typing import List, Dict


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF using pymupdf."""
    try:
        import fitz  # pymupdf
    except ImportError:
        raise ImportError("pymupdf is required. Install with: pip install pymupdf")
    
    doc = fitz.open(pdf_path)
    text_parts = []
    
    for page_num, page in enumerate(doc, 1):
        text = page.get_text()
        if text.strip():
            text_parts.append(f"<!-- Page {page_num} -->\n{text}")
    
    doc.close()
    return "\n\n".join(text_parts)


def split_into_chunks(text: str, chunk_size: int = 500) -> List[Dict]:
    """
    Split text into chunks with metadata.
    
    Args:
        text: Full text
        chunk_size: Target chunk size in characters
        
    Returns:
        List of chunk dictionaries
    """
    # Split by double newlines (paragraphs)
    paragraphs = re.split(r'\n\n+', text)
    
    chunks = []
    current_chunk = []
    current_size = 0
    current_page = 1
    
    for para in paragraphs:
        # Extract page number if present
        page_match = re.search(r'<!-- Page (\d+) -->', para)
        if page_match:
            current_page = int(page_match.group(1))
            para = re.sub(r'<!-- Page \d+ -->\n?', '', para)
        
        para = para.strip()
        if not para:
            continue
        
        para_size = len(para)
        
        if current_size + para_size > chunk_size and current_chunk:
            # Save current chunk
            chunks.append({
                "text": "\n\n".join(current_chunk),
                "start_page": current_page,
                "char_count": current_size
            })
            current_chunk = [para]
            current_size = para_size
        else:
            current_chunk.append(para)
            current_size += para_size
    
    # Save final chunk
    if current_chunk:
        chunks.append({
            "text": "\n\n".join(current_chunk),
            "start_page": current_page,
            "char_count": current_size
        })
    
    return chunks


def save_chunks_as_markdown(chunks: List[Dict], output_dir: str, source_name: str):
    """
    Save chunks as individual Markdown files.
    
    Args:
        chunks: List of chunk dictionaries
        output_dir: Output directory path
        source_name: Source file name (without extension)
    """
    os.makedirs(output_dir, exist_ok=True)
    
    manifest = []
    
    for i, chunk in enumerate(chunks, 1):
        chunk_id = f"{source_name}_ch{i:03d}"
        filename = f"{chunk_id}.md"
        filepath = os.path.join(output_dir, filename)
        
        # Write Markdown with frontmatter
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"---\n")
            f.write(f"chunk_id: {chunk_id}\n")
            f.write(f"source: {source_name}\n")
            f.write(f"start_page: {chunk['start_page']}\n")
            f.write(f"char_count: {chunk['char_count']}\n")
            f.write(f"---\n\n")
            f.write(chunk["text"])
        
        manifest.append({
            "chunk_id": chunk_id,
            "filename": filename,
            "start_page": chunk["start_page"],
            "char_count": chunk["char_count"]
        })
        
        print(f"  Created: {filename} ({chunk['char_count']} chars)")
    
    # Save manifest
    manifest_path = os.path.join(output_dir, f"{source_name}_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    
    print(f"\nManifest saved: {manifest_path}")
    print(f"Total chunks: {len(chunks)}")


def main():
    parser = argparse.ArgumentParser(description="Extract PDF to Markdown chunks")
    parser.add_argument("--input", "-i", required=True, help="Input PDF file path")
    parser.add_argument("--output", "-o", required=True, help="Output directory path")
    parser.add_argument("--chunk-size", "-s", type=int, default=500, help="Target chunk size")
    
    args = parser.parse_args()
    
    print(f"Extracting: {args.input}")
    
    # Get source name
    source_name = os.path.splitext(os.path.basename(args.input))[0]
    
    # Extract text
    text = extract_text_from_pdf(args.input)
    print(f"Extracted {len(text)} characters")
    
    # Split into chunks
    chunks = split_into_chunks(text, args.chunk_size)
    print(f"Split into {len(chunks)} chunks")
    
    # Save as Markdown
    save_chunks_as_markdown(chunks, args.output, source_name)
    
    print("\nDone! Please review the chunks manually for quality.")


if __name__ == "__main__":
    main()
