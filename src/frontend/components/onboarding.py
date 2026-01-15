"""
Frontend Components: Onboarding Wizard

Task 4: app_hybrid.py Refactoring - Component Extraction
Extracted onboarding wizard logic for better maintainability.
"""

import streamlit as st
import json
from pathlib import Path
from typing import Optional, Dict, Any


def load_industry_templates() -> Optional[Dict[str, Any]]:
    """
    Load industry templates from JSON file.
    
    Returns:
        Templates data dict or None if not found
    """
    try:
        template_path = Path(__file__).parent.parent / "data" / "industry_templates.json"
        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return None


def get_template_options() -> Dict[str, Optional[str]]:
    """Get available industry template options."""
    return {
        "テンプレートなし（空白から開始）": None,
        "🏭 製造業": "manufacturing",
        "🏪 小売業": "retail",
        "💼 サービス業": "service",
        "🏗️ 建設業": "construction",
        "🍽️ 飲食業": "restaurant"
    }


def show_template_preview(templates_data: Dict, template_key: str) -> None:
    """
    Show preview of selected industry template.
    
    Args:
        templates_data: Full templates JSON data
        template_key: Key of selected template (e.g., "manufacturing")
    """
    if not templates_data or not template_key:
        return
    
    template_info = templates_data.get("templates", {}).get(template_key, {})
    if template_info:
        with st.expander("📋 テンプレート内容プレビュー", expanded=False):
            st.caption(f"**災害想定**: {template_info.get('disaster_assumption', '')[:100]}...")
            st.caption(f"**事業概要**: {template_info.get('business_overview', '')[:100]}...")
            
            # Show measures preview
            measures = template_info.get("measures", {})
            if measures:
                st.caption("**事前対策例**:")
                for key, value in list(measures.items())[:2]:
                    st.caption(f"  - {key}: {value[:50]}...")


def apply_template_to_plan(plan, template_key: str) -> None:
    """
    Apply industry template data to current plan.
    
    Args:
        plan: ApplicationRoot plan object
        template_key: Key of selected template
    """
    templates_data = load_industry_templates()
    if not templates_data or not template_key:
        return
    
    template_info = templates_data.get("templates", {}).get(template_key, {})
    if not template_info:
        return
    
    try:
        # Apply disaster assumption
        if template_info.get("disaster_assumption"):
            plan.goals.disaster_scenario.disaster_assumption = template_info["disaster_assumption"]
        
        # Apply business overview
        if template_info.get("business_overview"):
            plan.goals.business_overview = template_info["business_overview"]
        
        # Apply measures
        measures = template_info.get("measures", {})
        if measures.get("personnel"):
            plan.measures.personnel.current_measure = measures["personnel"]
        if measures.get("building"):
            plan.measures.building.current_measure = measures["building"]
        if measures.get("money"):
            plan.measures.money.current_measure = measures["money"]
        if measures.get("data"):
            plan.measures.data.current_measure = measures["data"]
        
        # Apply response procedures
        procedures = template_info.get("response_procedures", [])
        if procedures and hasattr(plan, "response_procedures"):
            from src.api.schemas import ResponseProcedure
            for i, proc_text in enumerate(procedures[:3]):
                if len(plan.response_procedures) <= i:
                    plan.response_procedures.append(ResponseProcedure(content=proc_text))
                else:
                    plan.response_procedures[i].content = proc_text
                    
    except Exception as e:
        st.warning(f"テンプレート適用中にエラー: {e}")


def get_role_nav_target(role: str) -> str:
    """
    Get navigation target based on selected role.
    
    Args:
        role: Selected role string
        
    Returns:
        Navigation target string
    """
    if role == "経営者（事業主）":
        return "経営者インタビュー"
    elif role == "従業員":
        return "従業員インタビュー"
    else:
        return "商工会職員インタビュー"
