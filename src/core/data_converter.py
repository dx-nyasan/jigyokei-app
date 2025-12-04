import json
import google.generativeai as genai
import os
import streamlit as st
from src.api.schemas import ApplicationRoot
from typing import Dict, Any

class DataConverter:
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        # Configure API Key from Streamlit secrets or environment variable
        api_key = os.environ.get("GOOGLE_API_KEY")
        if "GOOGLE_API_KEY" in st.secrets:
            api_key = st.secrets["GOOGLE_API_KEY"]
        
        if api_key:
            genai.configure(api_key=api_key)
            
        self.model = genai.GenerativeModel(model_name)

    def convert_chat_to_structured_data(self, chat_history_path: str = None, chat_history_data: List[Dict] = None) -> Dict[str, Any]:
        """
        Reads chat history and converts it into the ApplicationRoot structure.
        Accepts either a file path or direct data.
        """
        if chat_history_data:
            chat_history = chat_history_data
        elif chat_history_path:
            with open(chat_history_path, "r", encoding="utf-8") as f:
                chat_history = json.load(f)
        else:
            return {}

        # Handle different history formats if needed
        # Assuming list of {role: ..., content: ...}
        if isinstance(chat_history, dict) and "history" in chat_history:
             chat_history = chat_history["history"]

        chat_text = "\n".join([f"{msg.get('role', 'unknown')}: {msg.get('content', '')}" for msg in chat_history])
        
        # Get the JSON schema from Pydantic model
        schema = ApplicationRoot.model_json_schema()
        
        prompt = f"""
        You are an expert data analyst. Your task is to extract structured information from the following chat log between a consultant and a business owner.
        
        Target JSON Schema:
        {json.dumps(schema, indent=2, ensure_ascii=False)}
        
        Chat Log:
        {chat_text}
        
        Instructions:
        1. Extract relevant information to fill the JSON schema.
        2. If information is missing, use null or empty strings/lists as appropriate based on the schema.
        3. Do NOT invent information not present in the chat.
        4. Output ONLY the valid JSON object.
        """
        
        response = self.model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            print("Failed to decode JSON from LLM response")
            return {}

    def get_expert_advice(self, current_data: Dict, context_text: str, section: str) -> str:
        """
        Generates expert advice based on current data and provided context (PDFs etc).
        """
        prompt = f"""
        You are a senior business continuity consultant.
        Based on the following reference materials (Context) and the user's current draft (Current Data), provide specific, actionable advice for the '{section}' section.
        
        Context (Guidelines/Expert Knowledge):
        {context_text[:10000]} ... (truncated if too long)
        
        Current Data:
        {json.dumps(current_data, indent=2, ensure_ascii=False)}
        
        Advice:
        """
        
        response = self.model.generate_content(prompt)
        return response.text
