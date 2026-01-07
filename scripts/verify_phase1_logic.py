import sys
import os
import unittest
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api.schemas import ApplicationRoot
from src.core.completion_checker import CompletionChecker

class TestPhase1Logic(unittest.TestCase):
    def test_mandatory_pdca_fields(self):
        """Verify that training_month, review_month, and internal_publicity are checked."""
        plan = ApplicationRoot()
        # Set basic requirements except for the new ones
        plan.pdca.training_education = "訓練を実施"
        
        result = CompletionChecker.analyze(plan)
        
        # Check if missing messages contain new requirements
        missing_msgs = [m['msg'] for m in result['missing_mandatory']]
        self.assertTrue(any("教育・訓練の「実施月」" in msg for msg in missing_msgs))
        self.assertTrue(any("計画見直しの「実施月」" in msg for msg in missing_msgs))
        self.assertTrue(any("「取組の社内周知」" in msg for msg in missing_msgs))
        
        # Now fill them and check again
        plan.pdca.training_month = 1
        plan.pdca.review_month = 1
        plan.pdca.internal_publicity = "周知済み"
        
        result2 = CompletionChecker.analyze(plan)
        missing_msgs2 = [m['msg'] for m in result2['missing_mandatory'] if m['section'] == 'PDCA']
        self.assertEqual(len(missing_msgs2), 0)

    def test_quality_phrasing_points(self):
        """Verify bonus points for '教育及び訓練' phrasing."""
        plan = ApplicationRoot()
        plan.pdca.training_education = "訓練のみ"
        # Set other mandatory fields to enable suggestions
        plan.pdca.training_month = 1
        plan.pdca.review_month = 1
        plan.pdca.internal_publicity = "周知"
        
        res1 = CompletionChecker.analyze(plan)
        
        plan2 = ApplicationRoot()
        plan2.pdca.training_education = "教育及び訓練を実施"
        plan2.pdca.training_month = 1
        plan2.pdca.review_month = 1
        plan2.pdca.internal_publicity = "周知"
        res2 = CompletionChecker.analyze(plan2)
        
        self.assertTrue(any("教育及び訓練" in sug for sug in res1['suggestions']))
        self.assertFalse(any("教育及び訓練" in sug for sug in res2['suggestions']))

if __name__ == "__main__":
    unittest.main()
