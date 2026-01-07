"""Quick test for RAG search functionality."""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.manual_rag import ManualRAG

def test_rag_search():
    db_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'data', 'vector_store.db')
    
    print(f"Loading RAG from: {db_path}")
    rag = ManualRAG(db_path)
    
    # Test search
    queries = [
        "災害想定",
        "初動対応",
        "教育及び訓練"
    ]
    
    for query in queries:
        print(f"\n--- Search: '{query}' ---")
        results = rag.search(query, top_k=2)
        
        if results:
            for i, r in enumerate(results, 1):
                print(f"  {i}. {r.chunk_id} (score: {r.score:.2f})")
                print(f"     Preview: {r.text[:100]}...")
        else:
            print("  No results found.")
    
    rag.close()
    print("\n✅ RAG search test completed!")

if __name__ == "__main__":
    test_rag_search()
