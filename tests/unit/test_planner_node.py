"""
TDD Tests for Planner Node and Multi-Section Support (Phase 4)

Tests for expanding LangGraph agent to all 12 certification sections.
Written BEFORE implementation (Red phase).
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPlannerNode:
    """Tests for the Planner node that orchestrates section processing."""
    
    def test_planner_determines_next_section(self):
        """Planner should decide which section to process next."""
        from src.core.langgraph_agent import planner_node
        
        state = {
            "sections_status": {
                "applicant_info": "completed",
                "business_overview": "completed",
                "disaster_assumption": "completed",
                "business_impact": "pending",
                "measures": "pending"
            },
            "current_section": None
        }
        
        result = planner_node(state)
        
        assert "current_section" in result
        # Should pick business_impact (pending and deps satisfied)
        assert result["current_section"] == "business_impact"
    
    def test_planner_respects_dependencies(self):
        """Planner should process sections in dependency order."""
        from src.core.langgraph_agent import planner_node
        
        # disaster_assumption has no dependencies, should be chosen
        # But applicant_info has higher priority and no dependencies
        state = {
            "sections_status": {
                "applicant_info": "completed",
                "business_overview": "completed",
                "disaster_assumption": "pending",
                "measures": "pending"
            },
            "current_section": None
        }
        
        result = planner_node(state)
        
        # Should choose disaster_assumption (next in priority with no blockers)
        assert result["current_section"] == "disaster_assumption"


class TestAllSectionsMapping:
    """Tests for all 12 certification sections."""
    
    ALL_SECTIONS = [
        "disaster_assumption",
        "business_impact", 
        "initial_response",
        "measures",
        "pdca",
        "business_overview",
        "applicant_info",
        "implementation_timeline",
        "resource_allocation",
        "communication_plan",
        "training_plan",
        "review_process"
    ]
    
    def test_section_name_mapping_complete(self):
        """All sections should have Japanese name mappings."""
        from src.core.langgraph_agent import SECTION_NAME_MAP
        
        for section_id in self.ALL_SECTIONS:
            assert section_id in SECTION_NAME_MAP, f"Missing mapping for {section_id}"
    
    def test_writer_supports_all_sections(self):
        """Writer node should handle any section ID."""
        from src.core.langgraph_agent import writer_node
        
        state = {
            "applicant_name": "テスト会社",
            "location": "東京都",
            "raw_interview_text": "テスト内容",
            "current_section": "business_impact",
            "revision_count": 0,
            "critique_list": []
        }
        
        # Should not raise an error
        result = writer_node(state)
        assert "draft_content" in result


class TestSectionDependencies:
    """Tests for section dependency checking."""
    
    def test_get_section_dependencies(self):
        """Should return list of dependent sections."""
        from src.core.langgraph_agent import get_section_dependencies
        
        deps = get_section_dependencies("measures")
        
        assert "disaster_assumption" in deps
    
    def test_check_dependencies_satisfied(self):
        """Should verify all dependencies are completed."""
        from src.core.langgraph_agent import check_dependencies_satisfied
        
        status = {
            "disaster_assumption": "completed",
            "business_impact": "completed",
            "measures": "pending"
        }
        
        assert check_dependencies_satisfied("measures", status) is True
        
        status["disaster_assumption"] = "pending"
        assert check_dependencies_satisfied("measures", status) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
