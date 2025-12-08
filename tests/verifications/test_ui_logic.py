
import pytest
from src.api.schemas import ApplicationRoot

def test_migrate_legacy_data():
    """Verify that legacy dictionary formats are correctly migrated to the new schema."""
    legacy_data = {
        "basic_info": {"corporate_name": "Test Corp"},
        "measures": [
            {"category": "personnel", "current_measure": "Training", "future_plan": "More Training"}
        ],
        "goals": {
            "disaster_scenario": {
                "impact_list": [
                    {"impact_personnel": "None", "impact_building": "Low"}
                ]
            }
        }
    }
    
    migrated = ApplicationRoot.migrate_legacy_data(legacy_data)
    
    try:
        # Check Measures migration (List -> Dict)
        assert isinstance(migrated["measures"], dict), f"Expected dict, got {type(migrated['measures'])}"
        assert "personnel" in migrated["measures"]
        assert migrated["measures"]["personnel"]["current_measure"] == "Training"
    except AssertionError as e:
        print(f"FAILED: {e}")
        import json
        print(json.dumps(migrated, indent=2, ensure_ascii=False))
        raise
    
    # Check Impacts migration (List -> Object)
    assert "impacts" in migrated["goals"]["disaster_scenario"]
    assert migrated["goals"]["disaster_scenario"]["impacts"]["impact_personnel"] == "None"

def test_dashboard_update_logic():
    """Simulate the dashboard update logic flow."""
    # Simulate extracted data from Chat
    extracted = {
        "basic_info": {"corporate_name": "New Name Corp"},
        "measures": [{"category": "building", "current_measure": "Fix Wall"}] 
        # Note: This is legacy format coming from "extract_structured_data" potentially
    }
    
    # 1. Migrate
    migrated = ApplicationRoot.migrate_legacy_data(extracted)
    
    # 2. Validate
    plan = ApplicationRoot.model_validate(migrated)
    
    assert plan.basic_info.corporate_name == "New Name Corp"
    assert plan.measures.building.current_measure == "Fix Wall"

if __name__ == "__main__":
    test_migrate_legacy_data()
    test_dashboard_update_logic()
    print("All logic tests passed!")
