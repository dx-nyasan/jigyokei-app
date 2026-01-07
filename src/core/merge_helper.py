from src.api.schemas import ApplicationRoot, FirstResponse, FinancialPlanItem
from typing import Dict, Any, List

def deep_merge_plan(target_plan: ApplicationRoot, updates: Dict[str, Any]) -> ApplicationRoot:
    """
    Recursively updates the target Pydantic model (ApplicationRoot) with values from the updates dictionary.
    Handles nested objects and specific list merging strategies.
    """
    if not updates:
        return target_plan

    # 1. Basic Info
    if "basic_info" in updates:
        update_model_section(target_plan.basic_info, updates["basic_info"])

    # 2. Goals
    if "goals" in updates:
        update_model_section(target_plan.goals, updates["goals"])

    # 3. Response Procedures (List Logic)
    if "response_procedures" in updates:
        merge_response_procedures(target_plan, updates["response_procedures"])

    # 4. Measures
    if "measures" in updates:
        update_model_section(target_plan.measures, updates["measures"])

    # 5. Financial Plan
    if "financial_plan" in updates:
        merge_financial_plan(target_plan, updates["financial_plan"])

    # 6. PDCA
    if "pdca" in updates:
        update_model_section(target_plan.pdca, updates["pdca"])

    return target_plan

def update_model_section(model_section: Any, data: Dict[str, Any]):
    """Helper to update a Pydantic model fields from a dict."""
    if not model_section or not data:
        return
    
    for key, value in data.items():
        if hasattr(model_section, key):
            # Recursion for nested models?
            # BasicInfo etc are mostly flat or primitive.
            # DisasterScenario is nested in Goals.
            current_val = getattr(model_section, key)
            
            # If current value is a Pydantic model and data is dict, recurse
            if hasattr(current_val, "model_dump") and isinstance(value, dict):
                 update_model_section(current_val, value)
            else:
                 # Simple set
                 # Prevent overwriting with None, empty string, or "未設定"
                 if value is not None and value != "" and value != "未設定":
                     setattr(model_section, key, value)

def merge_response_procedures(plan: ApplicationRoot, new_list: List[Dict[str, Any]]):
    """
    Smart merge for Response Procedures.
    Strategy:
    - Match existing items by 'category'.
    - If match found, update fields (like 'action_content', 'preparation_content').
    - If no match, append.
    """
    if not new_list:
        return

    if plan.response_procedures is None:
        plan.response_procedures = []

    current_list = plan.response_procedures

    for new_item in new_list:
        cat = new_item.get("category")
        matched = False
        
        # Try to find match
        for existing_item in current_list:
            if existing_item.category == cat:
                # MATCH FOUND: Update Fields
                if new_item.get("action_content"):
                    existing_item.action_content = new_item.get("action_content")
                if new_item.get("preparation_content"):
                     existing_item.preparation_content = new_item.get("preparation_content")
                if new_item.get("timing"):
                     existing_item.timing = new_item.get("timing")
                matched = True
                break
        
        if not matched:
            # NO MATCH: Create new
            plan.response_procedures.append(FirstResponse(**new_item))

def merge_financial_plan(plan: ApplicationRoot, financial_data: Dict[str, Any]):
    """
    Handle FinancialPlan merging.
    Specifically 'items' list which contains FinancialPlanItem objects.
    """
    if not financial_data:
        return

    # Update simple fields first
    target_plan = plan.financial_plan
    # Iterate keys to find 'items'
    for key, value in financial_data.items():
        if key == "items" and isinstance(value, list):
            # Special handling for List[FinancialPlanItem]
            # Strategy: Replace or Append?
            # Usually for financial plan, we might want to replace if new list provided,
            # OR append. Given "Correction", let's append if new?
            # Or simplified: Re-construct the list from dicts to Pydantic objects.
            
            # SAFE APPROACH: Convert dicts to FinancialPlanItem and Replace (or Append?)
            # User wants to fill missing items. If AI returns *all* items including new ones, replacement is risky if AI missed some.
            # But usually extraction returns *new* found items.
            # Let's APPEND for safety, unless it's a "Reset".
            
            if target_plan.items is None:
                target_plan.items = []
                
            for f_item_dict in value:
                # Check duplication? (by item name)
                is_dup = False
                for exists in target_plan.items:
                    if exists.item == f_item_dict.get("item"):
                        # Update existing
                        if f_item_dict.get("amount"): exists.amount = f_item_dict.get("amount")
                        if f_item_dict.get("method"): exists.method = f_item_dict.get("method")
                        is_dup = True
                        break
                
                if not is_dup:
                    target_plan.items.append(FinancialPlanItem(**f_item_dict))
                    
        elif hasattr(target_plan, key):
             # Simple field update (safe)
             if value is not None and value != "" and value != "未設定":
                 setattr(target_plan, key, value)
