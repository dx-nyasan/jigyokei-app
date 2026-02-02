import os
import json
from src.core.model_commander import get_commander
import streamlit as st
from typing import List, Dict, Any, Optional
from src.api.schemas import ApplicationRoot

class DataConverter:
    """
    チャット履歴やテキストデータを、Pydanticモデル（構造化データ）に変換するクラス。
    Gemini 1.5 Flash を使用する。
    """
    def __init__(self):
        self.commander = get_commander()

    def convert_chat_to_structured_data(self, chat_history_path: str = None, chat_history_data: List[Dict] = None) -> Dict[str, Any]:
        """
        チャット履歴（リストまたはファイル）を受け取り、ApplicationRootスキーマに合わせたJSONを返す。
        """
        if not self.commander:
            return {}

        # 履歴データの準備
        history_text = ""
        if chat_history_data:
            for msg in chat_history_data:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                history_text += f"{role}: {content}\n"
        elif chat_history_path and os.path.exists(chat_history_path):
            with open(chat_history_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 簡易的な読み込み（形式による）
                history_text = str(data)
        
        if not history_text:
            return {}

        # スキーマ定義の取得
        schema_json = ApplicationRoot.model_json_schema()
        
        # プロンプト作成
        prompt = f"""
        You are an expert data extractor.
        Extract relevant information from the following chat history between a consultant (model) and a business owner (user).
        
        Map the extracted info into a valid JSON object strictly following this schema:
        {json.dumps(schema_json)}
        
        --- Chat History ---
        {history_text}
        --- End History ---
        
        Output ONLY the JSON object.
        """

        try:
            response = self.commander.generate_content("extraction", prompt)
            return json.loads(response.text)
        except Exception as e:
            st.error(f"Data Conversion Failed: {e}")
            return {}

    def get_expert_advice(self, current_data: Dict[str, Any], context: str, section: str) -> str:
        """
        現在の入力内容と専門資料（Context）に基づき、アドバイスを生成する。
        """
        if not self.commander:
            return "API Key missing."

        data_str = json.dumps(current_data, ensure_ascii=False)
        
        prompt = f"""
        あなたは中小企業の事業継続力強化計画策定を支援する専門コンサルタントです。
        以下の「専門資料（Context）」と「ユーザーの現在の入力内容（Current Data）」に基づき、
        {section} セクションについて、より計画を具体化・改善するためのアドバイスを提示してください。
        
        不足している視点や、業界（Contextから推測）特有のリスク対策などを具体的に提案してください。
        
        --- Context (Reference Materials) ---
        {context[:10000]} 
        (truncated if too long)
        
        --- Current Data ({section}) ---
        {data_str}
        
        --- Response ---
        具体的で励みになるアドバイス:
        """
        
        try:
            response = self.commander.generate_content("reasoning", prompt)
            return response.text
        except Exception as e:
            return f"Error generating advice: {e}"
