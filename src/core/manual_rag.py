"""
Manual RAG Module
Provides local vector search for certification manual chunks.
Designed for read-only operation at runtime (no API calls).
"""
import json
import os
import sqlite3
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class SearchResult:
    """Search result from vector database."""
    chunk_id: str
    text: str
    score: float
    metadata: Dict


class ManualRAG:
    """
    Local vector search engine for certification manual.
    Uses pre-computed embeddings stored in SQLite.
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        self._embeddings_cache: Dict[str, List[float]] = {}
        self._synonyms: Dict[str, Dict] = self._load_synonyms()
    
    def _load_synonyms(self) -> Dict[str, Dict]:
        """Load keyword synonyms for query expansion."""
        synonyms_path = os.path.join(
            os.path.dirname(__file__),
            "..", "data", "keyword_synonyms.json"
        )
        if os.path.exists(synonyms_path):
            try:
                with open(synonyms_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("keyword_synonyms", {})
            except (json.JSONDecodeError, IOError):
                pass
        return {}
    
    def _expand_query(self, query: str) -> List[str]:
        """Expand query with synonyms for better matching."""
        keywords = [query]
        
        # Check if query matches any synonym group
        for main_keyword, synonym_data in self._synonyms.items():
            if main_keyword in query or query in main_keyword:
                keywords.extend(synonym_data.get("synonyms", []))
            else:
                # Check synonyms
                for syn in synonym_data.get("synonyms", []):
                    if syn in query or query in syn:
                        keywords.append(main_keyword)
                        keywords.extend(synonym_data.get("synonyms", []))
                        break
        
        return list(set(keywords))
    
    @classmethod
    def load(cls, db_path: Optional[str] = None) -> "ManualRAG":
        """
        Load vector database from path.
        
        Args:
            db_path: Path to SQLite database. If None, uses default location.
            
        Returns:
            ManualRAG instance
        """
        if db_path is None:
            db_path = os.path.join(
                os.path.dirname(__file__),
                "..", "data", "vector_store.db"
            )
        return cls(db_path)
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._conn is None:
            if not os.path.exists(self.db_path):
                raise FileNotFoundError(f"Vector database not found: {self.db_path}")
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    # =========================================================================
    # Phase 2: Vector Search Methods
    # =========================================================================
    
    def _get_api_key(self) -> Optional[str]:
        """Load API key from secrets or environment."""
        try:
            import tomllib
            secrets_path = os.path.join(
                os.path.dirname(__file__), 
                "..", "..", ".streamlit", "secrets.toml"
            )
            if os.path.exists(secrets_path):
                with open(secrets_path, "rb") as f:
                    secrets = tomllib.load(f)
                return secrets.get("GEMINI_API_KEY") or secrets.get("GOOGLE_API_KEY")
        except:
            pass
        return os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text using ModelCommander.
        """
        from src.core.model_commander import get_commander
        commander = get_commander()
        
        try:
            return commander.embed_content(text)
        except Exception as e:
            raise RuntimeError(f"Embedding generation failed: {e}")
    
    def has_embeddings(self) -> bool:
        """Check if embeddings exist in the database."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM chunks WHERE embedding IS NOT NULL")
            count = cursor.fetchone()[0]
            return count > 0
        except (sqlite3.OperationalError, FileNotFoundError):
            return False
    
    def get_embedding(self, chunk_id: str) -> Optional[List[float]]:
        """Get embedding for a specific chunk from database."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT embedding FROM chunks WHERE chunk_id = ?", (chunk_id,))
            row = cursor.fetchone()
            if row and row[0]:
                import struct
                # Embeddings are stored as BLOB, decode as float array
                blob = row[0]
                num_floats = len(blob) // 4
                return list(struct.unpack(f'{num_floats}f', blob))
            return None
        except (sqlite3.OperationalError, FileNotFoundError):
            return None
    
    def vector_search(self, query: str, top_k: int = 3) -> List[SearchResult]:
        """
        Search using vector similarity (cosine similarity).
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of SearchResult sorted by similarity score
        """
        # Generate query embedding
        try:
            query_embedding = self.generate_embedding(query)
        except RuntimeError:
            # Fallback to keyword search if embedding fails
            return self.search(query, top_k)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        results = []
        
        try:
            cursor.execute("SELECT chunk_id, text, metadata, embedding FROM chunks")
            rows = cursor.fetchall()
            
            for row in rows:
                chunk_id = row["chunk_id"]
                text = row["text"]
                metadata = json.loads(row["metadata"]) if row["metadata"] else {}
                embedding_blob = row["embedding"]
                
                if embedding_blob:
                    import struct
                    num_floats = len(embedding_blob) // 4
                    chunk_embedding = list(struct.unpack(f'{num_floats}f', embedding_blob))
                    
                    # Calculate cosine similarity
                    score = self._cosine_similarity(query_embedding, chunk_embedding)
                    
                    # Normalize to 0-1 range (cosine similarity is -1 to 1)
                    normalized_score = (score + 1) / 2
                    
                    results.append(SearchResult(
                        chunk_id=chunk_id,
                        text=text,
                        score=normalized_score,
                        metadata=metadata
                    ))
            
            # Sort by score and return top_k
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:top_k]
            
        except sqlite3.OperationalError:
            return []
    
    def hybrid_search(
        self, 
        query: str, 
        top_k: int = 3, 
        alpha: float = 0.5
    ) -> List[SearchResult]:
        """
        Hybrid search combining keyword (BM25-like) and vector similarity.
        
        Args:
            query: Search query
            top_k: Number of results to return
            alpha: Weight for vector search (0=pure keyword, 1=pure vector)
            
        Returns:
            List of SearchResult with combined scores
        """
        # Get keyword results
        keyword_results = self.search(query, top_k=top_k * 2)
        
        # Get vector results
        vector_results = self.vector_search(query, top_k=top_k * 2)
        
        # Combine scores
        combined_scores: Dict[str, Dict] = {}
        
        # Add keyword scores
        max_keyword = max((r.score for r in keyword_results), default=1.0) or 1.0
        for r in keyword_results:
            normalized = r.score / max_keyword
            combined_scores[r.chunk_id] = {
                "text": r.text,
                "metadata": r.metadata,
                "keyword_score": normalized,
                "vector_score": 0.0
            }
        
        # Add vector scores
        for r in vector_results:
            if r.chunk_id in combined_scores:
                combined_scores[r.chunk_id]["vector_score"] = r.score
            else:
                combined_scores[r.chunk_id] = {
                    "text": r.text,
                    "metadata": r.metadata,
                    "keyword_score": 0.0,
                    "vector_score": r.score
                }
        
        # Calculate final combined score
        results = []
        for chunk_id, data in combined_scores.items():
            final_score = (
                (1 - alpha) * data["keyword_score"] + 
                alpha * data["vector_score"]
            )
            results.append(SearchResult(
                chunk_id=chunk_id,
                text=data["text"],
                score=final_score,
                metadata=data["metadata"]
            ))
        
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    
    def search(self, query: str, top_k: int = 3) -> List[SearchResult]:
        """
        Search for relevant chunks using keyword matching.
        
        Note: For v1, we use simple keyword matching.
        Full vector search will be implemented when embeddings are available.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of SearchResult
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Simple keyword search (fallback for v1)
        # Split query into keywords and search
        keywords = query.replace("　", " ").split()
        
        results = []
        
        try:
            cursor.execute("SELECT chunk_id, text, metadata FROM chunks")
            rows = cursor.fetchall()
            
            for row in rows:
                chunk_id = row["chunk_id"]
                text = row["text"]
                metadata = json.loads(row["metadata"]) if row["metadata"] else {}
                
                # Calculate simple keyword match score
                score = 0.0
                for keyword in keywords:
                    if keyword in text:
                        score += 1.0
                
                if score > 0:
                    results.append(SearchResult(
                        chunk_id=chunk_id,
                        text=text,
                        score=score / len(keywords) if keywords else 0,
                        metadata=metadata
                    ))
            
            # Sort by score and return top_k
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:top_k]
            
        except sqlite3.OperationalError:
            # Table doesn't exist yet
            return []
    
    def get_chunk(self, chunk_id: str) -> Optional[str]:
        """Get specific chunk by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT text FROM chunks WHERE chunk_id = ?", (chunk_id,))
            row = cursor.fetchone()
            return row["text"] if row else None
        except sqlite3.OperationalError:
            return None
    
    def get_examples_for_section(self, section_id: str) -> List[str]:
        """
        Get example texts for a specific certification section.
        
        Args:
            section_id: Section ID (e.g., "disaster_assumption")
            
        Returns:
            List of example texts
        """
        # Load certification requirements to get chunk IDs
        from src.core.certification_requirements import requirements_loader
        
        section = requirements_loader.get_section(section_id)
        if not section:
            return []
        
        examples = []
        for chunk_id in section.example_chunk_ids:
            text = self.get_chunk(chunk_id)
            if text:
                examples.append(text)
        
        return examples
    
    def close(self):
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None


# Singleton-like factory function with caching
_rag_instance: Optional[ManualRAG] = None

def get_rag() -> ManualRAG:
    """Get or create RAG instance. Cached for performance."""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = ManualRAG.load()
    return _rag_instance
