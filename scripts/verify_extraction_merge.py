import sys
import os
import json
from unittest.mock import MagicMock

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api.schemas import ApplicationRoot, FirstResponse
from src.core.merge_helper import deep_merge_plan

def test_response_procedures_merge():
    print("--- Testing Response Procedures Merge Logic ---")
    
    # 1. Initial State (Missing Preparation Content)
    initial_plan = ApplicationRoot()
    initial_plan.response_procedures = [
        FirstResponse(
            category="人命安全確保",
            action_content="身の安全確保",
            timing="直後",
            preparation_content=None # Missing
        )
    ]
    
    print(f"Before: {initial_plan.response_procedures[0].preparation_content}")
    
    # 2. Extracted Data (From Chat)
    # The AI Agent extracts this from the user's answer about "Evacuation Drills"
    extracted_data = {
        "response_procedures": [
            {
                "category": "人命安全確保",
                "preparation_content": "毎年9月に避難訓練を実施。備蓄品を3日分確保。"
            }
        ]
    }
    
    # 3. Perform Merge
    updated_plan = deep_merge_plan(initial_plan, extracted_data)
    
    # 4. Verify
    after_val = updated_plan.response_procedures[0].preparation_content
    print(f"After: {after_val}")
    
    if after_val == "毎年9月に避難訓練を実施。備蓄品を3日分確保。":
        print("✅ SUCCESS: Preparation Content updated correctly.")
        return True
    else:
        print("❌ FAILURE: Content not updated.")
        return False

if __name__ == "__main__":
    test_response_procedures_merge()
