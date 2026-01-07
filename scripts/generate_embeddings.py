"""
Embedding Generation Script for RAG
Generates embeddings for manual chunks using Gemini text-embedding-004.
Updates the existing vector_store.db with embeddings.

Usage:
    python scripts/generate_embeddings.py
"""
import os
import sys
import sqlite3
import json
import struct
import google.generativeai as genai

# Setup
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

# Load API key from secrets.toml
def load_api_key():
    try:
        import tomllib
        secrets_path = os.path.join(PROJECT_ROOT, ".streamlit", "secrets.toml")
        with open(secrets_path, "rb") as f:
            secrets = tomllib.load(f)
        return secrets.get("GEMINI_API_KEY") or secrets.get("GOOGLE_API_KEY")
    except:
        pass
    return os.environ.get("GOOGLE_API_KEY")

api_key = load_api_key()
if api_key:
    genai.configure(api_key=api_key)
else:
    print("ERROR: No API key found")
    sys.exit(1)


def get_embedding(text: str, task_type: str = "retrieval_document") -> list[float]:
    """
    Generate embedding using Gemini text-embedding-004.
    
    Args:
        text: Text to embed
        task_type: "retrieval_document" for storing, "retrieval_query" for searching
        
    Returns:
        List of floats (768 dimensions)
    """
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=text,
        task_type=task_type
    )
    return result['embedding']


def embedding_to_blob(embedding: list[float]) -> bytes:
    """Convert embedding list to binary blob for SQLite."""
    return struct.pack(f'{len(embedding)}f', *embedding)


def blob_to_embedding(blob: bytes) -> list[float]:
    """Convert binary blob back to embedding list."""
    return list(struct.unpack(f'{len(blob)//4}f', blob))


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Calculate cosine similarity between two embeddings."""
    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    return dot_product / (norm_a * norm_b)


def main():
    db_path = os.path.join(PROJECT_ROOT, "src", "data", "vector_store.db")
    
    if not os.path.exists(db_path):
        print(f"ERROR: Database not found: {db_path}")
        print("Run build_vector_db.py first to create the database.")
        sys.exit(1)
    
    print("="*70)
    print("Embedding Generation for Manual RAG")
    print("="*70)
    print(f"Database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all chunks without embeddings
    cursor.execute("SELECT chunk_id, text FROM chunks WHERE embedding IS NULL")
    chunks = cursor.fetchall()
    
    if not chunks:
        print("\nNo chunks without embeddings found.")
        
        # Check if we have any chunks at all
        cursor.execute("SELECT COUNT(*) FROM chunks")
        total = cursor.fetchone()[0]
        print(f"Total chunks in database: {total}")
        
        if total == 0:
            print("Database is empty. Run build_vector_db.py first.")
        else:
            print("All chunks already have embeddings!")
        
        conn.close()
        return
    
    print(f"\nGenerating embeddings for {len(chunks)} chunks...")
    
    for i, (chunk_id, text) in enumerate(chunks, 1):
        try:
            print(f"  [{i}/{len(chunks)}] {chunk_id[:30]}...")
            
            # Generate embedding
            embedding = get_embedding(text)
            blob = embedding_to_blob(embedding)
            
            # Update database
            cursor.execute(
                "UPDATE chunks SET embedding = ? WHERE chunk_id = ?",
                (blob, chunk_id)
            )
            
        except Exception as e:
            print(f"    ERROR: {e}")
            continue
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Embeddings generated for {len(chunks)} chunks")
    print(f"Database updated: {db_path}")


def search(query: str, top_k: int = 3) -> list[dict]:
    """
    Search for similar chunks using embedding similarity.
    
    Args:
        query: Search query
        top_k: Number of results to return
        
    Returns:
        List of matching chunks with similarity scores
    """
    db_path = os.path.join(PROJECT_ROOT, "src", "data", "vector_store.db")
    
    # Generate query embedding
    query_embedding = get_embedding(query, task_type="retrieval_query")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all chunks with embeddings
    cursor.execute("SELECT chunk_id, text, metadata, embedding FROM chunks WHERE embedding IS NOT NULL")
    rows = cursor.fetchall()
    
    conn.close()
    
    # Calculate similarities
    results = []
    for chunk_id, text, metadata, embedding_blob in rows:
        if embedding_blob:
            chunk_embedding = blob_to_embedding(embedding_blob)
            similarity = cosine_similarity(query_embedding, chunk_embedding)
            results.append({
                "chunk_id": chunk_id,
                "text": text[:200] + "..." if len(text) > 200 else text,
                "metadata": json.loads(metadata) if metadata else {},
                "similarity": similarity
            })
    
    # Sort by similarity
    results.sort(key=lambda x: x["similarity"], reverse=True)
    
    return results[:top_k]


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--search":
        # Search mode
        query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "災害想定"
        print(f"Searching for: {query}\n")
        
        results = search(query)
        for i, r in enumerate(results, 1):
            print(f"{i}. [{r['similarity']:.3f}] {r['chunk_id']}")
            print(f"   {r['text'][:100]}...\n")
    else:
        # Generate embeddings
        main()
