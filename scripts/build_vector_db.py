"""
Vector Database Build Script
Creates SQLite vector store from Markdown chunks.
This is a one-time build script, NOT used at runtime.

Usage:
    python scripts/build_vector_db.py --input <chunks_dir> --output <db_path>
"""
import argparse
import json
import os
import re
import sqlite3
from typing import List, Dict, Optional


def parse_markdown_chunk(filepath: str) -> Optional[Dict]:
    """
    Parse a Markdown chunk file with YAML frontmatter.
    
    Returns:
        Dictionary with chunk_id, text, and metadata
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Parse YAML frontmatter
    frontmatter_match = re.match(r'^---\n(.*?)\n---\n\n?(.*)', content, re.DOTALL)
    
    if not frontmatter_match:
        return None
    
    frontmatter_text = frontmatter_match.group(1)
    body_text = frontmatter_match.group(2).strip()
    
    # Simple YAML parsing
    metadata = {}
    for line in frontmatter_text.split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip()
    
    return {
        "chunk_id": metadata.get("chunk_id", os.path.splitext(os.path.basename(filepath))[0]),
        "text": body_text,
        "metadata": metadata
    }


def create_database(db_path: str):
    """Create SQLite database with chunks table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            chunk_id TEXT PRIMARY KEY,
            text TEXT NOT NULL,
            metadata TEXT,
            embedding BLOB
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_chunk_id ON chunks(chunk_id)
    """)
    
    conn.commit()
    return conn


def insert_chunks(conn: sqlite3.Connection, chunks: List[Dict]):
    """Insert chunks into database."""
    cursor = conn.cursor()
    
    for chunk in chunks:
        cursor.execute("""
            INSERT OR REPLACE INTO chunks (chunk_id, text, metadata, embedding)
            VALUES (?, ?, ?, NULL)
        """, (
            chunk["chunk_id"],
            chunk["text"],
            json.dumps(chunk["metadata"], ensure_ascii=False)
        ))
    
    conn.commit()


def main():
    parser = argparse.ArgumentParser(description="Build vector database from Markdown chunks")
    parser.add_argument("--input", "-i", required=True, help="Input directory containing .md chunks")
    parser.add_argument("--output", "-o", required=True, help="Output SQLite database path")
    
    args = parser.parse_args()
    
    print(f"Building vector database:")
    print(f"  Input:  {args.input}")
    print(f"  Output: {args.output}")
    
    # Find all Markdown files
    md_files = [
        os.path.join(args.input, f)
        for f in os.listdir(args.input)
        if f.endswith(".md")
    ]
    
    if not md_files:
        print("No .md files found in input directory!")
        return
    
    print(f"Found {len(md_files)} Markdown files")
    
    # Parse chunks
    chunks = []
    for filepath in md_files:
        chunk = parse_markdown_chunk(filepath)
        if chunk:
            chunks.append(chunk)
            print(f"  Parsed: {chunk['chunk_id']} ({len(chunk['text'])} chars)")
        else:
            print(f"  Skipped: {os.path.basename(filepath)} (invalid format)")
    
    if not chunks:
        print("No valid chunks to insert!")
        return
    
    # Create database
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    conn = create_database(args.output)
    
    # Insert chunks
    insert_chunks(conn, chunks)
    
    conn.close()
    
    print(f"\nDatabase created: {args.output}")
    print(f"Total chunks: {len(chunks)}")
    print("\nNote: Embeddings are not yet generated. Run with --embed flag to generate.")


if __name__ == "__main__":
    main()
