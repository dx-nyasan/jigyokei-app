"""
Audit Agent Module
Provides LLM-based audit functionality for certification applications.
Uses explicit button trigger to minimize API calls.
"""
import json
import os
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
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



class SectionAuditResult(BaseModel):
    """Audit result for a single section."""
    name: str
    score: int = Field(ge=0, le=100)
    reason: str


class AuditResult(BaseModel):
    """Complete audit result."""
    total_score: int = Field(ge=0, le=100)
    sections: List[SectionAuditResult]
    improvements: List[str]
    raw_response: Optional[str] = None


AUDIT_SYSTEM_PROMPT = """あなたは中小企業庁の認定審査官として、事業継続力強化計画の申請書を厳格に評価してください。

【評価基準】

1. 災害想定 (20点満点)
- 具体的な震度・確率が数値で示されているか？(例: 震度6弱以上の確率72.3%)
- 出典（J-SHIS、ハザードマップ等）が明記されているか？

2. 事業影響 (20点満点)
- 物理的被害から事業停止への因果関係が明確か？
- 復旧までの期間が具体的に想定されているか？(例: 7日間休業)

3. 初動対応 (15点満点)
- 発災後の行動が時間軸で具体的か？
- 事前対策(preparation_content)が記載されているか？

4. 事前対策 (15点満点)
- ヒト・モノ・カネ・情報の4カテゴリが網羅されているか？
- 現在の取組と今後の計画が明確に分かれているか？

5. PDCA体制 (15点満点)
- 「教育及び訓練」の両方が含まれているか？(訓練だけは不可)
- 実施月が明記されているか？(12/17改修対応)
- 社内周知方法が具体的か？

6. 事業概要 (10点満点)
- サプライチェーン上の役割が明記されているか？
- 地域経済における重要性が説明されているか？

7. 基本情報 (5点満点)
- 必須項目がすべて入力されているか？

【出力形式】
以下のJSON形式で厳密に出力してください。他のテキストは一切含めないでください。

{
  "total_score": 0-100の整数,
  "sections": [
    {"name": "災害想定", "score": 0-20, "reason": "評価理由"},
    {"name": "事業影響", "score": 0-20, "reason": "評価理由"},
    {"name": "初動対応", "score": 0-15, "reason": "評価理由"},
    {"name": "事前対策", "score": 0-15, "reason": "評価理由"},
    {"name": "PDCA体制", "score": 0-15, "reason": "評価理由"},
    {"name": "事業概要", "score": 0-10, "reason": "評価理由"},
    {"name": "基本情報", "score": 0-5, "reason": "評価理由"}
  ],
  "improvements": ["改善提案1", "改善提案2", "改善提案3"]
}
"""


