"""
Unit tests for dialogue_brancher.py

Task 3: New Module Tests
"""

import pytest
from src.core.dialogue_brancher import (
    DialogueBrancher,
    ResponseIntent,
    BranchAction,
    get_dialogue_branch
)


class TestResponseIntent:
    """Tests for ResponseIntent enum."""
    
    def test_intent_values(self):
        """Test ResponseIntent enum has expected values."""
        assert ResponseIntent.AFFIRMATIVE.value == "affirmative"
        assert ResponseIntent.NEGATIVE.value == "negative"
        assert ResponseIntent.NEED_HELP.value == "need_help"
        assert ResponseIntent.HAS_EXISTING.value == "has_existing"
        assert ResponseIntent.SKIP.value == "skip"
        assert ResponseIntent.UNKNOWN.value == "unknown"


class TestDialogueBrancher:
    """Tests for DialogueBrancher class."""
    
    def test_brancher_initialization(self):
        """Test DialogueBrancher initializes correctly."""
        brancher = DialogueBrancher()
        assert hasattr(brancher, "INTENT_PATTERNS")
        assert hasattr(brancher, "BRANCH_TEMPLATES")
    
    def test_detect_intent_affirmative(self):
        """Test detecting affirmative intent."""
        brancher = DialogueBrancher()
        
        assert brancher.detect_intent("はい、そうです") == ResponseIntent.AFFIRMATIVE
        assert brancher.detect_intent("そうです") == ResponseIntent.AFFIRMATIVE
        assert brancher.detect_intent("お願いします") == ResponseIntent.AFFIRMATIVE
        assert brancher.detect_intent("ok") == ResponseIntent.AFFIRMATIVE  # lowercase works
    
    def test_detect_intent_negative(self):
        """Test detecting negative intent."""
        brancher = DialogueBrancher()
        
        assert brancher.detect_intent("いいえ") == ResponseIntent.NEGATIVE
        assert brancher.detect_intent("まだありません") == ResponseIntent.NEGATIVE
        assert brancher.detect_intent("できていない") == ResponseIntent.NEGATIVE
    
    def test_detect_intent_need_help(self):
        """Test detecting need_help intent."""
        brancher = DialogueBrancher()
        
        # Using exact patterns from INTENT_PATTERNS
        assert brancher.detect_intent("教えて") == ResponseIntent.NEED_HELP
        assert brancher.detect_intent("例") == ResponseIntent.NEED_HELP
        assert brancher.detect_intent("ヘルプ") == ResponseIntent.NEED_HELP
    
    def test_detect_intent_has_existing(self):
        """Test detecting has_existing intent."""
        brancher = DialogueBrancher()
        
        assert brancher.detect_intent("既にあります") == ResponseIntent.HAS_EXISTING
        assert brancher.detect_intent("対策済みです") == ResponseIntent.HAS_EXISTING
    
    def test_detect_intent_skip(self):
        """Test detecting skip intent."""
        brancher = DialogueBrancher()
        
        assert brancher.detect_intent("後で") == ResponseIntent.SKIP
        assert brancher.detect_intent("スキップ") == ResponseIntent.SKIP
    
    def test_detect_intent_unknown(self):
        """Test detecting unknown intent."""
        brancher = DialogueBrancher()
        
        assert brancher.detect_intent("random text xyz") == ResponseIntent.UNKNOWN
    
    def test_get_branch_action_disaster_measures(self):
        """Test getting branch action for disaster_measures topic."""
        brancher = DialogueBrancher()
        
        action = brancher.get_branch_action("disaster_measures", "はい")
        
        assert action is not None
        assert action.intent == ResponseIntent.AFFIRMATIVE
        assert action.next_question is not None
    
    def test_get_branch_action_unknown_topic(self):
        """Test getting branch action for unknown topic."""
        brancher = DialogueBrancher()
        
        action = brancher.get_branch_action("unknown_topic", "はい")
        
        assert action is None
    
    def test_format_branch_response(self):
        """Test formatting branch response."""
        brancher = DialogueBrancher()
        action = BranchAction(
            intent=ResponseIntent.AFFIRMATIVE,
            next_question="テスト質問",
            explanation="テスト説明"
        )
        
        response = brancher.format_branch_response(action)
        
        assert "テスト質問" in response
        assert "テスト説明" in response
    
    def test_get_branch_options(self):
        """Test getting branch options."""
        brancher = DialogueBrancher()
        action = BranchAction(
            intent=ResponseIntent.AFFIRMATIVE,
            next_question="質問",
            options=["選択肢1", "選択肢2"]
        )
        
        options = brancher.get_branch_options(action)
        
        assert options == ["選択肢1", "選択肢2"]


class TestBranchAction:
    """Tests for BranchAction dataclass."""
    
    def test_branch_action_creation(self):
        """Test BranchAction creation."""
        action = BranchAction(
            intent=ResponseIntent.NEGATIVE,
            next_question="次の質問",
            options=["はい", "いいえ"],
            explanation="説明文"
        )
        
        assert action.intent == ResponseIntent.NEGATIVE
        assert action.next_question == "次の質問"
        assert len(action.options) == 2
        assert action.explanation == "説明文"


class TestConvenienceFunction:
    """Tests for get_dialogue_branch convenience function."""
    
    def test_get_dialogue_branch_valid(self):
        """Test get_dialogue_branch with valid inputs."""
        result = get_dialogue_branch("disaster_measures", "はい")
        
        assert result["intent"] == "affirmative"
        assert result["next_question"] is not None
    
    def test_get_dialogue_branch_unknown_topic(self):
        """Test get_dialogue_branch with unknown topic."""
        result = get_dialogue_branch("unknown", "test")
        
        assert result["intent"] == "unknown"
        assert result["next_question"] is None
