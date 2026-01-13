"""
Unit tests for LogicValidator

Tests cross-section consistency checks for architecture alignment.
"""

import pytest
from src.core.logic_validator import LogicValidator, check_logic_consistency
from src.api.schemas import (
    ApplicationRoot, BasicInfo, BusinessStabilityGoal, DisasterScenario,
    FirstResponse, PreDisasterMeasures, MeasureDetail, PDCA
)


@pytest.fixture
def sample_plan():
    """Create a sample plan for testing"""
    return ApplicationRoot(
        basic_info=BasicInfo(
            corporate_name="テスト株式会社",
            representative_name="テスト 太郎",
            industry_major="製造業",
            industry_middle="金属製品製造業"
        ),
        goals=BusinessStabilityGoal(
            business_overview="当社は金属部品の製造・加工を行っています。",
            business_purpose="事業継続力を強化するため",
            disaster_scenario=DisasterScenario(
                disaster_assumption="地震（震度6弱以上の発生確率が高い地域に所在）"
            )
        ),
        response_procedures=[
            FirstResponse(
                category="人命の安全確保",
                action_content="発電機を使用して非常灯を確保する",
                preparation_content=""  # Missing preparation
            )
        ],
        measures=PreDisasterMeasures(
            personnel=MeasureDetail(
                current_measure="従業員の安否確認システムを導入済み",
                future_plan="年1回の避難訓練を実施予定"
            ),
            building=MeasureDetail(
                current_measure="耐震補強工事を実施済み",
                future_plan=""
            )
        ),
        pdca=PDCA(
            training_education="避難訓練の実施",
            training_month=9,
            review_month=12
        )
    )


class TestLogicValidator:
    """Test suite for LogicValidator"""
    
    def test_validator_creation(self):
        """Test that validator can be created"""
        validator = LogicValidator()
        assert validator is not None
    
    def test_validate_returns_dict(self, sample_plan):
        """Test that validate returns expected structure"""
        validator = LogicValidator()
        result = validator.validate(sample_plan)
        
        assert "is_consistent" in result
        assert "warnings" in result
        assert "suggestions" in result
        assert "consistency_score" in result
    
    def test_disaster_measure_consistency_pass(self, sample_plan):
        """Test that matching disaster-measure passes"""
        # sample_plan has 地震 and 耐震 in measures
        validator = LogicValidator()
        result = validator.validate(sample_plan)
        
        # Should not have critical warnings for disaster-measure consistency
        disaster_warnings = [w for w in result["warnings"] 
                            if "災害想定" in w["msg"] and w["severity"] == "critical"]
        assert len(disaster_warnings) == 0
    
    def test_disaster_measure_consistency_warning(self):
        """Test that mismatched disaster-measure generates warning"""
        plan = ApplicationRoot(
            basic_info=BasicInfo(corporate_name="テスト"),
            goals=BusinessStabilityGoal(
                business_overview="テスト事業",
                disaster_scenario=DisasterScenario(
                    disaster_assumption="感染症（新型ウイルス）"  # Infection
                )
            ),
            measures=PreDisasterMeasures(
                personnel=MeasureDetail(
                    current_measure="耐震補強済み"  # Only earthquake measures, no infection measures
                )
            )
        )
        
        validator = LogicValidator()
        result = validator.validate(plan)
        
        # Should have warning about missing infection countermeasures
        infection_warnings = [w for w in result["warnings"] if "感染症" in w["msg"]]
        assert len(infection_warnings) > 0
    
    def test_pdca_consistency(self, sample_plan):
        """Test measures-PDCA consistency check"""
        validator = LogicValidator()
        result = validator.validate(sample_plan)
        
        # sample_plan mentions 訓練 in measures and has PDCA training
        pdca_warnings = [w for w in result["warnings"] if "PDCA" in w["msg"]]
        assert len(pdca_warnings) == 0
    
    def test_response_preparation_warning(self, sample_plan):
        """Test response-preparation consistency check"""
        # sample_plan has response with 発電機 but empty preparation
        validator = LogicValidator()
        result = validator.validate(sample_plan)
        
        response_warnings = [w for w in result["warnings"] if "初動対応" in w["msg"]]
        assert len(response_warnings) > 0
    
    def test_convenience_function(self, sample_plan):
        """Test check_logic_consistency convenience function"""
        result = check_logic_consistency(sample_plan)
        
        assert isinstance(result, dict)
        assert "is_consistent" in result
    
    def test_consistency_score_calculation(self, sample_plan):
        """Test that consistency score is calculated correctly"""
        validator = LogicValidator()
        result = validator.validate(sample_plan)
        
        assert 0 <= result["consistency_score"] <= 100


class TestIndustryOverviewConsistency:
    """Test industry-overview consistency checks"""
    
    def test_manufacturing_overview_match(self):
        """Test that manufacturing industry matches manufacturing overview"""
        plan = ApplicationRoot(
            basic_info=BasicInfo(
                corporate_name="テスト製造",
                industry_middle="金属製品製造業"
            ),
            goals=BusinessStabilityGoal(
                business_overview="当社は金属部品の製造・生産を行っています。"
            )
        )
        
        validator = LogicValidator()
        result = validator.validate(plan)
        
        # Should not have warnings about industry mismatch
        industry_warnings = [w for w in result["warnings"] if "業種" in w["msg"]]
        assert len(industry_warnings) == 0
    
    def test_manufacturing_overview_mismatch(self):
        """Test that manufacturing industry with unrelated overview generates warning"""
        plan = ApplicationRoot(
            basic_info=BasicInfo(
                corporate_name="テスト製造",
                industry_middle="金属製品製造業"
            ),
            goals=BusinessStabilityGoal(
                business_overview="当社はコンサルティングを行っています。"  # Consulting, not manufacturing
            )
        )
        
        validator = LogicValidator()
        result = validator.validate(plan)
        
        # Should have info-level warning about industry mismatch
        industry_warnings = [w for w in result["warnings"] if "業種" in w["msg"]]
        assert len(industry_warnings) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
