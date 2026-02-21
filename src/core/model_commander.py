"""
Model Commander: Self-healing model fallback utility using google-genai SDK.

This module provides centralized governance for all Gemini API interactions,
implementing a 3-tier fallback mechanism to maximize free tier usage and
ensure system stability under quota constraints.

Dependencies:
    - google-genai: Google's Generative AI SDK
    - Environment variable: GOOGLE_API_KEY

Usage Example:
    >>> from src.core.model_commander import get_commander
    >>> commander = get_commander()
    >>> response = commander.generate_content("reasoning", "Analyze this plan...")
    >>> embedding = commander.embed_content("Search query text")

See Also:
    - .agent/skills/model-commander/SKILL.md for governance protocol
    - docs/MODEL_FLIGHT_LOG.md for operation history
"""
import os
import time
import logging
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("model-commander")

# Tier definitions based on research (Update these as newer models release)
MODEL_TIERS = {
    "reasoning": ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"],
    "draft": ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"],
    "extraction": ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-flash-8b"],
    "embedding": ["gemini-embedding-001", "text-embedding-004"]
}

# Known End-of-Life (EOL) dates to trigger warnings
MODEL_EOL = {
    "gemini-2.0-flash": "2026-03-31",
    "gemini-2.0-flash-lite": "2026-03-31",
}

class ModelCommander:
    """Central governance layer for Gemini API interactions.
    
    Implements 3-tier fallback mechanism to maximize free tier usage
    and ensure system stability under quota constraints.
    
    Attributes:
        api_key: Google API key for authentication.
        client: Initialized genai.Client instance.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize ModelCommander with API credentials.
        
        Args:
            api_key: Optional API key. If not provided, reads from
                GOOGLE_API_KEY environment variable.
        
        Raises:
            ValueError: If no API key is available.
        """
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY is not set.")
        self.client = genai.Client(api_key=self.api_key)

    def generate_content(self, task_type: str, contents: Any, config: Optional[Dict] = None) -> Any:
        """Generate content with automatic 3-tier fallback.
        
        Attempts generation starting from Tier 1 (latest model) and
        falls back to lower tiers on quota exhaustion (429 errors).
        
        Args:
            task_type: Task category ('reasoning', 'draft', 'extraction').
                Determines which model tier list to use.
            contents: Prompt or content to generate from.
            config: Optional generation configuration dictionary.
        
        Returns:
            GenerateContentResponse from the successful model.
        
        Raises:
            Exception: If all tiers fail or a non-quota error occurs.
        """
        models = MODEL_TIERS.get(task_type, ["gemini-1.5-flash"])
        
        last_exception = None
        for i, model_name in enumerate(models):
            # EOL Warning check
            if model_name in MODEL_EOL:
                eol_date = MODEL_EOL[model_name]
                logger.warning(f"⚠️ MODEL DEPRECATION WARNING: '{model_name}' is scheduled for shutdown on {eol_date}. Consider shifting up.")

            try:
                logger.info(f"Attempting task '{task_type}' with model '{model_name}' (Tier {i+1})")
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=config
                )
                logger.info(f"Success with {model_name}")
                self._log_flight(task_type, model_name, i + 1, "SUCCESS")
                return response
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Tier {i+1} ({model_name}) failed: {error_msg}")
                if "429" in error_msg or "ResourceExhausted" in error_msg:
                    last_exception = e
                    continue # Fallback to next tier
                else:
                    self._log_flight(task_type, model_name, i + 1, f"ERROR: {error_msg}")
                    raise e # Non-quota error
        
        # If all tiers failed
        self._log_flight(task_type, "ALL_TIERS_FAILED", 3, str(last_exception))
        raise last_exception

    def embed_content(self, text: str, task_type: str = "retrieval_document") -> List[float]:
        """Generate text embedding with automatic fallback.
        
        Creates vector embeddings for semantic search and similarity tasks.
        Falls back to alternative embedding models on quota exhaustion.
        
        Args:
            text: Text content to embed.
            task_type: Embedding task type. Options include:
                - 'retrieval_document': For indexing documents
                - 'retrieval_query': For search queries
                - 'semantic_similarity': For similarity comparison
        
        Returns:
            List of float values representing the embedding vector.
        
        Raises:
            Exception: If all embedding models fail.
        """
        models = MODEL_TIERS.get("embedding", ["gemini-embedding-001"])
        
        last_exception = None
        for i, model_name in enumerate(models):
            try:
                response = self.client.models.embed_content(
                    model=model_name,
                    contents=text,
                    config=types.EmbedContentConfig(task_type=task_type)
                )
                self._log_flight("embedding", model_name, i + 1, "SUCCESS")
                # Handle both single and batch results if necessary, but manual_rag uses single
                return response.embeddings[0].values if hasattr(response, "embeddings") else response.embedding.values
            except Exception as e:
                if "429" in str(e) or "ResourceExhausted" in str(e):
                    last_exception = e
                    continue
                raise e
        raise last_exception

    def _log_flight(self, task_type: str, model: str, tier: int, status: str):
        """Record model usage to the flight log for monitoring.
        
        Appends a timestamped entry to docs/MODEL_FLIGHT_LOG.md for
        operational visibility and debugging.
        
        Args:
            task_type: The task category executed.
            model: Model name that was used.
            tier: Tier number (1=primary, 2=fallback1, 3=fallback2).
            status: Result status ('SUCCESS' or 'ERROR: <message>').
        """
        log_path = os.path.join(os.getcwd(), "docs", "MODEL_FLIGHT_LOG.md")
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        if not os.path.exists(log_path):
            with open(log_path, "w", encoding="utf-8") as f:
                f.write("# Model Flight Log\n\n| Timestamp | Task | Model | Tier | Status |\n| :--- | :--- | :--- | :--- | :--- |\n")
        
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"| {timestamp} | {task_type} | {model} | {tier} | {status} |\n")

# Singleton instance
_commander = None


def get_commander() -> ModelCommander:
    """Get or create the singleton ModelCommander instance.
    
    Returns:
        ModelCommander: The shared commander instance.
    
    Raises:
        ValueError: If GOOGLE_API_KEY is not configured.
    """
    global _commander
    if _commander is None:
        _commander = ModelCommander()
    return _commander
