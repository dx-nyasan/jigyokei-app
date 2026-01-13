
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

    # --- Task 2: Session Sharing (Phase 1 Implementation) ---
    
    def generate_share_id(self) -> str:
        """
        Generate a unique shareable session ID.
        Uses timestamp + random suffix for uniqueness.
        """
        import hashlib
        import random
        timestamp = str(time.time())
        random_suffix = str(random.randint(1000, 9999))
        raw = f"{timestamp}-{random_suffix}"
        return hashlib.sha256(raw.encode()).hexdigest()[:12]
    
    def create_shareable_session(self, history: list, current_plan_dict: dict) -> str:
        """
        Create a shareable session and return the share ID.
        
        Args:
            history: Chat history
            current_plan_dict: Current plan as dictionary
            
        Returns:
            share_id: Unique session ID for sharing
        """
        share_id = self.generate_share_id()
        self.save_session(history, current_plan_dict, session_id=share_id)
        return share_id
    
    def get_share_url(self, share_id: str, base_url: str = "") -> str:
        """
        Generate a shareable URL for the session.
        
        Args:
            share_id: Session ID from create_shareable_session
            base_url: Base URL of the app (optional)
            
        Returns:
            Full shareable URL with session parameter
        """
        if not base_url:
            # Default for local development
            base_url = "http://localhost:8501"
        
        return f"{base_url}?session={share_id}"
    
    def load_shared_session(self, share_id: str) -> dict:
        """
        Load a shared session by its ID.
        
        Args:
            share_id: Session ID from URL parameter
            
        Returns:
            Session data dict or empty dict if not found
        """
        return self.load_session(session_id=share_id)
    
    def list_shared_sessions(self) -> list:
        """
        List all available shared sessions.
        
        Returns:
            List of session IDs and their metadata
        """
        sessions = []
        for filename in os.listdir(self.storage_dir):
            if filename.startswith("session_") and filename.endswith(".json"):
                session_id = filename[8:-5]  # Remove "session_" and ".json"
                try:
                    with open(os.path.join(self.storage_dir, filename), 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    sessions.append({
                        "id": session_id,
                        "timestamp": data.get("timestamp", 0),
                        "has_plan": data.get("current_plan") is not None
                    })
                except:
                    pass
        return sorted(sessions, key=lambda x: x["timestamp"], reverse=True)

