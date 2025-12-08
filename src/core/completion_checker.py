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
            "ResponseProcedures": bool(len(plan.response_procedures) >= 2), # Stricter: Need multiple items
            "Measures": bool(len(plan.measures) >= 2), # Stricter: Need multiple items
            "FinancialPlan": bool(len(plan.financial_plan.items) > 0),
            "PDCA": bool(plan.pdca.training_education and plan.pdca.training_education != "未設定")
        }
        
        mandatory_passed_count = sum(mandatory_checks.values())
        mandatory_total = len(mandatory_checks)
        mandatory_progress = mandatory_passed_count / mandatory_total


        # Helper function for severity classification
        def classify_severity(value, field_name: str) -> str:
            """Classify field severity: 'critical' or 'warning'"""
            # Critical: None, empty string, empty list/dict
            if value is None:
                return "critical"
            if isinstance(value, str) and (not value or value.strip() == ""):
                return "critical"
            if isinstance(value, (list, dict)) and len(value) == 0:
                return "critical"
            
            # Warning: Minimal/placeholder content
            if isinstance(value, str):
                minimal_phrases = ["なし", "未設定", "-", "N/A", "該当なし"]
                if value.strip() in minimal_phrases or len(value.strip()) < 10:
                    return "warning"
            
            # Otherwise, consider it complete
            return "complete"

        # Build detailed missing list for UI (WITH SEVERITY)
        missing_mandatory = []
        if not mandatory_checks["BasicInfo"]:
            severity = classify_severity(plan.basic_info.corporate_name if plan.basic_info else None, "corporate_name")
            missing_mandatory.append({
                "section": "BasicInfo",
                "msg": "基本情報（企業名・代表者名）が未入力です",
                "severity": severity
            })
        if not mandatory_checks["Goals"]:
            severity = classify_severity(plan.goals.business_overview, "business_overview")
            missing_mandatory.append({
                "section": "Goals",
                "msg": "災害想定が選択されていません",
                "severity": severity
            })
        if not mandatory_checks["ResponseProcedures"]:
            severity = "critical" if not plan.response_procedures else "warning"
            missing_mandatory.append({
                "section": "ResponseProcedures",
                "msg": "初動対応が登録されていません",
                "severity": severity
            })
        if not mandatory_checks["Measures"]:
            severity = "critical" if not plan.measures else "warning"
            missing_mandatory.append({
                "section": "Measures",
                "msg": "事前対策が登録されていません",
                "severity": severity
            })
        if not mandatory_checks["FinancialPlan"]:
            severity = "critical" if not plan.financial_plan.items else "warning"
            missing_mandatory.append({
                "section": "FinancialPlan",
                "msg": "資金計画が登録されていません",
                "severity": severity
            })
        if not mandatory_checks["PDCA"]:
            severity = classify_severity(plan.pdca.training_education, "training_education")
            missing_mandatory.append({
                "section": "PDCA",
                "msg": "PDCA（訓練計画）が未入力です",
                "severity": severity
            })
        
        # Sort by severity: critical first, then warning
        severity_order = {"critical": 0, "warning": 1, "complete": 2}
        missing_mandatory.sort(key=lambda x: severity_order.get(x.get("severity", "complete"), 2))


        # --- 2. Strict Scoring (Total Score) ---
        # Criteria: 100 points = Fully compliant with Electronic Application Manual
        # REVISED LOGIC: Shift focus from check-filling to substantive content (Measures & Finance)
        
        score = 0
        suggestions = []

        # A. Foundation (Max 40 pts) - Directly linked to Mandatory Checks
        # Previous: ~8pts each. New: Basic/PDCA reduced, Measures/Finance increased.
        if mandatory_checks["BasicInfo"]: score += 5
        if mandatory_checks["Goals"]: score += 5
        if mandatory_checks["ResponseProcedures"]: score += 5
        if mandatory_checks["Measures"]: score += 15  # Key Section
        if mandatory_checks["FinancialPlan"]: score += 15 # Key Section
        if mandatory_checks["PDCA"]: score += 5 # Basic Req
        
        # B. Quality & Quantity (Max 30 pts) - NotebookLM Insights + Skasuka Check
        
        # 1. Role in Overview (NotebookLM: Critical)
        ov_text = plan.goals.business_overview or ""
        role_keywords = ["サプライチェーン", "シェア", "地域", "役割", "供給", "責任", "インフラ", "雇用"]
        if any(k in ov_text for k in role_keywords) and len(ov_text) >= 20:
            score += 5
        elif mandatory_checks["Goals"]:
            suggestions.append("「サプライチェーン上の役割（シェア率、供給責任）」や「地域経済における重要性」を具体的に記述してください。")

        # 2. Hazard Map Reference (NotebookLM: Critical)
        dis_text = plan.goals.disaster_scenario.disaster_assumption or ""
        # Also check risk detail text
        all_risk_text = dis_text + " " + str([r.impact_info for r in (plan.goals.disaster_scenario.impact_list or [])])
        hazard_keywords = ["ハザードマップ", "J-SHIS", "浸水", "震度", "マグニチュード", "階級"]
        if any(k in all_risk_text for k in hazard_keywords):
            score += 5
        elif mandatory_checks["Goals"]:
            suggestions.append("被害想定の根拠として「ハザードマップ」や「J-SHIS」の名前を出し、具体的な数値（震度○、浸水○m）を記述してください。")

        # 3. Management Commitment (NotebookLM: Critical)
        pdca_text = str(plan.pdca.management_system) + str(plan.pdca.training_education)
        mgmt_keywords = ["代表", "経営", "社長", "役員", "トップ"]
        if any(k in pdca_text for k in mgmt_keywords):
            score += 5
        elif mandatory_checks["PDCA"]:
            suggestions.append("推進体制に「代表取締役」や「経営層」の関与を明記してください。（例：代表取締役の指揮の下で年1回見直す）")

        # 4. Response Count (Quantity)
        if len(plan.response_procedures) >= 2:
            score += 5
        elif mandatory_checks["ResponseProcedures"]:
            suggestions.append("初動対応は複数（人命安全、被害状況確認など）登録することが望ましいです。")

        # 5. Measures Count (Quantity)
        if len(plan.measures) >= 3:
            score += 5
        elif mandatory_checks["Measures"]:
            suggestions.append(f"事前対策は3件以上（ヒト・モノ・カネ・情報）の登録を強く推奨します。")

        # 6. Financial Detail
        financial_ok = False
        for f in plan.financial_plan.items:
            if f.amount > 0 or (f.method and len(f.method) > 2):
                financial_ok = True
        if financial_ok:
            score += 5
        elif mandatory_checks["FinancialPlan"]:
             suggestions.append("資金計画の内容（金額または調達方法）を具体的に入力してください。")

        # C. Compliance & Checklist (Max 10 pts, Reduced from 20)
        checklist = plan.attachments
        c_score = 0
        if checklist.certification_compliance: c_score += 2
        else: suggestions.append("認定要件への適合チェックが未完了です。")
        
        if checklist.no_false_statements: c_score += 2
        if checklist.not_anti_social: c_score += 2
        if checklist.legal_compliance: c_score += 2
        if checklist.sme_requirements: c_score += 2
        
        score += c_score
        
        # --- Final Adjustments & CAP ---
        # Rule: If critical sections (Measures, FinancialPlan) are missing, score cannot exceed 40.
        critical_missing = False
        if not mandatory_checks["Measures"] or not mandatory_checks["FinancialPlan"]:
            critical_missing = True
        
        total_score = min(100, score)
        
        if critical_missing:
            # Force cap at 40 to indicate "Not Ready"
            total_score = min(total_score, 40)
            if total_score == 40:
                suggestions.append("⚠️ 重要な項目（事前対策または資金計画）が未入力のため、スコアが制限されています。")
        
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
