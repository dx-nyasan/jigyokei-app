"""
TDD Tests for Production Integration (Phase 5)

Tests for integrating LangGraph agent with app_hybrid.py.
Written BEFORE implementation (Red phase).
"""
import sys
import os
import pytest
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestLangGraphSessionIntegration:
    """Tests for LangGraph session management integration."""
    
    def test_create_langgraph_session(self):
        """Should create a LangGraph session with checkpointer."""
        from src.core.langgraph_integration import create_langgraph_session
        
        session_id = "test_session_123"
        session = create_langgraph_session(session_id)
        
        assert session is not None
        assert session.session_id == session_id
    
    def test_restore_session_from_checkpoint(self):
        """Should restore session state from checkpoint."""
        from src.core.langgraph_integration import (
            create_langgraph_session, 
            restore_session
        )
        
        session_id = "test_session_456"
        session = create_langgraph_session(session_id)
        
        # Simulate some state
        session.state["current_section"] = "disaster_assumption"
        session.save_checkpoint()
        
        # Restore
        restored = restore_session(session_id)
        assert restored.state["current_section"] == "disaster_assumption"


class TestStreamlitStateSync:
    """Tests for syncing Streamlit session state with LangGraph."""
    
    def test_sync_streamlit_to_langgraph(self):
        """Should sync Streamlit session to LangGraph state."""
        from src.core.langgraph_integration import sync_to_langgraph
        
        streamlit_state = {
            "applicant_name": "テスト株式会社",
            "location": "東京都千代田区",
            "interview_log": ["Q: 御社の事業内容は?", "A: IT事業です"]
        }
        
        langgraph_state = sync_to_langgraph(streamlit_state)
        
        assert langgraph_state["applicant_name"] == "テスト株式会社"
        assert "interview_log" in langgraph_state or "raw_interview_text" in langgraph_state
    
    def test_sync_langgraph_to_streamlit(self):
        """Should sync LangGraph state back to Streamlit."""
        from src.core.langgraph_integration import sync_to_streamlit
        
        langgraph_state = {
            "draft_content": "生成された下書き内容",
            "critique_list": [{"issue": "数値不足"}],
            "status": "reviewing"
        }
        
        streamlit_updates = sync_to_streamlit(langgraph_state)
        
        assert "draft_content" in streamlit_updates
        assert streamlit_updates["critique_list"] == langgraph_state["critique_list"]


class TestLangGraphRunner:
    """Tests for running LangGraph workflow from Streamlit."""
    
    def test_run_section_generation(self):
        """Should run section generation workflow."""
        from src.core.langgraph_integration import LangGraphRunner
        
        runner = LangGraphRunner()
        
        initial_state = {
            "applicant_name": "テスト会社",
            "location": "大阪府",
            "raw_interview_text": "事業内容のテスト",
            "current_section": "disaster_assumption"
        }
        
        # Mock the graph execution by setting _graph directly
        mock_graph = Mock()
        mock_graph.invoke.return_value = {
            "draft_content": "生成された内容",
            "status": "reviewing"
        }
        runner._graph = mock_graph
        
        result = runner.run_section(initial_state)
        
        assert "draft_content" in result
    
    def test_handle_human_interrupt(self):
        """Should handle human-in-the-loop interrupt."""
        from src.core.langgraph_integration import LangGraphRunner
        
        runner = LangGraphRunner()
        
        # When graph returns with needs_human status
        state = {
            "status": "needs_human",
            "critique_list": [{"issue": "確認が必要"}]
        }
        
        is_waiting = runner.is_waiting_for_human(state)
        assert is_waiting is True
    
    def test_resume_after_human_input(self):
        """Should resume workflow after human provides input."""
        from src.core.langgraph_integration import LangGraphRunner
        
        runner = LangGraphRunner()
        
        state = {
            "status": "needs_human",
            "user_intent": None
        }
        
        human_input = "震度6弱の確率を追記してください"
        
        mock_graph = Mock()
        mock_graph.invoke.return_value = {"status": "writing"}
        runner._graph = mock_graph
        
        resumed = runner.resume_with_input(state, human_input)
        
        assert resumed is not None


class TestErrorHandling:
    """Tests for error handling in production integration."""
    
    def test_handle_api_error_gracefully(self):
        """Should handle API errors without crashing."""
        from src.core.langgraph_integration import LangGraphRunner
        
        runner = LangGraphRunner()
        
        mock_graph = Mock()
        mock_graph.invoke.side_effect = Exception("API Error")
        runner._graph = mock_graph
        
        result = runner.run_section_safe({
            "current_section": "disaster_assumption"
        })
        
        assert result["status"] == "error"
        assert "error_message" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
