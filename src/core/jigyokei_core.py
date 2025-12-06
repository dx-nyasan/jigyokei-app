import os
import json
import google.generativeai as genai
import streamlit as st

class AIInterviewer:
    """
    Gemini 2.5 Flash を使用したチャット管理クラス。
    履歴の保持とシステムプロンプトの適用を行う。
    (Updated for Phase 3: Analysis Features)
    """
    def __init__(self):
        self.history = []
        self.focus_fields = [] # AIが重点的に聞くべき不足項目のリスト
        
        # 基本システムプロンプト
        self.base_system_prompt = """
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
                # system_instruction はチャット開始時に設定されるため、動的変更が難しい。
                # そのため、send_messageごとのメッセージにinstructionを埋め込むか、
                # context cachingを使うのが一般的だが、ここではシンプルに
                # model初期化時の system_instruction は固定し、
                # 毎回の入力に System Instruction的なものを付与する方式、
                # あるいは会話履歴としてSystem Instructionを扱う方式をとる。
                # Gemini SDKの chat.send_message は system_instruction を上書きできないので、
                # ここでは初期化時にベースを設定し、不足項目に対する誘導は user prompt に hidden context として付与する。
                
                self.model = genai.GenerativeModel(
                    model_name='gemini-2.5-flash',
                    system_instruction=self.base_system_prompt
                )
                self.chat_session = self.model.start_chat(history=[])
            except Exception as e:
                st.error(f"Failed to initialize Gemini model: {e}")
                self.model = None
        else:
            self.model = None
            st.error("Google API Key not found. Please set it in Streamlit Secrets.")

    def set_focus_fields(self, fields: list):
        """
        AIが重点的に聞くべき項目を設定する。
        ダッシュボードでの解析結果に基づいて呼び出されることを想定。
        """
        self.focus_fields = fields

    def send_message(self, user_input: str, persona: str = "経営者") -> str:
        if not self.model:
            return "Error: API Key is missing or model initialization failed."

        # 履歴への追加（アプリ表示用）
        self.history.append({
            "role": "user", 
            "content": user_input,
            "persona": persona
        })
        
        # 実際にAPIに送るプロンプトの構築
        # Gap-Fillingのための誘導コンテキストを付与（ユーザーには見えない）
        actual_prompt = user_input
        if self.focus_fields:
            fields_str = ", ".join(self.focus_fields)
            actual_prompt += f"""
            
            [System Instruction for AI]
            現在、以下の項目がまだ入力されていません: {fields_str}
            
            【行動指針】
            1. **文脈優先**: ユーザーの直前の発言が、上記の未入力項目（例：住所）に関連する場合、**その項目そのもの**について質問してください。（例：「住所はまだ登録されていません。ご住所を教えていただけますか？」）
            2. **自然な誘導**: 文脈に関連がない場合のみ、上記リストから最も重要と思われるものを1つ選び、自然に話題を振ってください。
            3. **唐突さの回避**: 機械的にリストを消化するのではなく、会話の流れを維持してください。
            """
        
        try:
            # Geminiへの送信
            response = self.chat_session.send_message(actual_prompt)
            text_response = response.text
            
            self.history.append({
                "role": "model",
                "content": text_response,
                "persona": "AI Concierge"
            })
            return text_response
            
        except Exception as e:
            error_msg = f"申し訳ありません、エラーが発生しました: {str(e)}"
            self.history.append({"role": "model", "content": error_msg})
            return error_msg

    def analyze_history(self) -> dict:
        """
        現在の会話履歴を分析し、JigyokeiPlanスキーマに適合するJSONを生成する。
        """
        if not self.history:
            return {}

        # 履歴をテキスト化
        history_text = ""
        for msg in self.history:
            role = msg["role"]
            content = msg["content"]
            persona = msg.get("persona", "")
            history_text += f"[{role} ({persona})]: {content}\n"

        prompt = f"""
        あなたは事業継続力強化計画の策定支援AIです。
        以下の会話履歴から、事業計画書の作成に必要な情報を抽出し、JSON形式で出力してください。
        
        【抽出ルール】
        1. 以下のJSONスキーマに従うこと。
        2. 情報がない項目は null または "未設定" とする。
        3. 推測はせず、会話に出てきた事実のみを抽出すること。

        【会話履歴】
        {history_text}

        【出力スキーマ】
        {{
            "basic_info": {{
                "company_name": "企業名",
                "representative_name": "代表者名",
                "address": "住所",
                "phone_number": "電話番号",
                "business_type": "業種"
            }},
            "business_content": {{
                "target_customers": "誰に",
                "products_services": "何を",
                "delivery_methods": "どのように",
                "core_competence": "強み"
            }},
            "disaster_risks": [
                {{ "risk_type": "災害の種類", "impact_description": "影響" }}
            ],
            "pre_disaster_measures": [
                {{ "item": "対策項目", "content": "内容", "in_charge": "担当", "deadline": "時期" }}
            ],
            "post_disaster_measures": [
                {{ "item": "対応項目", "content": "内容", "in_charge": "担当", "deadline": "時期" }}
            ]
        }}
        """

        try:
            response = self.model.generate_content(prompt)
            text = response.text
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            else:
                return json.loads(text)
        except Exception as e:
            print(f"Analysis failed: {e}")
            return {}

    def load_history(self, history_data: list):
        """
        外部から履歴データを読み込み、内部状態とGeminiのセッションを復元する。
        """
        self.history = history_data
        
        if self.model:
            gemini_history = []
            for msg in history_data:
                role = "user" if msg["role"] == "user" else "model"
                gemini_history.append({
                    "role": role,
                    "parts": [msg["content"]]
                })
            
            try:
                self.chat_session = self.model.start_chat(history=gemini_history)
            except Exception as e:
                print(f"Failed to restore gemini session: {e}")
                self.chat_session = self.model.start_chat(history=[])
