from typing import List, Dict, Any
from src.api.schemas import ApplicationRoot

class CompletionChecker:
    """
    Analyzes the Jigyokei Plan (ApplicationRoot) and returns completion status,
    scores, and missing fields tailored for the Dashboard UI.
    """

    @staticmethod
    def analyze(plan: ApplicationRoot) -> Dict[str, Any]:
        """
        Main entry point. Returns a dictionary containing:
        - total_score (0-100)
        - status ("critical", "warning", "success")
        - mandatory_progress (0.0-1.0)
        - recommended_progress (0.0-1.0)
        - missing_mandatory (List[str])
        - suggestions (List[str])
        - section_status (Dict)
        """
        
        # 1. Mandatory Checks
        # These block the application from being submitted.
        missing_mandatory = []
        
        # Basic Info
        if not plan.basic_info.corporate_name or plan.basic_info.corporate_name == "未設定":
            missing_mandatory.append({"section": "BasicInfo", "msg": "企業名が未入力です"})
        if not plan.basic_info.representative_name or plan.basic_info.representative_name == "未設定":
            missing_mandatory.append({"section": "BasicInfo", "msg": "代表者名が未入力です"})
        elif "　" not in plan.basic_info.representative_name:
             missing_mandatory.append({"section": "BasicInfo", "msg": "代表者名の姓と名の間に全角スペースが必要です (例: 経済　太郎)"})

        # Goals / Risks
        if not plan.goals.disaster_scenario.disaster_assumption or plan.goals.disaster_scenario.disaster_assumption == "未設定":
             missing_mandatory.append({"section": "Goals", "msg": "想定する自然災害（地震・水害等）が選択されていません"})
        
        # Response Procedures (Must have at least one valid entry)
        if not plan.response_procedures:
             missing_mandatory.append({"section": "ResponseProcedures", "msg": "初動対応（人命確保など）が一つも登録されていません"})
        
        # Measures (Must have at least one pre-disaster measure)
        if not plan.measures:
             missing_mandatory.append({"section": "Measures", "msg": "事前対策（ヒト・モノ・カネ・情報）が登録されていません"})

        # Financial Plan (Must have items)
        if not plan.financial_plan.items:
             missing_mandatory.append({"section": "FinancialPlan", "msg": "資金計画が入力されていません"})

        # PDCA
        if not plan.pdca.training_education or plan.pdca.training_education == "未設定":
             missing_mandatory.append({"section": "PDCA", "msg": "訓練・教育の計画が未入力です"})


        # 2. Recommended Checks
        # Validates quality and completeness for "Standard" level.
        suggestions = []
        rec_score = 0
        rec_total = 3 # Impact, Measures, Advanced Risks
        
        # Check for Detailed Impacts
        if plan.goals.disaster_scenario.impact_list:
            rec_score += 1
        else:
             suggestions.append("災害時の具体的な被害影響（ヒト・モノ・カネ・情報）を記述しましょう。")

        # Check for Infection/Cyber (Heuristic check in text)
        # Note: In a real scenario, this would check specific fields if schema supported them separately.
        # Here we look for keywords in what we have.
        has_cyber = False
        has_infection = False
        all_text = str(plan.model_dump())
        if "サイバー" in all_text or "ウイルス" in all_text or "情報セキュリティ" in all_text:
            has_cyber = True
        if "感染症" in all_text:
            has_infection = True
            
        if not has_cyber:
            suggestions.append("近年増加している「サイバー攻撃」への対策も追記することで、計画の実効性が高まります。")
        if not has_infection:
            suggestions.append("「感染症」パンデミック時の対応についても触れておくと安心です。")
            
        if has_cyber or has_infection:
            rec_score += 1
            
        # Check Measure Count (Quantity)
        if len(plan.measures) >= 3:
            rec_score += 1
        else:
            suggestions.append(f"事前対策が現在{len(plan.measures)}件です。ヒト・モノ・カネ・情報の4観点から、あと{3-len(plan.measures)}件ほど追加しましょう。")


        # 3. Calculation
        mandatory_total_checks = 6 # defined above
        mandatory_passed = mandatory_total_checks - len(missing_mandatory)
        mandatory_progress = mandatory_passed / mandatory_total_checks
        
        recommended_progress = rec_score / rec_total
        
        # Total Score (Weighted: Mandatory 70%, Recommended 30%)
        total_score = int((mandatory_progress * 70) + (recommended_progress * 30))
        
        status = "critical"
        if len(missing_mandatory) == 0:
            status = "success" # Ready to apply
        
        return {
            "total_score": total_score,
            "status": status,
            "mandatory_progress": mandatory_progress,
            "recommended_progress": recommended_progress,
            "missing_mandatory": missing_mandatory,
            "suggestions": suggestions,
            "counts": {
                "measures": len(plan.measures),
                "procedures": len(plan.response_procedures),
                "risks": len(plan.goals.disaster_scenario.impact_list) if plan.goals.disaster_scenario.impact_list else 0
            }
        }
