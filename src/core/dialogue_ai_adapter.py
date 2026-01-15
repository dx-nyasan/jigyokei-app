"""
Dialogue Brancher AI Integration Adapter

Task 7: Integration of dialogue_brancher with AI Interviewer
Connects the branching logic to the chat interface for dynamic responses.
"""

from typing import Dict, List, Any, Optional, Callable
from src.core.dialogue_brancher import (
    DialogueBrancher,
    ResponseIntent,
    get_dialogue_branch
)


class DialogueAIAdapter:
    """
    Adapter to integrate DialogueBrancher with AIInterviewer.
    
    Provides:
    - Automatic topic detection
    - Intent-based response enhancement
    - Quick reply options generation
    """
    
    # Topic keywords for automatic topic detection
    TOPIC_KEYWORDS = {
        "disaster_measures": [
            "対策", "措置", "備え", "準備", "防災", "減災",
            "ヒト", "モノ", "カネ", "情報"
        ],
        "training_education": [
            "訓練", "教育", "研修", "練習", "避難訓練",
            "実施月", "見直し", "PDCA"
        ],
        "initial_response": [
            "初動", "発災直後", "避難", "安否確認",
            "緊急連絡", "対応手順"
        ],
        "business_impact": [
            "影響", "被害", "損害", "停止", "中断",
            "サプライチェーン", "取引先"
        ],
        "disaster_assumption": [
            "想定", "リスク", "地震", "水害", "津波",
            "J-SHIS", "ハザード"
        ]
    }
    
    def __init__(self):
        self.brancher = DialogueBrancher()
        self.current_topic: Optional[str] = None
        self.last_intent: Optional[ResponseIntent] = None
    
    def detect_topic(self, message: str) -> Optional[str]:
        """
        Detect conversation topic from message content.
        
        Args:
            message: User or AI message text
            
        Returns:
            Detected topic key or None
        """
        message_lower = message.lower()
        
        for topic, keywords in self.TOPIC_KEYWORDS.items():
            for keyword in keywords:
                if keyword in message_lower:
                    self.current_topic = topic
                    return topic
        
        return self.current_topic  # Keep previous topic if no new one detected
    
    def analyze_response(self, user_response: str) -> Dict[str, Any]:
        """
        Analyze user response and determine branching action.
        
        Args:
            user_response: User's message text
            
        Returns:
            {
                "topic": str or None,
                "intent": str,
                "should_branch": bool,
                "suggested_response": str or None,
                "quick_replies": List[str] or None
            }
        """
        # Detect topic if not set
        topic = self.detect_topic(user_response)
        
        # Get branching action
        if topic:
            branch_result = get_dialogue_branch(topic, user_response)
            self.last_intent = ResponseIntent(branch_result["intent"])
            
            return {
                "topic": topic,
                "intent": branch_result["intent"],
                "should_branch": branch_result["next_question"] is not None,
                "suggested_response": branch_result["next_question"],
                "quick_replies": branch_result["options"]
            }
        
        # Default fallback
        intent = self.brancher.detect_intent(user_response)
        self.last_intent = intent
        
        return {
            "topic": None,
            "intent": intent.value,
            "should_branch": False,
            "suggested_response": None,
            "quick_replies": None
        }
    
    def get_enhanced_prompt_suffix(self, user_response: str) -> str:
        """
        Get prompt suffix to enhance AI response based on user intent.
        
        This suffix can be appended to the AI's system prompt to guide
        the response style based on detected user needs.
        
        Args:
            user_response: User's message text
            
        Returns:
            Prompt suffix string to guide AI response
        """
        analysis = self.analyze_response(user_response)
        intent = analysis["intent"]
        
        if intent == "need_help":
            return """
【ユーザー意図検出: ヘルプ要求】
ユーザーは情報や例を求めています。具体的な例を挙げて説明してください。
"""
        
        elif intent == "negative":
            return """
【ユーザー意図検出: 否定的/未対応】
ユーザーはまだ対策ができていないようです。責めずに、簡単に始められる方法を提案してください。
"""
        
        elif intent == "has_existing":
            return """
【ユーザー意図検出: 既存対策あり】
ユーザーは既に対策を持っているようです。詳細を聞いて計画書に記載できる形式で整理してください。
"""
        
        elif intent == "skip":
            return """
【ユーザー意図検出: スキップ希望】
ユーザーはこの質問を後で回答したいようです。了承して次の質問に進んでください。
"""
        
        # Default: no special handling
        return ""
    
    def generate_quick_replies(self, ai_message: str) -> List[str]:
        """
        Generate contextual quick reply options based on AI message.
        
        Args:
            ai_message: AI's response message
            
        Returns:
            List of quick reply option strings
        """
        # Detect topic from AI message
        topic = self.detect_topic(ai_message)
        
        # Topic-specific quick replies
        if topic == "disaster_measures":
            return ["対策はあります", "まだできていません", "何から始めればいいですか？"]
        
        elif topic == "training_education":
            return ["毎年9月に実施", "まだ実施していません", "どんな訓練が必要ですか？"]
        
        elif topic == "disaster_assumption":
            return ["地震を想定", "水害を想定", "J-SHISを確認します"]
        
        # Default quick replies
        return ["はい", "いいえ", "わからないので教えてください"]


# Convenience function for quick integration
def enhance_ai_response(user_message: str, ai_response: str) -> Dict[str, Any]:
    """
    Enhance AI response with branching information.
    
    Args:
        user_message: User's input message
        ai_response: AI's generated response
        
    Returns:
        {
            "response": str (original AI response),
            "quick_replies": List[str],
            "topic": str or None,
            "intent": str
        }
    """
    adapter = DialogueAIAdapter()
    analysis = adapter.analyze_response(user_message)
    quick_replies = adapter.generate_quick_replies(ai_response)
    
    return {
        "response": ai_response,
        "quick_replies": quick_replies,
        "topic": analysis["topic"],
        "intent": analysis["intent"]
    }
