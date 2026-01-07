"""
Draft Sheet Audit and Scoring Script
Analyzes the extracted data for completeness and certification readiness
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def load_chat_history():
    """Load the chat history from session_default.json"""
    session_path = os.path.join(os.path.dirname(__file__), "userdata", "session_default.json")
    with open(session_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def extract_structured_data(history):
    """Extract the structured data from the last model message"""
    for msg in reversed(history):
        if msg.get("role") == "model" and "<data>" in msg.get("content", ""):
            content = msg["content"]
            start = content.find("<data>") + len("<data>")
            end = content.find("</data>")
            if start > 0 and end > 0:
                json_str = content[start:end].strip()
                return json.loads(json_str)
    return None

def score_completeness(data):
    """Score the completeness of each section"""
    scores = {}
    
    # Basic Info (12 fields)
    basic = data.get("basic_info", {})
    basic_fields = ["company_name", "company_name_furigana", "corporate_number", 
                    "establishment_date", "postal_code", "address",
                    "representative_position", "representative_name",
                    "industry_major_category", "industry_middle_category",
                    "capital_amount", "employee_count"]
    basic_filled = sum(1 for f in basic_fields if basic.get(f))
    scores["basic_info"] = {"filled": basic_filled, "total": len(basic_fields), 
                            "percent": round(basic_filled / len(basic_fields) * 100)}
    
    # Business Overview (2 fields)
    overview = data.get("business_overview", {})
    overview_fields = ["activity_summary", "purpose_of_plan"]
    overview_filled = sum(1 for f in overview_fields if overview.get(f) and len(str(overview.get(f))) > 10)
    scores["business_overview"] = {"filled": overview_filled, "total": len(overview_fields),
                                    "percent": round(overview_filled / len(overview_fields) * 100)}
    
    # Disaster Scenario (5 fields)
    disaster = data.get("disaster_scenario", {})
    disaster_fields = ["disaster_type", "damage_human", "damage_material", "damage_money", "damage_information"]
    disaster_filled = sum(1 for f in disaster_fields if disaster.get(f) and len(str(disaster.get(f))) > 10)
    scores["disaster_scenario"] = {"filled": disaster_filled, "total": len(disaster_fields),
                                    "percent": round(disaster_filled / len(disaster_fields) * 100)}
    
    # Initial Response (3 fields)
    initial = data.get("initial_response", {})
    initial_fields = ["safety_human", "emergency_system", "damage_assessment"]
    initial_filled = sum(1 for f in initial_fields if initial.get(f) and len(str(initial.get(f))) > 20)
    scores["initial_response"] = {"filled": initial_filled, "total": len(initial_fields),
                                   "percent": round(initial_filled / len(initial_fields) * 100)}
    
    # Measures (4 fields)
    measures = data.get("measures", {})
    measures_fields = ["human_measures", "material_measures", "money_measures", "information_measures"]
    measures_filled = sum(1 for f in measures_fields if measures.get(f) and len(str(measures.get(f))) > 20)
    scores["measures"] = {"filled": measures_filled, "total": len(measures_fields),
                          "percent": round(measures_filled / len(measures_fields) * 100)}
    
    # Implementation System (3 fields)
    impl = data.get("implementation_system", {})
    impl_fields = ["normal_time_system", "training_month", "review_month"]
    impl_filled = sum(1 for f in impl_fields if impl.get(f))
    scores["implementation_system"] = {"filled": impl_filled, "total": len(impl_fields),
                                        "percent": round(impl_filled / len(impl_fields) * 100)}
    
    # Finance (3 fields)
    finance = data.get("finance_and_period", {})
    finance_fields = ["implementation_period", "estimated_cost", "funding_method"]
    finance_filled = sum(1 for f in finance_fields if finance.get(f))
    scores["finance"] = {"filled": finance_filled, "total": len(finance_fields),
                         "percent": round(finance_filled / len(finance_fields) * 100)}
    
    # Contact Info (4 fields)
    contact = data.get("contact_info", {})
    contact_fields = ["person_in_charge_name", "person_in_charge_furigana", "email_address", "phone_number"]
    contact_filled = sum(1 for f in contact_fields if contact.get(f))
    scores["contact_info"] = {"filled": contact_filled, "total": len(contact_fields),
                               "percent": round(contact_filled / len(contact_fields) * 100)}
    
    return scores

def audit_content(data):
    """Perform content audit for certification readiness"""
    issues = []
    warnings = []
    suggestions = []
    
    basic = data.get("basic_info", {})
    overview = data.get("business_overview", {})
    disaster = data.get("disaster_scenario", {})
    initial = data.get("initial_response", {})
    measures = data.get("measures", {})
    impl = data.get("implementation_system", {})
    finance = data.get("finance_and_period", {})
    
    # Critical Issues
    if not basic.get("corporate_number") or basic.get("corporate_number") == "1234567890123":
        issues.append("[CRITICAL] Corporate number appears to be placeholder (1234567890123)")
    
    if basic.get("company_name") == "Kabushiki Kaisha XX" or "XX" in str(basic.get("company_name", "")):
        issues.append("[CRITICAL] Company name contains placeholder (XX)")
    
    # Warnings
    activity = overview.get("activity_summary", "")
    if len(activity) < 100:
        warnings.append("[WARNING] Business overview is quite short. Recommended: 200+ characters for certification.")
    
    purpose = overview.get("purpose_of_plan", "")
    if len(purpose) < 50:
        warnings.append("[WARNING] Purpose statement is brief. Consider adding more detail.")
    
    # Check disaster scenario depth
    for field in ["damage_human", "damage_material", "damage_money", "damage_information"]:
        val = disaster.get(field, "")
        if len(val) < 50:
            warnings.append(f"[WARNING] {field} description is short. Add more specific details.")
    
    # Suggestions
    if not measures.get("tax_incentive_utilization"):
        suggestions.append("[SUGGESTION] Consider tax incentive utilization for equipment purchases.")
    
    if not impl.get("training_month"):
        suggestions.append("[SUGGESTION] Specify training month (e.g., September during Disaster Prevention Week).")
    
    if finance.get("estimated_cost") and finance.get("estimated_cost") > 0:
        suggestions.append(f"[INFO] Budget: {finance.get('estimated_cost'):,} yen planned via {finance.get('funding_method', 'N/A')}")
    
    return {"issues": issues, "warnings": warnings, "suggestions": suggestions}

def main():
    print("=" * 70)
    print("Draft Sheet Audit and Scoring Report")
    print("=" * 70)
    
    # Load data
    session_data = load_chat_history()
    history = session_data.get("history", [])
    data = extract_structured_data(history)
    
    if not data:
        print("[ERROR] Could not extract structured data")
        return
    
    company_name = data.get("basic_info", {}).get("company_name", "Unknown")
    print(f"\nCompany: {company_name}")
    print("-" * 70)
    
    # Score completeness
    print("\n## COMPLETENESS SCORES\n")
    scores = score_completeness(data)
    
    total_filled = 0
    total_fields = 0
    
    for section, score in scores.items():
        bar = "#" * (score["percent"] // 5) + "-" * (20 - score["percent"] // 5)
        status = "OK" if score["percent"] == 100 else ("PARTIAL" if score["percent"] > 0 else "MISSING")
        print(f"  {section:25} [{bar}] {score['percent']:3}% ({score['filled']}/{score['total']}) {status}")
        total_filled += score["filled"]
        total_fields += score["total"]
    
    overall = round(total_filled / total_fields * 100)
    print("-" * 70)
    print(f"  OVERALL COMPLETENESS:                           {overall}% ({total_filled}/{total_fields})")
    
    # Audit
    print("\n## AUDIT RESULTS\n")
    audit = audit_content(data)
    
    if audit["issues"]:
        print("  CRITICAL ISSUES:")
        for issue in audit["issues"]:
            print(f"    - {issue}")
    else:
        print("  CRITICAL ISSUES: None")
    
    print()
    if audit["warnings"]:
        print("  WARNINGS:")
        for warning in audit["warnings"]:
            print(f"    - {warning}")
    else:
        print("  WARNINGS: None")
    
    print()
    if audit["suggestions"]:
        print("  SUGGESTIONS:")
        for suggestion in audit["suggestions"]:
            print(f"    - {suggestion}")
    
    # Final grade
    print("\n" + "=" * 70)
    if overall >= 90 and len(audit["issues"]) == 0:
        grade = "A"
        status = "CERTIFICATION READY"
    elif overall >= 75 and len(audit["issues"]) <= 1:
        grade = "B"
        status = "NEARLY READY - Minor fixes needed"
    elif overall >= 50:
        grade = "C"
        status = "NEEDS WORK - Address issues before submission"
    else:
        grade = "D"
        status = "INCOMPLETE - Significant content missing"
    
    print(f"  FINAL GRADE: {grade}")
    print(f"  STATUS: {status}")
    print("=" * 70)

if __name__ == "__main__":
    main()
