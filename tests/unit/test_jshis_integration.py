"""
Unit tests for J-SHIS Helper and Auto-Refinement modules.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestJShisHelper:
    """Tests for src/core/jshis_helper.py"""
    
    def test_get_jshis_data_shirahama(self):
        """Test J-SHIS data retrieval for Shirahama"""
        from src.core.jshis_helper import get_jshis_data
        
        address = "和歌山県西牟婁郡白浜町堅田2500番地"
        data = get_jshis_data(address)
        
        assert data is not None
        assert data.prefecture == "和歌山県"
        assert data.probability_30yr_6lower == 65.3
        assert "三角州" in data.terrain_type or "海岸低地" in data.terrain_type
    
    def test_get_jshis_data_unknown_address(self):
        """Test J-SHIS data for unknown address returns None or fallback"""
        from src.core.jshis_helper import get_jshis_data
        
        address = "北海道札幌市中央区1-1"
        data = get_jshis_data(address)
        
        # Should return None for unknown prefecture
        assert data is None
    
    def test_validate_disaster_scenario_pass(self):
        """Test validation with complete disaster scenario"""
        from src.core.jshis_helper import validate_disaster_scenario
        
        text = """当社は和歌山県白浜町にあります。
        今後30年以内に震度6弱以上の地震が起こる確率は65.3%と高く、
        地形区分が三角州であることから揺れやすさも顕著です。
        (J-SHIS地震ハザードカルテ参照)"""
        
        checks = validate_disaster_scenario(text)
        
        assert checks["has_probability"] == True
        assert checks["has_seismic_intensity"] == True
        assert checks["has_jshis_reference"] == True
        assert checks["has_location"] == True
        assert checks["has_terrain"] == True
    
    def test_validate_disaster_scenario_fail(self):
        """Test validation with incomplete disaster scenario"""
        from src.core.jshis_helper import validate_disaster_scenario
        
        text = "地震"  # Case 2 original - should fail
        
        checks = validate_disaster_scenario(text)
        
        assert checks["has_probability"] == False
        assert checks["has_seismic_intensity"] == False
        assert checks["has_jshis_reference"] == False
    
    def test_get_missing_requirements(self):
        """Test missing requirements detection"""
        from src.core.jshis_helper import get_missing_requirements
        
        # Incomplete text
        missing = get_missing_requirements("地震")
        assert len(missing) >= 4  # Should have multiple missing items
        
        # Complete text
        complete_text = """当社は白浜町にあり、震度6弱確率65.3%です。
        地形区分は三角州。(J-SHISハザードカルテ参照)"""
        missing_complete = get_missing_requirements(complete_text)
        assert len(missing_complete) == 0
    
    def test_format_jshis_disaster_text(self):
        """Test formatted text generation"""
        from src.core.jshis_helper import get_jshis_data, format_jshis_disaster_text
        
        data = get_jshis_data("和歌山県西牟婁郡白浜町")
        assert data is not None
        
        text = format_jshis_disaster_text(data, include_tsunami=False)
        
        assert "和歌山県" in text
        assert "65.3" in text
        assert "J-SHIS" in text


class TestAutoRefinement:
    """Tests for src/core/auto_refinement.py"""
    
    def test_refinement_prompts_exist(self):
        """Test that refinement prompts are defined"""
        from src.core.auto_refinement import REFINEMENT_PROMPTS
        
        expected_keys = [
            "disaster_assumption",
            "business_impact",
            "response_procedures",
            "measures",
            "pdca"
        ]
        
        for key in expected_keys:
            assert key in REFINEMENT_PROMPTS
            assert len(REFINEMENT_PROMPTS[key]) > 100  # Should have substantial prompts
    
    def test_refinement_result_model(self):
        """Test RefinementResult model"""
        from src.core.auto_refinement import RefinementResult
        
        result = RefinementResult(
            original_text="test",
            refined_text="improved test",
            improvements_made=["Added detail"],
            confidence_score=85
        )
        
        assert result.original_text == "test"
        assert result.confidence_score == 85


class TestManualRAG:
    """Tests for src/core/manual_rag.py"""
    
    def test_rag_search(self):
        """Test ManualRAG search functionality"""
        from src.core.manual_rag import get_rag
        
        try:
            rag = get_rag()
            results = rag.search("災害想定 地震", top_k=3)
            
            # Should return some results if DB is populated
            assert isinstance(results, list)
            
            if len(results) > 0:
                assert hasattr(results[0], 'text')
                assert hasattr(results[0], 'chunk_id')
        except FileNotFoundError:
            pytest.skip("Vector store not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
