"""
Auto-Refinement Agent Module
Provides LLM-based text refinement to certification level.
One-click improvement from draft to certification-quality text.
"""
import os
import json
from typing import Optional
from pydantic import BaseModel
import google.generativeai as genai


# Configure Gemini API key from secrets.toml
def _load_api_key():
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

_api_key = _load_api_key()
if _api_key:
    genai.configure(api_key=_api_key)


class RefinementResult(BaseModel):
    """Result of text refinement."""
    original_text: str
    refined_text: str
    improvements_made: list[str]
    confidence_score: int  # 1-100


REFINEMENT_PROMPTS = {
    "disaster_assumption": """あなたは事業継続力強化計画の専門家です。以下の「災害想定」のテキストを認定レベルに改善してください。

【改善ポイント】
1. 具体的な震度・発生確率を数値で明記（例：震度6弱以上の確率72.3%）
2. 出典を明記（J-SHIS、ハザードマップ等）
3. 津波がある地域は津波到達時間・高さを記載
4. 地域固有のリスクを具体的に記述

【入力テキスト】
{input_text}

【出力形式】
以下のJSON形式で出力してください：
{{
    "refined_text": "改善後のテキスト",
    "improvements_made": ["改善点1", "改善点2"],
    "confidence_score": 85
}}
""",
    
    "business_impact": """あなたは事業継続力強化計画の専門家です。以下の「事業影響」のテキストを認定レベルに改善してください。

【改善ポイント】
1. 物理的被害から事業停止への因果関係を明確に
2. 復旧までの期間を具体的に（例：7日間休業）
3. サプライチェーンへの影響を記載
4. 売上・資金繰りへの具体的影響を数値化

【入力テキスト】
{input_text}

【出力形式】
以下のJSON形式で出力してください：
{{
    "refined_text": "改善後のテキスト",
    "improvements_made": ["改善点1", "改善点2"],
    "confidence_score": 85
}}
""",
    
    "response_procedures": """あなたは事業継続力強化計画の専門家です。以下の「初動対応」のテキストを認定レベルに改善してください。

【改善ポイント】
1. 発災後の時間軸を明確に（発災後30分以内、2時間以内等）
2. 「発災直後の行動」と「事前対策」を明確に分離
3. 具体的な判断基準を記載（震度5強以上の場合等）
4. 連絡先・報告先を具体的に

【入力テキスト】
{input_text}

【出力形式】
以下のJSON形式で出力してください：
{{
    "refined_text": "改善後のテキスト",
    "improvements_made": ["改善点1", "改善点2"],
    "confidence_score": 85
}}
""",
    
    "measures": """あなたは事業継続力強化計画の専門家です。以下の「事前対策」のテキストを認定レベルに改善してください。

【改善ポイント】
1. 現在の取組と今後の計画を明確に分離
2. ヒト・モノ・カネ・情報の4カテゴリを網羅
3. 具体的な対策内容（多能工化、バックアップ、保険等）
4. 実施時期・予算があれば記載

【入力テキスト】
{input_text}

【出力形式】
以下のJSON形式で出力してください：
{{
    "refined_text": "改善後のテキスト",
    "improvements_made": ["改善点1", "改善点2"],
    "confidence_score": 85
}}
""",
    
    "pdca": """あなたは事業継続力強化計画の専門家です。以下の「PDCA体制」のテキストを認定レベルに改善してください。

【改善ポイント】
1. 「訓練」だけでなく「教育及び訓練」と表記（12/17対応）
2. 実施月を明記（毎年◯月）
3. 社内周知方法を具体的に（掲示板、朝礼、社内報等）
4. 計画見直しの時期・方法を明記

【入力テキスト】
{input_text}

【出力形式】
以下のJSON形式で出力してください：
{{
    "refined_text": "改善後のテキスト",
    "improvements_made": ["改善点1", "改善点2"],
    "confidence_score": 85
}}
"""
}


class AutoRefinementAgent:
    """
    Agent for automatically refining application text to certification level.
    """
    
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.model_name = model_name
        self._model = None
    
    def _get_model(self):
        """Lazy initialization of Gemini model."""
        if self._model is None:
            self._model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.3  # Moderate creativity for refinement
                )
            )
        return self._model
    
    def refine(self, section_type: str, input_text: str) -> RefinementResult:
        """
        Refine input text to certification level.
        
        Args:
            section_type: One of "disaster_assumption", "business_impact", 
                         "response_procedures", "measures", "pdca"
            input_text: Original text to refine
            
        Returns:
            RefinementResult with refined text and improvements
        """
        if section_type not in REFINEMENT_PROMPTS:
            return RefinementResult(
                original_text=input_text,
                refined_text=input_text,
                improvements_made=["対応するセクションタイプがありません"],
                confidence_score=0
            )
        
        if not input_text or len(input_text.strip()) < 10:
            return RefinementResult(
                original_text=input_text,
                refined_text=input_text,
                improvements_made=["入力テキストが短すぎます。詳細を追加してください。"],
                confidence_score=0
            )
        
        model = self._get_model()
        prompt = REFINEMENT_PROMPTS[section_type].format(input_text=input_text)
        
        try:
            response = model.generate_content(prompt)
            result_data = json.loads(response.text)
            
            return RefinementResult(
                original_text=input_text,
                refined_text=result_data.get("refined_text", input_text),
                improvements_made=result_data.get("improvements_made", []),
                confidence_score=result_data.get("confidence_score", 50)
            )
            
        except json.JSONDecodeError as e:
            return RefinementResult(
                original_text=input_text,
                refined_text=input_text,
                improvements_made=[f"結果のパースに失敗: {str(e)}"],
                confidence_score=0
            )
        except Exception as e:
            return RefinementResult(
                original_text=input_text,
                refined_text=input_text,
                improvements_made=[f"API呼び出しに失敗: {str(e)}"],
                confidence_score=0
            )


# Convenience function
def refine_text(section_type: str, text: str) -> RefinementResult:
    """
    Convenience function to refine text.
    
    Args:
        section_type: Section type (disaster_assumption, business_impact, etc.)
        text: Text to refine
        
    Returns:
        RefinementResult
    """
    agent = AutoRefinementAgent()
    return agent.refine(section_type, text)
