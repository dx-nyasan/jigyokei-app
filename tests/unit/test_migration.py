
import pytest
from src.api.schemas import ApplicationRoot

def test_migrate_legacy_json():
    """
    Test that legacy JSON structure (Level 1) is correctly migrated to the new ApplicationRoot schema.
    """
    legacy_data = {
        "basic_info": {
            "applicant_type": "法人",
            "corporate_name": "Test Company",
            "representative_name": "Test Representative",
            "address_pref": "Tokyo"
        },
        "goals": {
            "disaster_scenario": {
                "disaster_type": "Earthquake",
                # Legacy: list of impacts
                "impact_list": [
                    {
                        "impact_personnel": "Injury",
                        "impact_building": "Damage",
                        "impact_funds": "Loss",
                        "impact_info": "Leak"
                    }
                ]
            }
        },
        # Legacy: list of measures
        "measures": [
            {
                "category": "人に関する対策",
                "current_measure": "Evacuation drill",
                "future_plan": "More drills"
            },
            {
                "category": "建物・設備の対策",
                "current_measure": "Fix shelves",
                "future_plan": "Buy new shelves"
            }
        ],
        # Missing new fields like period, applicant_info
    }

    # 1. Run Migration
    migrated_data = ApplicationRoot.migrate_legacy_data(legacy_data)

    # 2. Assertions on Structure
    # Measures should be dict with keys
    assert isinstance(migrated_data["measures"], dict)
    assert "personnel" in migrated_data["measures"]
    assert migrated_data["measures"]["personnel"]["current_measure"] == "Evacuation drill"
    assert "building" in migrated_data["measures"]
    assert migrated_data["measures"]["building"]["current_measure"] == "Fix shelves"
    # Defaults should be filled
    assert "money" in migrated_data["measures"]
    
    # Disaster Scenario should be flattened
    assert "impacts" in migrated_data["goals"]["disaster_scenario"]
    assert migrated_data["goals"]["disaster_scenario"]["impacts"]["impact_personnel"] == "Injury"
    
    # New fields should exist
    assert "applicant_info" in migrated_data
    assert "period" in migrated_data

    # 3. Full Validation (Schema Check)
    # This checks if the migrated data actually fits the Pydantic model
    try:
        model = ApplicationRoot.model_validate(migrated_data)
        assert model.basic_info.corporate_name == "Test Company"
        assert model.measures.personnel.future_plan == "More drills"
    except Exception as e:
        pytest.fail(f"Validation failed after migration: {e}")
