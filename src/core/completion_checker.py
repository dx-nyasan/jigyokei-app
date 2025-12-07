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
        - total_score (0-100): Strict Certification Readiness Score
        - status ("critical", "warning", "success")
        - mandatory_progress (0.0-1.0): Completion rate of mandatory sections
        - missing_mandatory (List[str]): List of missing items
        - suggestions (List[str]): Quality improvement suggestions
        """
        
        # --- 1. Mandatory Progress (Start Rate) ---
        # Checks if sections are "touched" or minimal requirements met.
        mandatory_checks = {
            "BasicInfo": bool(plan.basic_info.corporate_name and plan.basic_info.representative_name),
            "Goals": bool(plan.goals.disaster_scenario.disaster_assumption and plan.goals.disaster_scenario.disaster_assumption != "未設定"),
            "ResponseProcedures": bool(len(plan.response_procedures) > 0),
            "Measures": bool(len(plan.measures) > 0),
            "FinancialPlan": bool(len(plan.financial_plan.items) > 0),
            "PDCA": bool(plan.pdca.training_education and plan.pdca.training_education != "未設定")
        }
        
        mandatory_passed_count = sum(mandatory_checks.values())
        mandatory_total = len(mandatory_checks)
        mandatory_progress = mandatory_passed_count / mandatory_total

        # Build detailed missing list for UI
        missing_mandatory = []
        if not mandatory_checks["BasicInfo"]: missing_mandatory.append({"section": "BasicInfo", "msg": "基本情報（企業名・代表者名）が未入力です"})
        if not mandatory_checks["Goals"]: missing_mandatory.append({"section": "Goals", "msg": "災害想定が選択されていません"})
        if not mandatory_checks["ResponseProcedures"]: missing_mandatory.append({"section": "ResponseProcedures", "msg": "初動対応が登録されていません"})
        if not mandatory_checks["Measures"]: missing_mandatory.append({"section": "Measures", "msg": "事前対策が登録されていません"})
        if not mandatory_checks["FinancialPlan"]: missing_mandatory.append({"section": "FinancialPlan", "msg": "資金計画が登録されていません"})
        if not mandatory_checks["PDCA"]: missing_mandatory.append({"section": "PDCA", "msg": "PDCA（訓練計画）が未入力です"})

        # --- 2. Strict Scoring (Total Score) ---
        # Criteria: 100 points = Fully compliant with Electronic Application Manual
        score = 0
        suggestions = []

        # A. Foundation (Max 50 pts) - Directly linked to Mandatory Checks
        # Using slightly different weights if needed, but simple distribution is fine.
        if mandatory_checks["BasicInfo"]: score += 8
        if mandatory_checks["Goals"]: score += 8
        if mandatory_checks["ResponseProcedures"]: score += 8
        if mandatory_checks["Measures"]: score += 8
        if mandatory_checks["FinancialPlan"]: score += 9
        if mandatory_checks["PDCA"]: score += 9
        
        # B. Quality & Quantity (Max 30 pts) - "Skasuka" Check
        # Business Overview Length
        ov_text = plan.goals.business_overview or ""
        if len(ov_text) >= 20: 
            score += 5
        elif mandatory_checks["Goals"]:
            suggestions.append("事業概要の記述が短すぎます。20文字以上で具体的に記述してください。")

        # Disaster Assumption Detail
        # Assuming impact_list has content
        has_risk_detail = False
        if plan.goals.disaster_scenario.impact_list:
             # Check if any text is decent length
             for imp in plan.goals.disaster_scenario.impact_list:
                 if len(imp.impact_building or "") > 10 or len(imp.impact_personnel or "") > 10:
                     has_risk_detail = True
                     break
        if has_risk_detail:
            score += 5
        elif mandatory_checks["Goals"]:
            suggestions.append("被害想定（ヒト/モノ）の記述が『未設定』または短すぎます。")

        # Response Count (Manual often suggests multiple)
        if len(plan.response_procedures) >= 2:
            score += 5
        elif mandatory_checks["ResponseProcedures"]:
            suggestions.append("初動対応は複数（人命安全、被害状況確認など）登録することが望ましいです。")

        # Measures Count (Manual requires covering Person, Building, Money, Info ideally, or at least 3)
        if len(plan.measures) >= 3:
            score += 10
        elif mandatory_checks["Measures"]:
            suggestions.append(f"事前対策が現在{len(plan.measures)}件です。認定には3件以上の具体的な対策登録を強く推奨します。")

        # Financial Items (redundancy check, maybe strictly need 'method' filled)
        financial_ok = False
        for f in plan.financial_plan.items:
            if f.amount > 0 or (f.method and len(f.method) > 2):
                financial_ok = True
        if financial_ok:
            score += 5
        elif mandatory_checks["FinancialPlan"]:
             suggestions.append("資金計画の内容（金額または調達方法）を具体的に入力してください。")

        # C. Compliance & Checklist (Max 20 pts) - Electronic Application Reqs
        # Checking AttachmentsChecklist booleans
        # Note: These default to False (None -> False in previous fix? No, None allowed).
        # We need to treat None as False for scoring.
        checklist = plan.attachments
        c_score = 0
        if checklist.certification_compliance: c_score += 4
        else: suggestions.append("認定要件への適合チェックが未完了です。")
        
        if checklist.no_false_statements: c_score += 4
        if checklist.not_anti_social: c_score += 4
        if checklist.legal_compliance: c_score += 4
        
        # Data Consent (Optional but good for 'application' readiness context?)
        # Let's check 'sme_requirements' instead as it is critical
        if checklist.sme_requirements: c_score += 4
        
        score += c_score
        
        # --- Final Adjustments ---
        total_score = min(100, score) # Cap at 100
        
        status = "critical"
        if len(missing_mandatory) == 0:
            status = "success"

        return {
            "total_score": total_score,
            "status": status,
            "mandatory_progress": mandatory_progress,
            "recommended_progress": 0.0, # Deprecated/Unused for calculation now
            "missing_mandatory": missing_mandatory,
            "suggestions": suggestions,
            "counts": {
                "measures": len(plan.measures),
                "procedures": len(plan.response_procedures),
                "risks": len(plan.goals.disaster_scenario.impact_list) if plan.goals.disaster_scenario.impact_list else 0
            }
        }
