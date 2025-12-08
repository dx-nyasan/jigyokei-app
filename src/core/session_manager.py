
import os
import json
import time
from typing import List, Dict, Any, Optional

class SessionManager:
    """
    Manages local persistence of session data to prevent data loss on page reloads/browser switches.
    Especially important for mobile users where switching apps might kill the websocket connection.
    """
    def __init__(self, storage_dir: str = "userdata"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)
        # In a real multi-user app, this would be user-specific. 
        # For this local/hosted version, we use a single 'latest_session.json' or key-based.
        self.default_file_name = "latest_session.json"
        
    def _get_file_path(self, session_id: str = "default") -> str:
        return os.path.join(self.storage_dir, f"session_{session_id}.json")

    def save_session(self, history: List[Dict], current_plan_dict: Optional[Dict], session_id: str = "default"):
        """
        Save the current chat history and plan data to a JSON file.
        """
        data = {
            "timestamp": time.time(),
            "history": history,
            "current_plan": current_plan_dict
        }
        
        file_path = self._get_file_path(session_id)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            # print(f"DEBUG: Session saved to {file_path}")
        except Exception as e:
            print(f"ERROR: Failed to save session: {e}")

    def load_session(self, session_id: str = "default") -> Dict[str, Any]:
        """
        Load the session data if it exists.
        Returns None or empty dict if not found or error.
        """
        file_path = self._get_file_path(session_id)
        if not os.path.exists(file_path):
            return {}
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"ERROR: Failed to load session: {e}")
            return {}

    def clear_session(self, session_id: str = "default"):
         file_path = self._get_file_path(session_id)
         if os.path.exists(file_path):
             os.remove(file_path)
