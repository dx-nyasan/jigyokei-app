import google.generativeai as genai
import os
import json
import streamlit as st
from typing import List, Dict

class ChatManager:
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        # Configure API Key from Streamlit secrets or environment variable
        api_key = os.environ.get("GOOGLE_API_KEY")
        if "GOOGLE_API_KEY" in st.secrets:
            api_key = st.secrets["GOOGLE_API_KEY"]
        
        if api_key:
            genai.configure(api_key=api_key)
        
        self.model = genai.GenerativeModel(model_name)
        self.chat_session = None
        self.history: List[Dict] = []

    def start_chat(self, system_instruction: str = None):
        """Starts a new chat session."""
        # Note: system_instruction can be passed to GenerativeModel constructor in newer versions,
        # or just handled via the first message.
        self.chat_session = self.model.start_chat(history=[])
        if system_instruction:
            # Send as a user message or system message if supported.
            # For simplicity in this version, we'll just append it to history conceptually
            # or rely on the prompt engineering in the loop.
            pass

    def send_message(self, message: str) -> str:
        """Sends a message to the model and returns the response."""
        if not self.chat_session:
            self.start_chat()
        
        try:
            response = self.chat_session.send_message(message)
            text = response.text
        except Exception as e:
            text = f"Error: {str(e)}"
        
        # Update local history tracking
        self.history.append({"role": "user", "content": message})
        self.history.append({"role": "model", "content": text})
        
        return text

    def save_history(self, filepath: str):
        """Saves the chat history to a JSON file."""
        # In Cloud environment, this might be used for temporary storage or download preparation
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)

    def load_history(self, filepath: str):
        """Loads chat history from a JSON file."""
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                self.history = json.load(f)
            # Re-initialize chat session with history
            # genai history format is slightly different, we might need conversion
            # history=[{'role': 'user', 'parts': ['...']}, ...]
            converted_history = []
            for msg in self.history:
                role = "user" if msg["role"] == "user" else "model"
                converted_history.append({"role": role, "parts": [msg["content"]]})
            
            self.chat_session = self.model.start_chat(history=converted_history)
