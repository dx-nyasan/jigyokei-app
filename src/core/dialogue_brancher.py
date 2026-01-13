"""
Dialogue Branching Logic for Dynamic Conversation Flow

Task 7: Phase 3 Implementation
Enables response-based branching for more intelligent dialogue.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ResponseIntent(Enum):
    """Detected intent from user response."""
    AFFIRMATIVE = "affirmative"      # はい、Yes系
    NEGATIVE = "negative"            # いいえ、No系
    NEED_HELP = "need_help"          # わからない、教えて
    HAS_EXISTING = "has_existing"    # 既にある、対策済み
    SKIP = "skip"                    # 後で、スキップ
    UNKNOWN = "unknown"


@dataclass
class BranchAction:
    """Action to take based on detected intent."""
    intent: ResponseIntent
    next_question: str
    options: Optional[List[str]] = None
    explanation: Optional[str] = None


class DialogueBrancher:
    """
    Analyzes user responses and determines appropriate branching.
    
    理念対応:
    - 「引き出し」: 回答内容に応じた動的な深掘り
    - 「導く」: 適切なガイダンスへの誘導
    """
    
    # Keyword patterns for intent detection
    INTENT_PATTERNS = {
        ResponseIntent.AFFIRMATIVE: [
            "はい", "yes", "うん", "そう", "ええ", "その通り",
            "進めます", "お願い", "了解", "OK", "わかりました"
        ],
        ResponseIntent.NEGATIVE: [
            "いいえ", "no", "ない", "ありません", "まだ", "していない",
            "できていない", "未対応", "検討中"
        ],
        ResponseIntent.NEED_HELP: [
            "わからない", "教えて", "どうすれば", "例", "サンプル",
            "ヘルプ", "意味", "何", "どういう", "具体的に"
        ],
        ResponseIntent.HAS_EXISTING: [
            "既に", "すでに", "もう", "対策済み", "あります",
            "やっています", "整備済み", "完了"
        ],
        ResponseIntent.SKIP: [
            "後で", "スキップ", "次", "飛ばして", "パス",
            "また今度", "保留"
        ]
    }
    
    # Branching responses for common topics
    BRANCH_TEMPLATES = {
        "disaster_measures": {
            ResponseIntent.AFFIRMATIVE: BranchAction(
                intent=ResponseIntent.AFFIRMATIVE,
                next_question="素晴らしいですね！具体的にどのような対策を行っていますか？",
                options=["文書化されている", "口頭レベル", "これから整備予定"]
            ),
            ResponseIntent.NEGATIVE: BranchAction(
                intent=ResponseIntent.NEGATIVE,
                next_question="承知しました。対策がまだの場合でも大丈夫です。\n\nまずは**簡単にできる対策**から始めましょう。以下のどれから着手しますか？",
                options=["緊急連絡網の整備", "避難経路の確認", "保険の確認"],
                explanation="【他社事例】多くの企業は緊急連絡網の整備から始めています。従業員の連絡先リストを作成するだけでも立派な対策です。"
            ),
            ResponseIntent.NEED_HELP: BranchAction(
                intent=ResponseIntent.NEED_HELP,
                next_question="災害対策の例をご紹介します。\n\n**人（従業員）の対策例:**\n- 緊急連絡網の整備\n- 多能工化の推進\n- 安否確認システムの導入\n\nどれか興味のあるものはありますか？",
                options=["緊急連絡網について詳しく", "多能工化とは？", "安否確認システムとは？"]
            ),
            ResponseIntent.HAS_EXISTING: BranchAction(
                intent=ResponseIntent.HAS_EXISTING,
                next_question="既に対策があるのですね！計画書に記載するため、**現在実施している対策の内容**を教えてください。",
                options=None
            )
        },
        "training_education": {
            ResponseIntent.AFFIRMATIVE: BranchAction(
                intent=ResponseIntent.AFFIRMATIVE,
                next_question="訓練を実施されているのですね。**何月に訓練を行っていますか？**（電子申請では訓練月の入力が必須です）",
                options=["毎年5月頃", "毎年9月（防災の日に合わせて）", "年2回", "不定期"]
            ),
            ResponseIntent.NEGATIVE: BranchAction(
                intent=ResponseIntent.NEGATIVE,
                next_question="まだ訓練を実施されていないのですね。\n\n事業継続力強化計画では**訓練の予定月**を記載する必要があります。以下の時期はいかがですか？",
                options=["毎年9月（防災の日）", "毎年3月（年度末）", "毎年6月（梅雨前）"],
                explanation="【ポイント】初めての場合は「防災の日（9月1日）」に合わせた訓練が覚えやすく、おすすめです。"
            )
        }
    }
    
    def detect_intent(self, response: str) -> ResponseIntent:
        """
        Detect user intent from response text.
        
        Args:
            response: User's response text
            
        Returns:
            Detected ResponseIntent
        """
        response_lower = response.lower()
        
        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if pattern in response_lower:
                    return intent
        
        return ResponseIntent.UNKNOWN
    
    def get_branch_action(self, topic: str, response: str) -> Optional[BranchAction]:
        """
        Get the appropriate branch action based on topic and response.
        
        Args:
            topic: Current conversation topic (e.g., "disaster_measures")
            response: User's response text
            
        Returns:
            BranchAction with next steps, or None if topic not found
        """
        if topic not in self.BRANCH_TEMPLATES:
            return None
        
        intent = self.detect_intent(response)
        topic_branches = self.BRANCH_TEMPLATES[topic]
        
        if intent in topic_branches:
            return topic_branches[intent]
        
        # Default fallback for unknown intent
        return BranchAction(
            intent=ResponseIntent.UNKNOWN,
            next_question="もう少し詳しく教えていただけますか？",
            options=["はい", "いいえ", "わからない"]
        )
    
    def format_branch_response(self, action: BranchAction) -> str:
        """
        Format a branch action into a displayable response.
        
        Args:
            action: BranchAction to format
            
        Returns:
            Formatted response string
        """
        response = action.next_question
        
        if action.explanation:
            response += f"\n\n{action.explanation}"
        
        return response
    
    def get_branch_options(self, action: BranchAction) -> Optional[List[str]]:
        """Get quick reply options from a branch action."""
        return action.options


# Convenience function for integration
def get_dialogue_branch(topic: str, user_response: str) -> Dict[str, Any]:
    """
    Main interface for dialogue branching.
    
    Args:
        topic: Current conversation topic
        user_response: User's response text
        
    Returns:
        {
            "intent": str,
            "next_question": str,
            "options": List[str] or None,
            "explanation": str or None
        }
    """
    brancher = DialogueBrancher()
    action = brancher.get_branch_action(topic, user_response)
    
    if action:
        return {
            "intent": action.intent.value,
            "next_question": brancher.format_branch_response(action),
            "options": action.options,
            "explanation": action.explanation
        }
    
    return {
        "intent": "unknown",
        "next_question": None,
        "options": None,
        "explanation": None
    }
