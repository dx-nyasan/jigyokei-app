"""
Jigyokei Core Module
Main AI Interviewer class for BCP (Business Continuity Plan) generation.
Migrated to google-genai SDK (2026-01-07)
"""
import os
import json
import re
import tempfile
from google import genai
import streamlit as st


class AIInterviewer:
    """
    Gemini 2.5 Flash を使用したチャット管理クラス。
    履歴の保持とシステムプロンプトの適用を行う。
    (Updated for Phase 3: Analysis Features)
    (Migrated to google-genai SDK)
    """
    def __init__(self):
        self.history = []
        self.uploaded_file_refs = []  # アップロードされたファイルの参照保持用
        self.focus_fields = []  # AIが重点的に聞くべき不足項目のリスト
        self.client = None  # google-genai Client
        self.model_name = 'gemini-2.5-flash'
        self.chat_history = []  # For multi-turn chat (google-genai format)
        
        # 基本システムプロンプト (Updated via NotebookLM)
        self.base_system_prompt = """
# Role Definition
あなたは、中小企業の「事業継続力強化計画」策定支援を行う、親切で優秀なAIコンサルタントです。
あなたの目的は、対話を通じて電子申請に必要な情報をユーザーから引き出し、申請システムへの入力が可能な形式（構造化データ）に整理することです。

# Tone & Style
- **親しみやすさ**: 丁寧語（「です・ます」調）を使用し、温かみのあるコンシェルジュのように接してください。
- **専門性**: 専門用語はなるべく噛み砕き、ユーザーが回答に詰まった際は、業種別の具体例（建設業、製造業、小売業など）を提示して導いてください。
- **励まし**: 計画策定が企業の信頼性向上や強靭化につながることを意識させ、前向きな対話を心がけてください。

# Operational Constraints (重要)
1. **一問一答の原則**: ユーザーへの質問は**一度に1つ**に限定してください。複数の質問をまとめて投げかけてはいけません。
2. **順次進行**: 後述する【Interaction Flow】のセクション順（Step 1 → Step 8）に従って進行してください。
3. **バリデーション（入力検証）**: ユーザーの回答が【Input Rules】に違反している場合、優しく指摘し、正しい形式での再入力を促してください。
4. **ガイドライン連携**: ユーザーが「何をかけばいいか分からない」等の反応を示した場合、【Reference Examples】の内容を参照して助言してください。

# Input Rules (電子申請システムの制約)
- **数値**: 全て「半角数字」で入力させること。（例: 1000）
- **代表者氏名**: 姓と名の間に必ず「全角スペース」を1つ入れること。（例: 経済　太郎）
- **事業所住所**: 登記上の正確な住所を入力させること。
- **必須要件**: 「自然災害（地震、水害等）」の想定は必須。感染症やサイバー攻撃は推奨だが任意。

# Output Rules (Response Format)
- **構造化データ**: ユーザーへの回答の最後（末尾）に、必ず以下のXMLタグで囲んだJSONデータを出力してください。
  ```xml
  <suggestions>
  {
    "options": ["はい", "いいえ", "選択肢A", "選択肢B"], 
    "hints": "回答のヒント（例：製造業の場合は...）",
    "example": "回答例（例：工場内の重要設備として、X号機プレス機があります。）"
  }
  </suggestions>
  ```
- **options**: ユーザーがワンタップで返信できる短い選択肢（最大4つ）。「はい/いいえ」や、具体的な候補（「地震」「水害」など）。
- **hints**: ユーザーが考えやすくするための観点や、業界別の一般的な傾向。
- **example**: 具体的な回答の例文。ユーザーがこれを参考に文章を作れるようにする。

---

# Interaction Flow

以下の手順でヒアリングを行ってください。
**重要**: ユーザーが既に長文や資料で詳細な情報を提供している場合は、機械的に質問を繰り返さず、「情報の確認（Verification）」モードに切り替えて進行してください。

## STEP 1: 基本情報の完全ヒアリング (Basic Info Complete Interview)
1. **必須項目の網羅的確認**: 以下の項目は電子申請で**必須**です。未入力の項目がないよう、順次ヒアリングを行ってください。（一度に全て聞かず、一つずつ丁寧に聞いてください）
   - **事業者名（正式名称）**: まずはこれだけを聞いてください。
   - **フリガナ**: 事業者名の回答があった後に、「そのフリガナをカタカナで」と聞いてください。
   - **法人番号（13桁）**: 分からなければ「後で確認」という選択肢を提示してください。
   - **設立年月日**: 分からなければ「後で確認する」という選択肢を提示してください（optionsに含める）。
   - **住所詳細**: 
     - **郵便番号**: ハイフンあり（641-0054）でもなし（6410054）でも**そのまま受け入れてください**。ユーザーに再入力を求めてはいけません。
     - **住所入力**: 郵便番号を聞いた直後、そこから推測される住所（県・市・町名）を提示し、「番地を入力してください」と促してください。
     - **重要**: この時、JSONの `example` フィールドには「和歌山県和歌山市〇〇町1-1」のように、**推測された住所＋仮の番地** をセットしてください。
   - **代表者情報**: 役職、氏名（姓と名の間に全角スペース）。
   - **業種（大分類・中分類）**: 
     - ユーザーにいきなり「中分類」を聞いてはいけません。
     - まず「どのようなお仕事をされていますか？（例：書道教室、ラーメン屋）」と**具体的な事業内容**を聞いてください。
     - 事業内容を聞き取ったら、あなたが責任を持って日本標準産業分類を特定してください。
   - **資本金又は出資の額**
   - **常時使用する従業員の数**
2. **確認**: 「入力された基本情報（上記）に間違いがないか確認してください。」

## STEP 2: 事業内容の深掘り (Deep Dive into Business)
**重要**: ここは形式的な確認で終わらせず、計画書の下書きとして十分なボリューム（文字数）を確保できるよう、1つずつ深掘りして聞いてください。

## STEP 3: 災害リスクの想定 (Scenarios)
1. **災害種別**: 「御社の事業に最も影響を与える『自然災害』を1つ選んでください（地震、水害など）。」
2. **被害想定**: 「その災害が起きた時、以下の4つの資源にどのような被害が出ると想定されますか？」

## STEP 4: 初動対応 (First Response)
1. **人命安全確保**: 「発災直後、従業員の避難や安否確認はどのように行いますか？」
2. **緊急時体制**: 「誰を本部長として、どのような基準で災害対策本部を立ち上げますか？」
3. **被害状況把握**: 「被害状況をどのように確認し、誰（取引先、自治体等）へ連絡しますか？」

## STEP 5: 対策 (Measures)
※「現在できていること」と「今後の計画」をセットで聞く。

## STEP 6: 推進体制 (Implementation)
1. **平時の体制**: 「計画を推進するために、経営層はどのように関与しますか？」
2. **訓練・見直し**: 「訓練と計画の見直しは、それぞれ年1回以上実施する必要があります。」

## STEP 7: 資金計画・期間 (Finance & Period)

## STEP 8: その他・連絡先 (Contact)

---

# Reference Examples (困ったときの助言集)
"""

        # Extraction System Prompt for Agentic Mode
        self.extraction_system_prompt = """
        あなたは熟練の中小企業診断士兼AIデータアナリストです。
        提供されたテキストや資料から、事業継続力強化計画（BCP）の申請に必要な情報を漏らさず、正確に抽出してください。
        
        【抽出方針】
        - 曖昧な表現は避け、事実に基づいた情報のみを抽出すること。
        - 該当する情報がない場合は、無理に埋めずに null を出力すること。
        - 特に「事業継続力強化の目的」「災害リスク」「初動対応」に関する記述を重点的に探すこと。
        """

        # Streamlit Secrets または 環境変数からAPIキーを取得
        api_key = None
        try:
            api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
        except Exception:
            pass
        
        if not api_key:
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

        if api_key:
            try:
                # google-genai Client initialization
                self.client = genai.Client(api_key=api_key)
            except Exception as e:
                st.error(f"Failed to initialize Gemini client: {e}")
                self.client = None
        else:
            self.client = None
            st.error("Google API Key not found. Please set GEMINI_API_KEY in Streamlit Secrets.")

    def set_focus_fields(self, fields: list):
        """
        AIが重点的に聞くべき項目を設定する。
        ダッシュボードでの解析結果に基づいて呼び出されることを想定。
        """
        self.focus_fields = fields

    def process_files(self, uploaded_files, target_persona: str = None):
        """
        StreamlitのUploadedFileリストを受け取り、Gemini File APIにアップロードし、
        チャットセッションに登録する。
        """
        if not self.client:
            return 0
            
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
                else: mime_type = 'application/pdf'  # Default

            try:
                # 一時ファイルとして保存
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{up_file.name.split('.')[-1]}") as tmp:
                    tmp.write(up_file.getvalue())
                    tmp_path = tmp.name
                
                # google-genai: Use client.files.upload
                g_file = self.client.files.upload(file=tmp_path, config={"mime_type": mime_type, "display_name": up_file.name})
                
                self.uploaded_file_refs.append(g_file)
                new_files.append(g_file)
                count += 1
                
                # クリーンアップ
                os.unlink(tmp_path)
                
            except Exception as e:
                print(f"File upload failed: {e}")
                st.error(f"Error uploading {up_file.name}: {e}")

        # ファイルアップロード完了のお知らせを履歴に追加
        if new_files:
            self.history.append({
                "role": "model",
                "content": f"📁 {count}件の資料を受け取りました。\n内容を確認して、分かる部分は入力を省略できるようにしますね。",
                "persona": "AI Concierge",
                "target_persona": target_persona
            })

        return count

    def send_message(self, user_input: str, persona: str = "経営者", user_data: dict = None) -> str:
        if not self.client:
            return "Error: API Key is missing or model initialization failed."

        # 履歴への追加（アプリ表示用）
        self.history.append({
            "role": "user", 
            "content": user_input,
            "persona": persona,
            "user_data": user_data
        })
        
        # 実際にAPIに送るプロンプトの構築
        actual_prompt = user_input
        
        # Inject User Name context
        if user_data and (user_data.get("name") or user_data.get("position")):
            name = user_data.get("name", "")
            pos = user_data.get("position", "")
            display_str = f"{pos} {name}".strip()
            actual_prompt = f"【発言者情報: {persona} ({display_str})】\n{user_input}"

        # Gap-Fillingのための誘導コンテキストを付与（ユーザーには見えない）
        if self.focus_fields:
            fields_str = ", ".join(self.focus_fields)
            actual_prompt += f"""
            
            [System Instruction for AI]
            現在、以下の項目がまだ入力されていません: {fields_str}
            
            【行動指針：会話の流れを絶対優先】
            1. **ユーザーの話題優先**: ユーザーが独自の話題を話している場合、その話題に徹底的に寄り添ってください。
            2. **自然な移行**: ユーザーの話が一段落したタイミングでのみ、未入力項目について切り出してください。
            3. **強引な誘導の禁止**: 脈絡なく「ところで、〇〇は？」と切り出すことは禁止です。
            """
        
        try:
            # Build contents with chat history for multi-turn
            contents = []
            
            # Add system instruction
            contents.append({
                "role": "user",
                "parts": [{"text": self.base_system_prompt}]
            })
            contents.append({
                "role": "model", 
                "parts": [{"text": "了解しました。事業継続力強化計画の策定支援を開始します。"}]
            })
            
            # Add chat history
            for msg in self.chat_history:
                contents.append(msg)
            
            # Add current user message
            contents.append({
                "role": "user",
                "parts": [{"text": actual_prompt}]
            })
            
            # Send to Gemini using google-genai
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents
            )
            
            text_response = response.text
            
            # Post-processing to remove leaked thought process
            patterns = [
                r"^思考プロセス:.*?(?:\n\n|\Z)",
                r"^Thinking Process:.*?(?:\n\n|\Z)",
                r"【思考プロセス】.*?(?:\n\n|\Z)"
            ]
            for pat in patterns:
                text_response = re.sub(pat, "", text_response, flags=re.DOTALL | re.MULTILINE).strip()
            
            # Update chat history for multi-turn
            self.chat_history.append({
                "role": "user",
                "parts": [{"text": actual_prompt}]
            })
            self.chat_history.append({
                "role": "model",
                "parts": [{"text": text_response}]
            })
            
            self.history.append({
                "role": "model",
                "content": text_response,
                "persona": "AI Concierge",
                "target_persona": persona
            })
            return text_response
            
        except Exception as e:
            error_msg = f"申し訳ありません、エラーが発生しました: {str(e)}"
            self.history.append({
                "role": "model", 
                "content": error_msg,
                "persona": "AI Concierge",
                "target_persona": persona
            })
            return error_msg

    def analyze_history(self) -> dict:
        """
        現在の会話履歴を分析し、JigyokeiPlanスキーマに適合するJSONを生成する。
        """
        if not self.history:
            return {}
        
        if not self.client:
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
                "applicant_type": "法人 or 個人事業主",
                "corporate_name": "企業名",
                "corporate_name_kana": "フリガナ",
                "representative_title": "役職",
                "representative_name": "代表者名",
                "address_zip": "郵便番号",
                "address_pref": "都道府県",
                "address_city": "市区町村",
                "address_street": "番地",
                "address_building": "建物名",
                "capital": 0,
                "employees": 0,
                "establishment_date": "YYYY/MM/DD",
                "industry_major": "大分類",
                "industry_middle": "中分類",
                "industry_minor": "小分類",
                "corporate_number": "法人番号"
            }},
            "goals": {{
                "business_overview": "事業概要",
                "business_purpose": "目的",
                "disaster_scenario": {{
                    "disaster_assumption": "想定災害",
                    "impacts": {{
                        "impact_personnel": "人員への影響",
                        "impact_building": "建物への影響",
                        "impact_funds": "資金への影響",
                        "impact_info": "情報への影響"
                    }}
                }}
            }},
            "response_procedures": [
                {{ "category": "...", "action_content": "...", "timing": "発災直後", "preparation_content": "..." }}
            ],
            "measures": {{
                "personnel": {{ "current_measure": "...", "future_plan": "..." }},
                "building": {{ "current_measure": "...", "future_plan": "..." }},
                "money": {{ "current_measure": "...", "future_plan": "..." }},
                "data": {{ "current_measure": "...", "future_plan": "..." }}
            }},
            "pdca": {{
                "management_system": "...",
                "training_education": "...",
                "plan_review": "..."
            }}
        }}
        """

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            
            text = response.text
            
            # 1. Try finding Markdown Code Block
            json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            
            # 2. Try finding raw JSON structure
            raw_match = re.search(r'(\{.*\})', text, re.DOTALL)
            if raw_match:
                return json.loads(raw_match.group(1))
                
            # 3. Last resort
            return json.loads(text)
            
        except Exception as e:
            print(f"Analysis failed: {e}")
            return {}

    def detect_conflicts(self) -> dict:
        """
        全チャット履歴を分析し、ペルソナ間の意見の不一致や矛盾を抽出する。
        """
        if not self.history:
            return {"conflicts": []}
        
        if not self.client:
            return {"conflicts": []}

        # 履歴をテキスト化
        history_text = ""
        for msg in self.history:
            role = msg["role"]
            content = msg["content"]
            persona = msg.get("persona", "Unknown")
            user_data = msg.get("user_data", {})
            
            sender_info = persona
            if user_data:
                name = user_data.get("name")
                pos = user_data.get("position")
                if name: sender_info += f" ({name})"
                if pos: sender_info += f" [{pos}]"
            
            history_text += f"[{sender_info}]: {content}\n"

        prompt = f"""
        あなたは事業継続力強化計画策定の「矛盾検知・合意形成支援AI」です。
        以下のチャット履歴を分析し、ペルソナ間で「事実認識」や「意見」に食い違いがある点を抽出してください。

        【回答形式】
        以下のJSON形式のみを出力してください。矛盾がない場合は空リストを返してください。
        
        {{
            "conflicts": [
                {{
                    "topic": "矛盾しているトピック",
                    "persona_A": "経営者",
                    "statement_A": "発言内容A",
                    "persona_B": "従業員",
                    "statement_B": "発言内容B",
                    "suggestion": "解決提案"
                }}
            ]
        }}

        【チャット履歴】
        {history_text}
        """

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={"response_mime_type": "application/json"}
            )
            return json.loads(response.text)
        except Exception as e:
            return {"conflicts": []}

    def merge_history(self, new_history: list):
        """
        新しい履歴データを現在の履歴に統合（マージ）する。
        """
        self.history.extend(new_history)
        self._rebuild_chat_history()

    def _rebuild_chat_history(self):
        """
        現在の self.history に基づいて chat_history を再構築する
        """
        self.chat_history = []
        for msg in self.history:
            role = "user" if msg["role"] == "user" else "model"
            self.chat_history.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })

    def load_history(self, history_data: list, merge: bool = False):
        """
        外部から履歴データを読み込む。
        merge=Trueの場合、既存の履歴を保持したまま追加する（マスターチャット化）。
        """
        if merge:
            self.merge_history(history_data)
        else:
            self.history = history_data
            self._rebuild_chat_history()

    def extract_structured_data(self, text: str = "", file_refs: list = None) -> dict:
        """
        Agentic Extraction:
        入力された長文テキストや資料から構造化データを一括抽出する。
        """
        if not self.client:
            return {}
            
        try:
            content_parts = [self.extraction_system_prompt]
            
            if text:
                content_parts.append(f"\n\n# Input Text\n{text}")
            
            if file_refs:
                content_parts.append("\n\n# Input Documents (Already Uploaded)")
                # Note: File handling may need adjustment for new SDK
            
            content_parts.append("\n\n# Output JSON (Strict Schema Match ApplicationRoot)")
            
            full_prompt = "\n".join(content_parts)
            
            response = self.client.models.generate_content(
                model="gemini-1.5-pro",
                contents=full_prompt
            )
            
            # Extract JSON from code block
            match = re.search(r'```json\n(.*?)\n```', response.text, flags=re.DOTALL)
            if match:
                return json.loads(match.group(1))
            else:
                clean_text = response.text.strip()
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]
                return json.loads(clean_text)
                 
        except Exception as e:
            print(f"Extraction Error: {e}")
            return {}
    
    # Compatibility property for old code that checks self.model
    @property
    def model(self):
        """Compatibility property - returns True if client is initialized."""
        return self.client is not None
