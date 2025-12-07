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
        self.uploaded_file_refs = [] # アップロードされたファイルの参照保持用
        self.focus_fields = [] # AIが重点的に聞くべき不足項目のリスト
        
        # 基本システムプロンプト
        self.base_system_prompt = """
        あなたは日本の中小企業を支援する「事業継続力強化計画策定支援コンシェルジュ」です。
        ユーザー（経営者・従業員・商工会職員）に対し、以下のガイドラインに従ってインタビューを行い、計画策定を支援してください。

        【最重要指針：資料読み込みファースト】
        ユーザーから資料（PDFや画像）が提供された場合、**絶対に**以下の手順を守ること：
        1. **まず資料を読む**: ユーザーへの質問を開始する前に、アップロードされた資料を隅々まで読み込んでください。
        2. **情報の抽出と確認**: 資料に記載されている情報（企業概要、事業内容、設備、リスク、連絡網など）を抽出してください。
        3. **ユーザーへの提示**: 「いただいた資料から、以下の情報を読み取りました」と提示し、「この内容で登録してよろしいですか？」と確認を求めてください。
        4. **重複質問の禁止**: **資料に書いてあることをユーザーに質問してはいけません。** 資料にない、または読み取れなかった必須項目についてのみ質問してください。

        【基本ガイドライン】
        - 相手のペルソナ（経営者、従業員、商工会職員）に合わせて口調や着眼点を調整してください。
        - 専門用語は避け、分かりやすい言葉で話しかけてください。
        - 一度に複数の質問をせず、一つずつ確認してください。
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
                # model_name を gemini-2.5-flash に固定
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

    def process_files(self, uploaded_files):
        """
        StreamlitのUploadedFileリストを受け取り、Gemini File APIにアップロードし、
        チャットセッションに登録する。
        """
        if not self.model:
            return 0
            
        import tempfile
        import time
        
        count = 0
        new_files = []
        
        for up_file in uploaded_files:
            # MIMEタイプ簡易判定
            mime_type = up_file.type
            if not mime_type:
                # 拡張子から推測（最低限）
                ext = up_file.name.split('.')[-1].lower()
                if ext in ['png', 'jpg', 'jpeg']: mime_type = 'image/jpeg'
                elif ext == 'pdf': mime_type = 'application/pdf'
                else: mime_type = 'application/pdf' # Default

            try:
                # 一時ファイルとして保存
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{up_file.name.split('.')[-1]}") as tmp:
                    tmp.write(up_file.getvalue())
                    tmp_path = tmp.name
                
                # Geminiへアップロード
                g_file = genai.upload_file(path=tmp_path, mime_type=mime_type, display_name=up_file.name)
                
                # Active待ち（Flashは早いが念のため）
                # while g_file.state.name == "PROCESSING":
                #     time.sleep(1)
                #     g_file = genai.get_file(g_file.name)
                
                self.uploaded_file_refs.append(g_file)
                new_files.append(g_file)
                count += 1
                
                # クリーンアップ
                os.unlink(tmp_path)
                
            except Exception as e:
                print(f"File upload failed: {e}")
                st.error(f"Error uploading {up_file.name}: {e}")

        # チャットセッションにファイルを投入
        if new_files:
            # ユーザーには見えないが、モデルには「資料を渡す」アクション
            files_prompt = """
            【システム指示】
            ユーザーから参考資料がアップロードされました。これらを読み込み、事業継続力強化計画（BCP）の各項目（企業基本情報、事業内容、設備、リスク対策など）に該当する情報を抽出してください。
            
            抽出後は、以下のフォーマットでユーザーに確認してください：
            「以下の情報を資料から読み取りました。登録してよろしいですか？
            - 項目名: 値 (出典: 資料名)
            ...」
            """
            try:
                # メッセージとしてファイル参照を送信
                self.chat_session.send_message([files_prompt] + new_files)
                
                # AIの応答（「読み込みました」）を履歴に追加（実際はsend_messageの返答だが今回は擬似的に）
                self.history.append({
                    "role": "model",
                    "content": f"📁 {count}件の資料（{', '.join([f.display_name for f in new_files])}）を受け取りました。\n内容を確認して、分かる部分は入力を省略できるようにしますね。",
                    "persona": "AI Concierge"
                })
            except Exception as e:
                 st.error(f"Error sending files to chat: {e}")

        return count

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

    def merge_history(self, new_history: list):
        """
        新しい履歴データを現在の履歴に統合（マージ）する。
        単純な追記（extend）を行うが、将来的にはタイムスタンプ等によるソートも検討可能。
        """
        # 重複排除ロジックを含めるとなお良いが、まずは単純結合
        # 会話の流れが不自然になるリスクはあるが、Geminiはコンテキストとして処理することを期待
        self.history.extend(new_history)
        
        # Geminiセッションの再構築（履歴が変わったため必須）
        self._rebuild_gemini_session()

    def _rebuild_gemini_session(self):
        """
        現在の self.history に基づいて Gemini のチャットセッションを再構築する
        """
        if not self.model:
            return

        gemini_history = []
        for msg in self.history:
            role = "user" if msg["role"] == "user" else "model"
            # Gemini history format: role must be 'user' or 'model'
            gemini_history.append({
                "role": role,
                "parts": [msg["content"]]
            })
        
        try:
            self.chat_session = self.model.start_chat(history=gemini_history)
        except Exception as e:
            print(f"Failed to rebuild gemini session: {e}")
            # エラー時は空で初期化
            self.chat_session = self.model.start_chat(history=[])

    def load_history(self, history_data: list, merge: bool = False):
        """
        外部から履歴データを読み込む。
        merge=Trueの場合、既存の履歴を保持したまま追加する（マスターチャット化）。
        """
        if merge:
            self.merge_history(history_data)
        else:
            self.history = history_data
            self._rebuild_gemini_session()
