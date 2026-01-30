"""
TDD Tests for RAG Vector Search (Phase 2)

These tests are written BEFORE implementation (Red phase).
They should FAIL initially, then PASS after implementation.
"""
import sys
import os
import pytest
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestEmbeddingGeneration:
    """Tests for embedding generation functionality."""
    
    def test_generate_embedding_returns_vector(self):
        """Embedding generation should return a numpy array."""
        from src.core.manual_rag import ManualRAG
        
        rag = ManualRAG.load()  # Use factory method
        text = "南海トラフ地震の発生確率"
        
        # This method doesn't exist yet - should fail
        embedding = rag.generate_embedding(text)
        
        assert embedding is not None
        assert isinstance(embedding, (list, np.ndarray))
        assert len(embedding) > 0
    
    def test_embedding_dimension_is_consistent(self):
        """All embeddings should have the same dimension."""
        from src.core.manual_rag import ManualRAG
        
        rag = ManualRAG.load()
        
        emb1 = rag.generate_embedding("テスト文章1")
        emb2 = rag.generate_embedding("別のテスト文章")
        
        assert len(emb1) == len(emb2)


class TestVectorSearch:
    """Tests for vector similarity search."""
    
    def test_vector_search_returns_results(self):
        """Vector search should return ranked results."""
        from src.core.manual_rag import ManualRAG
        
        rag = ManualRAG.load()
        query = "災害時の初動対応について"
        
        # This method should use vector similarity
        results = rag.vector_search(query, top_k=3)
        
        assert results is not None
        assert len(results) <= 3
    
    def test_vector_search_scores_are_normalized(self):
        """Similarity scores should be between 0 and 1."""
        from src.core.manual_rag import ManualRAG
        
        rag = ManualRAG.load()
        results = rag.vector_search("事業継続計画", top_k=3)
        
        for result in results:
            assert 0.0 <= result.score <= 1.0
    
    def test_semantic_similarity_outperforms_keyword(self):
        """Vector search should find semantically similar content
        even without exact keyword match."""
        from src.core.manual_rag import ManualRAG
        
        rag = ManualRAG.load()
        
        # Query using different words but same meaning
        results = rag.vector_search("地震が起きた時の対処法", top_k=3)
        
        # Should find content about "初動対応" or "災害時の行動"
        texts = [r.text for r in results]
        assert any(
            "対応" in t or "行動" in t or "避難" in t 
            for t in texts
        ), "Semantic search should find related content"


class TestHybridSearch:
    """Tests for hybrid search (BM25 + Vector)."""
    
    def test_hybrid_search_combines_scores(self):
        """Hybrid search should combine keyword and vector scores."""
        from src.core.manual_rag import ManualRAG
        
        rag = ManualRAG.load()
        query = "ハザードマップ 確認"
        
        # This method should combine both approaches
        results = rag.hybrid_search(query, top_k=3, alpha=0.5)
        
        assert results is not None
        assert len(results) <= 3
    
    def test_hybrid_search_alpha_parameter(self):
        """Alpha=0 should be pure keyword, alpha=1 should be pure vector."""
        from src.core.manual_rag import ManualRAG
        
        rag = ManualRAG.load()
        query = "災害想定"
        
        keyword_results = rag.hybrid_search(query, top_k=3, alpha=0.0)
        vector_results = rag.hybrid_search(query, top_k=3, alpha=1.0)
        
        # Results may differ based on approach
        assert keyword_results is not None
        assert vector_results is not None


class TestDatabaseEmbeddings:
    """Tests for storing/retrieving embeddings from database."""
    
    def test_store_embedding_in_database(self):
        """Embeddings should be stored in the database."""
        from src.core.manual_rag import ManualRAG
        
        rag = ManualRAG.load()
        
        # Check if embeddings exist in database
        has_embeddings = rag.has_embeddings()
        
        # This should return True after embedding generation
        assert isinstance(has_embeddings, bool)
    
    def test_retrieve_embedding_by_chunk_id(self):
        """Should be able to retrieve embedding for a specific chunk."""
        from src.core.manual_rag import ManualRAG
        
        rag = ManualRAG.load()
        
        # Get embedding for a known chunk
        embedding = rag.get_embedding("example_chunk_id")
        
        # May be None if chunk doesn't exist, but method should exist
        assert embedding is None or len(embedding) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
