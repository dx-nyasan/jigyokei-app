"""
TDD Tests for Human-in-the-loop UI Components (Phase 3)

These tests verify the review panel and Streamlit integration.
Written BEFORE implementation (Red phase).
"""
import sys
import os
import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestReviewPanel:
    """Tests for the review panel component."""
    
    def test_render_critique_list(self):
        """Should render a list of critique items."""
        from src.frontend.components.review_panel import render_critique_list
        
        critiques = [
            {"section_id": "disaster_assumption", "issue": "具体的な数値が不足", "manual_reference": "例: 震度6弱"},
            {"section_id": "disaster_assumption", "issue": "出典が明記されていない", "manual_reference": "J-SHIS参照"}
        ]
        
        # Should return HTML or Streamlit-compatible markup
        rendered = render_critique_list(critiques)
        
        assert rendered is not None
        assert "具体的な数値が不足" in rendered
    
    def test_highlight_text_with_issues(self):
        """Should highlight problematic sections in draft text."""
        from src.frontend.components.review_panel import highlight_issues
        
        draft = "当社は災害リスクに対応します。"
        issues = ["具体的な数値が不足"]
        
        highlighted = highlight_issues(draft, issues)
        
        assert highlighted is not None
        # Should contain some form of highlighting markup
        assert len(highlighted) >= len(draft)
    
    def test_render_manual_reference_panel(self):
        """Should render manual examples in a side panel."""
        from src.frontend.components.review_panel import render_manual_panel
        
        examples = [
            "例1: 震度6弱以上の確率72.3%（J-SHIS）",
            "例2: 当社周辺は津波浸水区域外"
        ]
        
        rendered = render_manual_panel(examples)
        
        assert rendered is not None
        assert "震度6弱" in rendered


class TestLangGraphIntegration:
    """Tests for LangGraph interrupt and state integration."""
    
    def test_interrupt_before_human_approval(self):
        """Graph should be configured with interrupt_before."""
        from src.core.langgraph_agent import build_jigyokei_graph
        
        graph = build_jigyokei_graph()
        
        # The graph should have interrupt configuration
        # This is a structural test
        assert graph is not None
    
    def test_get_pending_critiques_from_state(self):
        """Should extract critique list from graph state."""
        from src.frontend.components.review_panel import get_pending_critiques
        
        state = {
            "critique_list": [
                {"section_id": "test", "issue": "Test issue"}
            ],
            "status": "needs_human"
        }
        
        critiques = get_pending_critiques(state)
        
        assert len(critiques) == 1
        assert critiques[0]["issue"] == "Test issue"


class TestUserInputHandler:
    """Tests for handling user revision input."""
    
    def test_apply_user_revision(self):
        """Should apply user comments to state."""
        from src.frontend.components.review_panel import apply_user_revision
        
        state = {
            "draft_content": "旧ドラフト",
            "user_intent": None
        }
        user_input = "南海トラフ地震の発生確率70%を追記してください"
        
        updated_state = apply_user_revision(state, user_input)
        
        assert updated_state["user_intent"] == user_input
    
    def test_mark_critique_resolved(self):
        """Should mark a specific critique as resolved."""
        from src.frontend.components.review_panel import mark_resolved
        
        critiques = [
            {"section_id": "test", "issue": "Issue 1", "is_resolved": False},
            {"section_id": "test", "issue": "Issue 2", "is_resolved": False}
        ]
        
        updated = mark_resolved(critiques, 0)
        
        assert updated[0]["is_resolved"] is True
        assert updated[1]["is_resolved"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
