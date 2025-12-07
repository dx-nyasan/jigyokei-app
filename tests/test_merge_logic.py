import unittest
from unittest.mock import MagicMock
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.jigyokei_core import AIInterviewer

class TestHistoryMerge(unittest.TestCase):
    def setUp(self):
        # Mock API Key injection
        os.environ["GOOGLE_API_KEY"] = "dummy_key"
        self.ai = AIInterviewer()
        # Mock model to avoid actual API calls
        self.ai.model = MagicMock()
        self.ai.model.start_chat.return_value = MagicMock()

    def test_merge_history(self):
        # Initial state
        initial_history = [{"role": "user", "content": "Hello", "persona": "A"}]
        self.ai.load_history(initial_history, merge=False)
        self.assertEqual(len(self.ai.history), 1)

        # New data to merge
        new_data = [{"role": "model", "content": "Hi", "persona": "AI"}]
        
        # Action: Merge
        self.ai.load_history(new_data, merge=True)
        
        # Assert
        self.assertEqual(len(self.ai.history), 2)
        self.assertEqual(self.ai.history[0]["content"], "Hello")
        self.assertEqual(self.ai.history[1]["content"], "Hi")
        print("Done: Merge Test Passed")

    def test_overwrite_history(self):
        # Initial state
        initial_history = [{"role": "user", "content": "Old", "persona": "A"}]
        self.ai.load_history(initial_history, merge=False)
        
        # New data to overwrite
        new_data = [{"role": "user", "content": "New", "persona": "B"}]
        
        # Action: Overwrite
        self.ai.load_history(new_data, merge=False)
        
        # Assert
        self.assertEqual(len(self.ai.history), 1)
        self.assertEqual(self.ai.history[0]["content"], "New")
        print("Done: Overwrite Test Passed")

if __name__ == '__main__':
    unittest.main()