class AuditAgent:
    """
    Audit agent that evaluates application content from certification perspective.
    Designed to be triggered explicitly (button) to minimize API calls.
    """
    
    def __init__(self, model_name: str = "gemini-3-flash"):
        self.model_name = model_name
        self._model = None
    
    def _get_model(self):
        """Lazy initialization of Gemini model."""
        if self._model is None:
            self._model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.1  # Low temperature for consistent evaluation
                )
            )
        return self._model
    
    def audit(self, application_text: str) -> AuditResult:
        """
        Perform audit on application text.
        
        Args:
            application_text: Full text representation of the application
            
        Returns:
            AuditResult with scores, reasons, and improvement suggestions
        """
        model = self._get_model()
        
        prompt = f"""以下の事業継続力強化計画申請書を評価してください。

【申請書内容】
{application_text}

【評価を開始してください】"""
        
        try:
            response = model.generate_content(
                [{"role": "user", "parts": [{"text": AUDIT_SYSTEM_PROMPT + "\n\n" + prompt}]}]
            )
            
            raw_text = response.text
            
            # Parse JSON response
            result_data = json.loads(raw_text)
            
            return AuditResult(
                total_score=result_data.get("total_score", 0),
                sections=[
                    SectionAuditResult(**s) for s in result_data.get("sections", [])
                ],
                improvements=result_data.get("improvements", []),
                raw_response=raw_text
            )
            
        except json.JSONDecodeError as e:
            # Fallback if JSON parsing fails
            return AuditResult(
                total_score=0,
                sections=[],
                improvements=[f"監査結果のパースに失敗しました: {str(e)}"],
                raw_response=raw_text if 'raw_text' in locals() else None
            )
        except Exception as e:
            return AuditResult(
                total_score=0,
                sections=[],
                improvements=[f"監査API呼び出しに失敗しました: {str(e)}"],
                raw_response=None
            )
    
    def format_application_for_audit(self, plan) -> str:
        """
        Convert ApplicationRoot to text format for audit.
        
        Args:
            plan: ApplicationRoot instance
            
        Returns:
            Text representation of the plan
        """
        lines = []
        
        # Basic Info
        if plan.basic_info:
            bi = plan.basic_info
            lines.append("【基本情報】")
            lines.append(f"事業者名: {bi.corporate_name or '未入力'}")
            lines.append(f"法人番号: {bi.corporate_number or '未入力'}")
            lines.append(f"代表者: {bi.representative_name or '未入力'}")
            lines.append(f"資本金: {bi.capital or '未入力'}")
            lines.append(f"従業員数: {bi.employees or '未入力'}")
            lines.append("")
        
        # Business Overview
        if plan.goals:
            lines.append("【事業活動の概要】")
            lines.append(plan.goals.business_overview or "未入力")
            lines.append("")
            lines.append("【取組目的】")
            lines.append(plan.goals.business_purpose or "未入力")
            lines.append("")
        
        # Disaster Scenario
        if plan.goals and plan.goals.disaster_scenario:
            ds = plan.goals.disaster_scenario
            lines.append("【災害想定】")
            lines.append(ds.disaster_assumption or "未入力")
            lines.append("")
            
            if ds.impacts:
                lines.append("【事業活動への影響】")
                lines.append(f"人員への影響: {ds.impacts.impact_personnel or '未入力'}")
                lines.append(f"建物への影響: {ds.impacts.impact_building or '未入力'}")
                lines.append(f"資金への影響: {ds.impacts.impact_funds or '未入力'}")
                lines.append(f"情報への影響: {ds.impacts.impact_info or '未入力'}")
                lines.append("")
        
        # Response Procedures
        lines.append("【初動対応】")
        if plan.response_procedures:
            for i, proc in enumerate(plan.response_procedures, 1):
                lines.append(f"{i}. 項目: {proc.item or '未入力'}")
                lines.append(f"   取組内容: {proc.content or '未入力'}")
                lines.append(f"   事前対策: {proc.preparation_content or '未入力'}")
        else:
            lines.append("未入力")
        lines.append("")
        
        # Measures
        lines.append("【事前対策】")
        if plan.measures:
            m = plan.measures
            lines.append(f"ヒト: {m.personnel.current_measure or '未入力'} / {m.personnel.future_plan or '未入力'}")
            lines.append(f"モノ: {m.building.current_measure or '未入力'} / {m.building.future_plan or '未入力'}")
            lines.append(f"カネ: {m.money.current_measure or '未入力'} / {m.money.future_plan or '未入力'}")
            lines.append(f"情報: {m.data.current_measure or '未入力'} / {m.data.future_plan or '未入力'}")
        lines.append("")
        
        # PDCA
        lines.append("【PDCA体制】")
        if plan.pdca:
            lines.append(f"推進体制: {plan.pdca.management_system or '未入力'}")
            lines.append(f"訓練・教育: {plan.pdca.training_education or '未入力'}")
            lines.append(f"訓練実施月: {plan.pdca.training_month or '未入力'}")
            lines.append(f"計画見直し: {plan.pdca.plan_review or '未入力'}")
            lines.append(f"見直し実施月: {plan.pdca.review_month or '未入力'}")
            lines.append(f"社内周知: {plan.pdca.internal_publicity or '未入力'}")
        
        return "\n".join(lines)


# Convenience function
def run_audit(plan) -> AuditResult:
    """
    Convenience function to run audit on an ApplicationRoot.
    
    Args:
        plan: ApplicationRoot instance
        
    Returns:
        AuditResult
    """
    agent = AuditAgent()
    text = agent.format_application_for_audit(plan)
    return agent.audit(text)
