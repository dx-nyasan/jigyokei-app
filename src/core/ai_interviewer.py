import os
import google.generativeai as genai
import streamlit as st

class ChatManager:
    """
    Gemini 1.5 Flash を使用したチャット管理クラス。
    履歴の保持とシステムプロンプトの適用を行う。
    """
    def __init__(self):
        self.history = []
        
        # システムプロンプト（コンシェルジュの人格定義）
        self.system_prompt = """
        あなたは日本の中小企業を支援する「事業継続力強化計画策定支援コンシェルジュ」です。
        ユーザー（経営者）に対し、以下のガイドラインに従ってインタビューを行ってください。

        1. **一度に一つだけ質問する**: ユーザーが答えやすいよう、複数の質問を同時にしないこと。
        2. **肯定と深掘り**: 回答に対して「それは素晴らしいですね」と肯定しつつ、「具体的にはどのような...？」と深掘りすること。
        3. **専門的アドバイス**: 必要に応じて「建設業の方ですと、このようなリスクも考えられますが...」と気づきを与えること。
        4. **未完成を許容**: ユーザーが「わからない」と言ったら、無理に聞かず「では当日の支援担当者と相談しましょう」と優しくスキップすること。

        まずは、ユーザーの事業内容について優しく尋ねてスタートしてください。
        """

        # Streamlit Secrets または 環境変数からAPIキーを取得
        api_key = None
        try:
            api_key = st.secrets["GOOGLE_API_KEY"]
        except Exception:
            api_key = os.getenv("GOOGLE_API_KEY")

        if api_key:
            genai.configure(api_key=api_key)
            try:
                # system_instruction を正しく使用 (SDK v0.3.5+ supported)
                self.model = genai.GenerativeModel(
                    model_name='gemini-2.5-flash',
                    system_instruction=self.system_prompt
                )
                self.chat_session = self.model.start_chat(history=[])
            except Exception as e:
                st.error(f"Failed to initialize Gemini model: {e}")
                self.model = None
        else:
            self.model = None
            st.error("Google API Key not found. Please set it in Streamlit Secrets.")

    def send_message(self, user_input: str) -> str:
        if not self.model:
            return "Error: API Key is missing or model initialization failed."

        # 履歴への追加
        self.history.append({"role": "user", "content": user_input})
        
        try:
            # 実際のAPIコール
            response = self.chat_session.send_message(user_input)
            text_response = response.text
            
            self.history.append({"role": "model", "content": text_response})
            return text_response
            

            
        except Exception as e:
            error_msg = f"申し訳ありません、エラーが発生しました: {str(e)}"
            self.history.append({"role": "model", "content": error_msg})
            return error_msg
