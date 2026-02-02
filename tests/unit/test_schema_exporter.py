from src.api.schemas import ApplicationRoot, BasicInfo, DisasterScenario, ImpactAssessment, PreDisasterMeasures, MeasureDetail
from src.core.draft_exporter import DraftExporter
import pytest

def test_schema_instantiation():
    """Verify Schema accepts new fields"""
    plan = ApplicationRoot(
        basic_info=BasicInfo(
            corporate_name="Test Corp",
            corporate_name_kana="テストコープ",
            industry_major="Manu",
            representative_name="佐藤 太郎" # Should enforce space?
        ),
        measures=PreDisasterMeasures(
            personnel=MeasureDetail(current_measure="Training"),
            building=MeasureDetail(current_measure="Quake-proof"),
            money=MeasureDetail(current_measure="Insurance"),
            data=MeasureDetail(current_measure="Backup")
        )
    )
    assert plan.basic_info.corporate_name_kana == "テストコープ"
    assert plan.measures.personnel.current_measure == "Training"

def test_exporter_runs():
    """Verify Exporter runs without error"""
    plan = ApplicationRoot(
        basic_info=BasicInfo(
            corporate_name="Test Corp",
            representative_name="John Doe" # No space, validator might fix or leave
        )
    )
    result = {} # Mock result
    
    # Run exporter
    excel_data = DraftExporter.export_to_excel(plan, result)
    assert excel_data is not None
    assert excel_data.getbuffer().nbytes > 0
