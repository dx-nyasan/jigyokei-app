import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pytest
from src.api.schemas import ApplicationRoot
from src.core.draft_exporter import DraftExporter
from src.core.completion_checker import CompletionChecker

def test_export_legacy_data():
    """
    Reproduction test for 'tuple object has no attribute category' error.
    """
    # Simulate Level 1 JSON (Legacy)
    data = {
        "basic_info": {
            "corporate_name": "Test Corp",
            "representative_name": "Test Rep"
        },
        "goals": {
            "business_overview": "Overview",
            "disaster_scenario": {
                "disaster_assumption": "Earthquake",
                "impact_list": [{"impact_personnel": "None", "impact_building": "None", "impact_funds": "None", "impact_info": "None"}]
            }
        },
        "response_procedures": [
            {
                "category": "Cat1",
                "action_content": "Act1",
                "timing": "Time1",
                "preparation_content": "Prep1"
            },
            {
                "category": "Cat2",
                "action_content": "Act2",
                "timing": "Time2",
                "preparation_content": "Prep2"
            }
        ],
        "measures": [
             {"category": "人に関する対策", "current_measure": "M1", "future_plan": "F1"},
             {"category": "建物に関する対策", "current_measure": "M2", "future_plan": "F2"}
        ],
        "financial_plan": {
            "items": []
        },
        "pdca": {
            "training_education": "None"
        }
    }
    
    # 1. Migrate
    migrated = ApplicationRoot.migrate_legacy_data(data)
    
    # 2. Validate
    plan = ApplicationRoot.model_validate(migrated)
    
    # Verify response_procedures structure
    assert isinstance(plan.response_procedures, list)
    assert len(plan.response_procedures) == 2
    assert not isinstance(plan.response_procedures[0], tuple)
    assert hasattr(plan.response_procedures[0], 'category')
    
    # 3. Analyze
    result = CompletionChecker.analyze(plan)
    
    # 4. Export (This is where it should crash)
    try:
        excel_bytes = DraftExporter.export_to_excel(plan, result)
        assert excel_bytes is not None
        print("Export successful")
    except AttributeError as e:
        pytest.fail(f"Export failed with AttributeError: {e}")
    except Exception as e:
        pytest.fail(f"Export failed with {type(e)}: {e}")
