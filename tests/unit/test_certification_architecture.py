"""
Unit tests for certification-driven architecture modules.
"""
import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.core.certification_requirements import RequirementsLoader, requirements_loader


class TestCertificationRequirements(unittest.TestCase):
    
    def test_load_requirements(self):
        """Test that requirements can be loaded from JSON."""
        reqs = requirements_loader.load()
        
        self.assertIsNotNone(reqs)
        self.assertEqual(reqs.version, "1.0.0")
        self.assertIn("disaster_assumption", reqs.sections)
    
    def test_get_section(self):
        """Test getting a specific section."""
        section = requirements_loader.get_section("disaster_assumption")
        
        self.assertIsNotNone(section)
        self.assertEqual(section.name, "自然災害等の想定")
        self.assertEqual(section.scoring_weight, 20)
        self.assertIn("震度", section.required_keywords)
    
    def test_check_keywords_present(self):
        """Test keyword checking with matching text."""
        text = "J-SHISによると震度6弱以上の確率は72.3%です。ハザードマップを参照しました。"
        
        result = requirements_loader.check_keywords("disaster_assumption", text)
        
        self.assertTrue(result["震度"])
        self.assertTrue(result["確率"])
        self.assertTrue(result["J-SHIS"])
        self.assertTrue(result["ハザードマップ"])
    
    def test_check_keywords_missing(self):
        """Test keyword checking with insufficient text."""
        text = "地震が怖いです。"
        
        result = requirements_loader.check_keywords("disaster_assumption", text)
        
        self.assertFalse(result["震度"])
        self.assertFalse(result["確率"])
        self.assertFalse(result["J-SHIS"])
    
    def test_calculate_section_score(self):
        """Test score calculation."""
        # Good text with many keywords
        good_text = "J-SHISによると震度6弱の確率は72%。津波到達は60分。浸水想定2m。ハザードマップ参照。"
        good_score = requirements_loader.calculate_section_score("disaster_assumption", good_text)
        
        # Bad text with few keywords
        bad_text = "地震が怖いです。"
        bad_score = requirements_loader.calculate_section_score("disaster_assumption", bad_text)
        
        self.assertGreater(good_score, bad_score)
        self.assertGreater(good_score, 10)  # Should be high
        self.assertLess(bad_score, 5)  # Should be low
    
    def test_get_disclaimer(self):
        """Test disclaimer retrieval."""
        disclaimer = requirements_loader.get_disclaimer()
        
        self.assertIn("参考値", disclaimer)
        self.assertIn("保証", disclaimer)


class TestAuditAgentStructure(unittest.TestCase):
    """Test audit agent structure without API calls."""
    
    def test_import(self):
        """Test that audit agent can be imported."""
        from src.core.audit_agent import AuditAgent, AuditResult
        
        self.assertIsNotNone(AuditAgent)
        self.assertIsNotNone(AuditResult)
    
    def test_format_application(self):
        """Test application formatting for audit."""
        from src.core.audit_agent import AuditAgent
        from src.api.schemas import ApplicationRoot
        
        plan = ApplicationRoot()
        plan.basic_info.corporate_name = "テスト株式会社"
        plan.goals.business_overview = "テスト事業の概要"
        
        agent = AuditAgent()
        text = agent.format_application_for_audit(plan)
        
        self.assertIn("テスト株式会社", text)
        self.assertIn("テスト事業の概要", text)
        self.assertIn("【基本情報】", text)


class TestManualRAGStructure(unittest.TestCase):
    """Test manual RAG structure without database."""
    
    def test_import(self):
        """Test that manual RAG can be imported."""
        from src.core.manual_rag import ManualRAG, SearchResult
        
        self.assertIsNotNone(ManualRAG)
        self.assertIsNotNone(SearchResult)


if __name__ == "__main__":
    unittest.main()
