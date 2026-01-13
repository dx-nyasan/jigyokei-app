from typing import List, Dict, Any
from src.api.schemas import ApplicationRoot
from src.core.logic_validator import check_logic_consistency

# Concrete improvement examples for Task 4 (Expert Audit Implementation)
CONCRETE_EXAMPLES = {
    "PDCA_training_month": {
        "msg": "訓練月が未設定",
        "suggestion": "→ 毎年○月に訓練を実施（例：5月、10月）と記載してください",
        "example": "【他社事例】防災の日(9/1)に合わせて毎年9月に訓練を実施"
    },
    "PDCA_review_month": {
        "msg": "計画見直し月が未設定",
        "suggestion": "→ 年1回の見直し月を設定してください（例：3月、9月）",
        "example": "【他社事例】年度末の3月に前年度の振り返りと改訂を実施"
    },
    "disaster_assumption": {
        "msg": "災害想定が不十分",
        "suggestion": "→ J-SHISやハザードマップを参照し、具体的な数値を記載",
        "example": "【記載例】今後30年以内に震度6弱以上の確率65.3%（J-SHIS参照）"
    },
    "business_overview_short": {
        "msg": "事業概要が短い",
        "suggestion": "→ 200文字以上で、サプライチェーン上の役割を含めて記載",
        "example": "【記載例】当社は○○県で○○を製造し、主要取引先△△社への供給を担う"
    },
    "measures_personnel": {
        "msg": "人員体制の対策が未設定",
        "suggestion": "→ 災害時の連絡体制、代替要員の確保方法を記載",
        "example": "【他社事例】緊急連絡網の整備、従業員の多能工化を推進"
    },
    "measures_money": {
        "msg": "資金確保の対策が未設定",
        "suggestion": "→ 運転資金確保、保険加入状況を記載",
        "example": "【他社事例】災害対応融資枠を確保、火災・地震保険に加入済"
    }
}

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
        
        # Helper to count valid measures
        def count_measures(m) -> int:
            count = 0
            if m.personnel and (m.personnel.current_measure or m.personnel.future_plan): count += 1
            if m.building and (m.building.current_measure or m.building.future_plan): count += 1
            if m.money and (m.money.current_measure or m.money.future_plan): count += 1
            if m.data and (m.data.current_measure or m.data.future_plan): count += 1
            return count

        measures_count = count_measures(plan.measures)

        # --- 1. Mandatory Progress (Start Rate) ---
        # Checks if sections are "touched" or minimal requirements met.
        # Validate Basic Info Detailed
        basic_ok = True
        basic_missing_list = []
        
        if plan.basic_info:
            bi = plan.basic_info
            # Check list: (field_value, field_name_jp)
            checks = [
                (bi.corporate_name, "事業者名"),
                (bi.representative_name, "代表者名"),
                (bi.establishment_date, "設立年月日"),
                (bi.address_zip, "郵便番号"),
                (bi.address_city, "住所（市区町村）"),
                (bi.industry_middle, "業種"),
                (bi.capital, "資本金"),
                (bi.employees, "従業員数")
            ]
            for val, name in checks:
                # Check for empty or "Check Later"
                if not val or str(val).strip() == "" or "後で確認" in str(val) or str(val) == "-":
                    basic_ok = False
                    basic_missing_list.append(f"{name}が未入力（または確認待ち）です")
        else:
            basic_ok = False
            basic_missing_list.append("基本情報が全体的に未入力です")

        mandatory_checks = {
            "BasicInfo": basic_ok,
            "BusinessOverview": bool(plan.goals.business_overview and plan.goals.business_purpose),
            "DisasterScenario": bool(plan.goals.disaster_scenario.disaster_assumption and plan.goals.disaster_scenario.disaster_assumption != "未設定"),
            "ResponseProcedures": bool(len(plan.response_procedures) >= 2), # Stricter: Need multiple items
            "Measures": bool(measures_count >= 2), # Updated: Check count of filled categories
            "FinancialPlan": bool(len(plan.financial_plan.items) > 0),
            "PDCA": bool(
                plan.pdca.training_education and plan.pdca.training_education != "未設定" and
                plan.pdca.training_month and plan.pdca.review_month and
                plan.pdca.internal_publicity and plan.pdca.internal_publicity != "未設定"
            )
        }
        
        mandatory_passed_count = sum(mandatory_checks.values())
        mandatory_total = len(mandatory_checks)
        mandatory_progress = mandatory_passed_count / mandatory_total


        # Helper function for severity classification AND reason
        def analyze_field_quality(value, field_type: str) -> tuple[str, str]:
            """Returns (severity, message)"""
            s_val = str(value).strip() if value else ""
            
            # 1. Critical: Empty
            if not s_val or s_val in ["-", "未設定", "N/A"]:
                return "critical", "未入力（または未設定）です"
            
            # 2. Warning check base on type
            if field_type == "text_description":
                # Too short?
                if len(s_val) < 20: 
                    return "warning", f"記述内容が短すぎます（現在{len(s_val)}文字）。具体的に記述してください。"
                return "complete", ""

            if field_type == "list":
                if len(value) == 0: return "critical", "登録されていません"
                if len(value) < 2: return "warning", "複数項目の登録が推奨されます" # Optional warning
                return "complete", ""

            return "complete", ""

        # Build detailed missing list for UI (WITH SEVERITY)
        missing_mandatory = []
        
        # 1. Basic Info (Granular)
        if not basic_ok:
            for msg in basic_missing_list:
                missing_mandatory.append({
                    "section": "BasicInfo",
                    "msg": msg,
                    "severity": "critical"
                })

        # 2. Business Overview
        # Check Overview specifically
        ov_sev, ov_msg = analyze_field_quality(plan.goals.business_overview, "text_description")
        if ov_sev != "complete":
             missing_mandatory.append({
                "section": "Goals", # Tab 2
                "msg": f"事業活動の概要: {ov_msg}",
                "severity": ov_sev
            })
        
        # Check Purpose specifically
        pur_sev, pur_msg = analyze_field_quality(plan.goals.business_purpose, "text_description")
        if pur_sev != "complete":
             missing_mandatory.append({
                "section": "Goals", # Tab 2
                "msg": f"取組目的: {pur_msg}",
                "severity": pur_sev
            })

        # 3. Disaster Scenario
        if not mandatory_checks["DisasterScenario"]:
            ds_val = plan.goals.disaster_scenario.disaster_assumption
            msg = "災害想定が選択されていません"
            if ds_val == "未設定": msg = "災害想定が「未設定」のままです"
            
            missing_mandatory.append({
                "section": "Disaster", # Tab 3
                "msg": msg,
                "severity": "critical"
            })
        
        # 4. Response Procedures (Modified: Deep Content Check)
        resp_sev, resp_msg = analyze_field_quality(plan.response_procedures, "list")
        if resp_sev != "complete":
            # Override for empty list vs short list
            if len(plan.response_procedures) == 0:
                 missing_mandatory.append({"section": "ResponseProcedures", "msg": "初動対応が登録されていません", "severity": "critical"})
            elif len(plan.response_procedures) < 2:
                 missing_mandatory.append({"section": "ResponseProcedures", "msg": "初動対応は複数（2つ以上）の登録が必要です", "severity": "warning"})
        
        # Check for missing `preparation_content` (User Request)
        if len(plan.response_procedures) > 0:
             missing_prep = False
             for proc in plan.response_procedures:
                 # Check if null, empty, or "not set"
                 if not proc.preparation_content or str(proc.preparation_content).strip() == "" or "未設定" in str(proc.preparation_content):
                     missing_prep = True
                     break
             
             if missing_prep:
                 missing_mandatory.append({
                     "section": "ResponseProcedures", 
                     "msg": "初動対応における「事前対策（preparation_content）」が未入力の項目があります。具体的な準備内容を追記してください。", 
                     "severity": "critical"
                 })

        # 5. Measures & Finance (Existing logic kept but refined)
        if not mandatory_checks["Measures"]:
            msg = "事前対策が登録されていません" if measures_count == 0 else "事前対策の項目が不足しています（2カテゴリ以上推奨）"
            sev = "critical" if measures_count == 0 else "warning"
            missing_mandatory.append({"section": "Measures", "msg": msg, "severity": sev})

        if not mandatory_checks["FinancialPlan"]:
             missing_mandatory.append({"section": "FinancialPlan", "msg": "資金計画が登録されていません", "severity": "critical"})

        if not mandatory_checks["PDCA"]:
             pdca = plan.pdca
             if not pdca.training_education or pdca.training_education == "未設定":
                 missing_mandatory.append({"section": "PDCA", "msg": "訓練・教育の計画が未入力です", "severity": "critical"})
             if not pdca.training_month:
                 missing_mandatory.append({"section": "PDCA", "msg": "教育・訓練の「実施月」が未設定です（12/17改修必須項目）", "severity": "critical"})
             if not pdca.review_month:
                 missing_mandatory.append({"section": "PDCA", "msg": "計画見直しの「実施月」が未設定です（12/17改修必須項目）", "severity": "critical"})
             if not pdca.internal_publicity or pdca.internal_publicity == "未設定":
                 missing_mandatory.append({"section": "PDCA", "msg": "「取組の社内周知」が未入力です（12/17改修必須項目）", "severity": "critical"})
        
        # Sort by severity
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
        if mandatory_checks["BusinessOverview"]: score += 3
        if mandatory_checks["DisasterScenario"]: score += 2
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
        elif mandatory_checks["BusinessOverview"]:
            suggestions.append("「サプライチェーン上の役割（シェア率、供給責任）」や「地域経済における重要性」を具体的に記述してください。")

        # 2. Hazard Map Reference (NotebookLM: Critical)
        dis_text = plan.goals.disaster_scenario.disaster_assumption or ""
        # Also check risk detail text
        # impact_list is GONE. Use impacts object.
        imp_vals = []
        if plan.goals.disaster_scenario.impacts:
             imp = plan.goals.disaster_scenario.impacts
             imp_vals = [imp.impact_personnel, imp.impact_building, imp.impact_funds, imp.impact_info]
        all_risk_text = dis_text + " " + str(imp_vals)
        hazard_keywords = ["ハザードマップ", "J-SHIS", "浸水", "震度", "マグニチュード", "階級"]
        if any(k in all_risk_text for k in hazard_keywords):
            score += 5
        elif mandatory_checks["DisasterScenario"]:
            suggestions.append("被害想定の根拠として「ハザードマップ」や「J-SHIS」の名前を出し、具体的な数値（震度○、浸水○m）を記述してください。")

        # 3. Management Commitment & 12/17 Compliance (NotebookLM: Critical)
        pdca_text = str(plan.pdca.management_system) + str(plan.pdca.training_education) + str(plan.pdca.plan_review)
        mgmt_keywords = ["代表", "経営", "社長", "役員", "トップ"]
        phrasing_ok = "教育及び訓練" in pdca_text or ("教育" in pdca_text and "訓練" in pdca_text)
        
        if any(k in pdca_text for k in mgmt_keywords) and phrasing_ok:
            score += 5
        elif mandatory_checks["PDCA"]:
            if not phrasing_ok:
                suggestions.append("訓練だけでなく「教育及び訓練」と記載し、座学と実技の両面をカバーするようにしてください。")
            else:
                suggestions.append("推進体制に「代表取締役」や「経営層」の関与を明記してください。（例：代表取締役の指揮の下で年1回見直す）")

        # 4. Response Count (Quantity)
        if len(plan.response_procedures) >= 2:
            score += 5
        elif mandatory_checks["ResponseProcedures"]:
            suggestions.append("初動対応は複数（人命安全、被害状況確認など）登録することが望ましいです。")

        # 5. Measures Count (Quantity)
        if measures_count >= 3:
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

        # 7. Disaster-Measures Consistency Check (NEW)
        # Verify that measures address the declared disaster type
        disaster_text = plan.goals.disaster_scenario.disaster_assumption or ""
        disaster_text_lower = disaster_text.lower()
        
        # Define disaster types and expected measure keywords
        disaster_measure_map = {
            "地震": ["耐震", "固定", "倒壊", "落下", "避難", "安否", "備蓄", "緊急地震速報", "転倒防止"],
            "水害": ["浸水", "止水", "排水", "土嚢", "避難", "高所", "防水", "ハザードマップ"],
            "台風": ["強風", "飛散", "防風", "養生", "避難", "停電", "ガラス"],
            "停電": ["発電", "UPS", "バッテリー", "蓄電", "電源", "非常用電源"],
            "感染症": ["感染", "テレワーク", "消毒", "マスク", "リモート", "在宅"]
        }
        
        # Collect all measures text
        measures_text = ""
        if plan.measures:
            m = plan.measures
            measures_text = " ".join([
                m.personnel.current_measure or "", m.personnel.future_plan or "",
                m.building.current_measure or "", m.building.future_plan or "",
                m.money.current_measure or "", m.money.future_plan or "",
                m.data.current_measure or "", m.data.future_plan or ""
            ])
        
        # Check consistency
        consistency_ok = False
        detected_disaster = None
        
        for disaster_type, keywords in disaster_measure_map.items():
            if disaster_type in disaster_text:
                detected_disaster = disaster_type
                # Check if any measure addresses this disaster
                if any(kw in measures_text for kw in keywords):
                    consistency_ok = True
                    score += 5  # Bonus for consistency
                break
        
        if detected_disaster and not consistency_ok and mandatory_checks["Measures"]:
            suggestions.append(f"⚠️ 災害想定「{detected_disaster}」に対応した事前対策が不足しています。{disaster_type}対策のキーワード（例：{', '.join(keywords[:3])}）を含めてください。")


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

        # --- Logic Consistency Check (WS-1 Integration) ---
        logic_result = check_logic_consistency(plan)
        
        # Add logic warnings to missing_mandatory with "info" severity
        for warning in logic_result.get("warnings", []):
            if warning["severity"] in ["warning", "critical"]:
                missing_mandatory.append(warning)
        
        # Add logic suggestions
        suggestions.extend(logic_result.get("suggestions", []))

        return {
            "total_score": total_score,
            "status": status,
            "mandatory_progress": mandatory_progress,
            "recommended_progress": 0.0, # Deprecated/Unused for calculation now
            "missing_mandatory": missing_mandatory,
            "suggestions": suggestions,
            "logic_consistency": logic_result,
            "counts": {
                "measures": measures_count,
                "procedures": len(plan.response_procedures),
                "risks": 1 if plan.goals.disaster_scenario.impacts else 0
            }
        }

