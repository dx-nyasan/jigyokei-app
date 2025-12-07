import unittest
from unittest.mock import MagicMock
import sys
import os

# Filter simulation logic needs to replicate app_hybrid.py logic
class TestFilterLogic(unittest.TestCase):
    def test_filter_logic(self):
        # Mock History
        history = [
            {"role": "user", "content": "Hello CEO", "persona": "経営者"},
            {"role": "model", "content": "Hi CEO", "target_persona": "経営者"}, # Supported
            {"role": "user", "content": "Hello Staff", "persona": "従業員"},
            {"role": "model", "content": "Hi Staff", "target_persona": "従業員"}, # Supported
            {"role": "model", "content": "Old Msg", "persona": "AI Concierge"} # Legacy (no target)
        ]
        
        # Test for "経営者"
        visible_msgs_ceo = []
        current_persona = "経営者"
        for msg in history:
            role = msg["role"]
            msg_persona = msg.get("persona", "Unknown")
            target_persona = msg.get("target_persona")
            visible = False
            if role == "user" and msg_persona == current_persona:
                visible = True
            elif role == "model" and target_persona == current_persona:
                visible = True
            
            if visible:
                visible_msgs_ceo.append(msg["content"])
        
        self.assertIn("Hello CEO", visible_msgs_ceo)
        self.assertIn("Hi CEO", visible_msgs_ceo)
        self.assertNotIn("Hello Staff", visible_msgs_ceo)
        self.assertNotIn("Hi Staff", visible_msgs_ceo)
        self.assertNotIn("Old Msg", visible_msgs_ceo) # Legacy hidden
        
        print("Done: Filter Test Passed")

if __name__ == '__main__':
    unittest.main()
