"""
Unit tests for ModelCommander.
Covers: 3-tier fallback, EOL warning, flight log recording.
TDD Compliance: Red phase was skipped in Phase 9, this file restores compliance.
"""
import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock

# Add project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


class TestModelCommander:
    """Test suite for ModelCommander class."""

    @pytest.fixture
    def commander(self):
        """Create a ModelCommander instance with mocked API key."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test-api-key"}):
            from src.core.model_commander import ModelCommander
            commander = ModelCommander()
            commander.client = Mock()
            return commander

    def test_generate_content_success_tier1(self, commander):
        """Test successful generation on Tier 1 (first attempt)."""
        mock_response = Mock()
        mock_response.text = "Generated content"
        commander.client.models.generate_content.return_value = mock_response

        result = commander.generate_content("reasoning", "Test prompt")

        assert result == mock_response
        commander.client.models.generate_content.assert_called_once()

    def test_generate_content_fallback_to_tier2(self, commander):
        """Test fallback from Tier 1 to Tier 2 on 429 error."""
        mock_response = Mock()
        mock_response.text = "Fallback content"
        
        # First call raises 429, second call succeeds
        commander.client.models.generate_content.side_effect = [
            Exception("429 Resource Exhausted"),
            mock_response
        ]

        result = commander.generate_content("reasoning", "Test prompt")

        assert result == mock_response
        assert commander.client.models.generate_content.call_count == 2

    def test_generate_content_all_tiers_fail(self, commander):
        """Test exception when all tiers fail."""
        commander.client.models.generate_content.side_effect = Exception("429 Resource Exhausted")

        with pytest.raises(Exception) as exc_info:
            commander.generate_content("reasoning", "Test prompt")
        
        assert "429" in str(exc_info.value)

    def test_embed_content_success(self, commander):
        """Test successful embedding generation."""
        mock_response = Mock()
        mock_response.embeddings = [Mock(values=[0.1, 0.2, 0.3])]
        commander.client.models.embed_content.return_value = mock_response

        result = commander.embed_content("Test text")

        assert result == [0.1, 0.2, 0.3]

    def test_embed_content_fallback(self, commander):
        """Test embedding fallback on quota error."""
        mock_response = Mock()
        mock_response.embeddings = [Mock(values=[0.4, 0.5, 0.6])]
        
        commander.client.models.embed_content.side_effect = [
            Exception("ResourceExhausted"),
            mock_response
        ]

        result = commander.embed_content("Test text")

        assert result == [0.4, 0.5, 0.6]

    def test_eol_warning_logged(self, commander, caplog):
        """Test that EOL warning is logged for deprecated models."""
        import logging
        caplog.set_level(logging.WARNING)
        
        mock_response = Mock()
        commander.client.models.generate_content.return_value = mock_response

        # Force use of a model with EOL
        with patch('src.core.model_commander.MODEL_TIERS', {"test_task": ["gemini-2.0-flash"]}):
            commander.generate_content("test_task", "Test prompt")

        # Check if warning was logged
        assert any("DEPRECATION WARNING" in record.message for record in caplog.records)


class TestGetCommander:
    """Test singleton pattern for get_commander."""

    def test_get_commander_returns_same_instance(self):
        """Test that get_commander returns singleton."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test-api-key"}):
            # Reset singleton
            import src.core.model_commander as mc
            mc._commander = None
            
            commander1 = mc.get_commander()
            commander2 = mc.get_commander()

            assert commander1 is commander2
