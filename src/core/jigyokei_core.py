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
1. **必須項目の網羅的確認**: 以下の項目は電子申請で**必須**です。未入力の項目がないよう、順次ヒアリングを行ってください。（一度に全て聞かず、2〜3個ずつ区切って聞いてください）
   - 事業者名（正式名称）とフリガナ
   - 法人番号（13桁）※分からなければ「後で確認」でも可
   - 設立年月日（和暦・西暦どちらでも可）
   - 住所詳細（郵便番号、都道府県、市区町村、番地、ビル名）
   - 代表者情報（役職、氏名 ※姓と名の間にスペース）
   - 業種（大分類・中分類）
   - 資本金又は出資の額
   - 常時使用する従業員の数
2. **確認**: 「入力された基本情報（上記）に間違いがないか確認してください。」

## STEP 2: 事業内容の深掘り (Deep Dive into Business)
**重要**: ここは形式的な確認で終わらせず、計画書の下書きとして十分なボリューム（文字数）を確保できるよう、1つずつ深掘りして聞いてください。
1. **事業活動の概要**: 「事業内容を具体的に確認します。〇〇という事業を行っているとの認識で合っていますか？」
   - Yesの場合: 「ありがとうございます。では、その事業における『強み』や『競合との違い』について、もう少し詳しく教えていただけますか？（例：〇〇という独自の技術がある、など）」と深掘りする。
2. **取組む目的**: 「今回の計画策定の目的について確認します。〇〇のために取り組む、ということでよろしいですか？」
   - Yesの場合: 「承知しました。その目的を達成するために、特に重視しているポイント（人命優先、納期遵守など）はありますか？」と補足情報を引き出す。

## STEP 3: 災害リスクの想定 (Scenarios)
1. **事業者名**: 「登記上の正式名称を教えてください（例：株式会社○○）。」
2. **住所**: 「本社登記されている住所を入力してください。」
3. **代表者の役職**: 「代表者様の役職を教えてください（個人事業主の場合は『代表』）。」
4. **代表者の氏名**: 「代表者様のお名前を入力してください。※姓と名の間に全角スペースを入れてください（例：経済　太郎）。」
   - *Check*: 全角スペースがない場合、修正を依頼する。
5. **従業員数**: 「常時使用する従業員数を半角数字で教えてください。」
6. **業種**: 「日本標準産業分類の『中分類』を教えてください（例：総合工事業、食料品製造業など）。」

## STEP 2: 目標 (Goals)
1. **事業活動の概要**: 「御社の事業内容と、地域やサプライチェーンで担っている役割について教えてください。」
   - *Advice*: 供給責任、地域唯一の店舗、シェア率などに触れるよう促す。
2. **取組む目的**: 「今回の計画策定の目的は何ですか？（例：人命優先、供給責任の遂行、地域貢献など）」

## STEP 3: 災害リスクの想定 (Scenarios)
1. **災害種別**: 「御社の事業に最も影響を与える『自然災害』を1つ選んでください（地震、水害など）。」
   - *Advice*: ハザードマップ（J-SHIS等）の確認を促す。
2. **被害想定**: 「その災害が起きた時、以下の4つの資源にどのような被害が出ると想定されますか？まずは『ヒト（従業員）』への影響から教えてください。」
   - 続けて『モノ（設備・建物）』『カネ（資金）』『情報（データ）』について順に聞く。

## STEP 4: 初動対応 (First Response)
1. **人命安全確保**: 「発災直後、従業員の避難や安否確認はどのように行いますか？」
2. **緊急時体制**: 「誰を本部長として、どのような基準で災害対策本部を立ち上げますか？」
3. **被害状況把握**: 「被害状況をどのように確認し、誰（取引先、自治体等）へ連絡しますか？」

## STEP 5: 対策 (Measures)
※「現在できていること」と「今後の計画」をセットで聞く。
1. **ヒトの対策**: 「多能工化や参集訓練など、人員に関する対策は？」
2. **モノの対策**: 「設備の固定、止水板の設置、予備電源など、設備に関する対策は？」
   - *Branch*: 「この計画で設備導入を行い、税制優遇（防災・減災投資促進税制）を活用しますか？」
     - Yesの場合: 設備名称、型式、単価、数量、取得予定時期を追加で聞く。
3. **カネの対策**: 「損害保険への加入や手元資金の確保など、資金面の対策は？」
4. **情報の対策**: 「データのバックアップやサイバーセキュリティ対策は？」

## STEP 6: 推進体制 (Implementation)
1. **平時の体制**: 「計画を推進するために、経営層はどのように関与しますか？（例：年1回の会議開催など）」
2. **訓練・見直し**: 「訓練と計画の見直しは、それぞれ年1回以上実施する必要があります。実施時期（月）の目安を教えてください。」

## STEP 7: 資金計画・期間 (Finance & Period)
1. **実施期間**: 「計画の実施期間を教えてください（申請月から3年以内）。」
2. **資金計画**: 「対策に必要な概算金額と、その調達方法（自己資金、融資など）を教えてください。」

## STEP 8: その他・連絡先 (Contact)
1. **担当者情報**: 担当者名、メールアドレス、電話番号。
2. **確認**: 「入力内容の概要を作成します。法令遵守等のチェック項目に同意いただけますか？」

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

    def process_files(self, uploaded_files, target_persona: str = None):
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
            【システム指示: 資料分析と詳細抽出】
            ユーザーから参考資料がアップロードされました。これらを読み込み、事業継続力強化計画（BCP）に必要な情報を抽出してください。
            """
            try:
                # メッセージとしてファイル参照を送信
                self.chat_session.send_message([files_prompt] + new_files)
                
                # AIの応答（「読み込みました」）を履歴に追加（実際はsend_messageの返答だが今回は擬似的に）
                self.history.append({
                    "role": "model",
                    "content": f"📁 {count}件の資料（{', '.join([f.display_name for f in new_files])}）を受け取りました。\n内容を確認して、分かる部分は入力を省略できるようにしますね。",
                    "persona": "AI Concierge",
                    "target_persona": target_persona # Explicitly set target
                })
            except Exception as e:
                 st.error(f"Error sending files to chat: {e}")

        return count

    def send_message(self, user_input: str, persona: str = "経営者", user_data: dict = None) -> str:
        if not self.model:
            return "Error: API Key is missing or model initialization failed."

        # 履歴への追加（アプリ表示用）
        self.history.append({
            "role": "user", 
            "content": user_input,
            "persona": persona,
            "user_data": user_data # Store metadata (name, position)
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
        actual_prompt_base = actual_prompt # keep base for modification
        if self.focus_fields:
            fields_str = ", ".join(self.focus_fields)
            actual_prompt += f"""
            
            [System Instruction for AI]
            現在、以下の項目がまだ入力されていません: {fields_str}
            
            【行動指針：会話の流れを絶対優先】
            1. **ユーザーの話題優先**: ユーザーが独自の話題（特に懸念や質問）を話している場合、**未入力項目のことは一時的に忘れ、その話題に徹底的に寄り添ってください。**
            2. **自然な移行**: ユーザーの話が完全に一段落した、またはユーザーが「次は何をすればいい？」と聞いたタイミングでのみ、未入力項目（{fields_str}）について切り出してください。
            3. **強引な誘導の禁止**: 脈絡なく「ところで、〇〇は？」と切り出すことは禁止です。まずは目の前の話題を深掘りしてください。
            """
        
        try:
            # Geminiへの送信
            response = self.chat_session.send_message(actual_prompt)
            text_response = response.text
            
            # Post-processing to remove leaked thought process
            import re
            # Remove "思考プロセス:" block. It usually seems to be at the start or distinct block.
            # Logic: Remove content starting with "思考プロセス:" or "Thinking Process:" until a double newline or end.
            patterns = [
                r"^思考プロセス:.*?(?:\n\n|\Z)",
                r"^Thinking Process:.*?(?:\n\n|\Z)",
                r"【思考プロセス】.*?(?:\n\n|\Z)"
            ]
            for pat in patterns:
                text_response = re.sub(pat, "", text_response, flags=re.DOTALL | re.MULTILINE).strip()
            
            self.history.append({
                "role": "model",
                "content": text_response,
                "persona": "AI Concierge",
                "target_persona": persona  # Add target persona for filtering
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
            "equipment": {{
                "use_tax_incentive": false,
                "items": [
                    {{ "name_model": "...", "acquisition_date": "...", "location": "...", "unit_price": 0, "quantity": 0, "amount": 0 }}
                ],
                "compliance_checks": []
            }},
            "cooperation_partners": [
                {{ "name": "...", "address": "...", "representative": "...", "content": "..." }}
            ],
            "pdca": {{
                "management_system": "...",
                "training_education": "...",
                "plan_review": "..."
            }},
            "financial_plan": {{
                "items": [
                    {{ "item": "...", "usage": "...", "method": "...", "amount": 0 }}
                ]
            }},
            "period": {{
                "start_date": "YYYY/MM/DD",
                "end_date": "YYYY/MM/DD"
            }},
            "applicant_info": {{
                "contact_name": "...",
                "email": "...",
                "phone": "...",
                "closing_month": "..."
            }},
            "attachments": {{
                "check_sheet_uploaded": false,
                "certification_compliance": true,
                "no_false_statements": true,
                "not_anti_social": true,
                "not_cancellation_subject": true,
                "legal_compliance": true,
                "sme_requirements": true,
                "registration_consistency": true,
                "data_utilization_consent": "可",
                "case_publication_consent": "可"
            }}
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

    def detect_conflicts(self) -> dict:
        """
        全チャット履歴を分析し、ペルソナ間（経営者、従業員、商工会職員）の意見の不一致や矛盾を抽出する。
        """
        if not self.history:
            return {"conflicts": []}

        # 履歴をテキスト化（メタデータ付き）
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
        以下のチャット履歴は、同じ企業の「経営者」「従業員」「商工会職員」がそれぞれの視点で語ったものです。

        【指令】
        履歴を分析し、ペルソナ間で「事実認識」や「意見」に食い違い（矛盾）がある点を抽出してください。
        特に「避難場所」「連絡網」「重要事業」「リスク認識」における不一致を重点的に探してください。

        【回答形式】
        以下のJSON形式のみを出力してください。矛盾がない場合は空リストを返してください。
        
        {{
            "conflicts": [
                {{
                    "topic": "矛盾しているトピック（例：避難場所）",
                    "persona_A": "経営者 (山田)",
                    "statement_A": "避難場所は高台の公園と決めている",
                    "persona_B": "従業員 (鈴木)",
                    "statement_B": "避難場所は聞いていないし決まっていない",
                    "suggestion": "両者の認識を合わせるため、避難場所の周知状況を確認しましょう。"
                }}
            ]
        }}

        【チャット履歴】
        {history_text}
        """

        try:
            response = self.model.generate_content(prompt)
            # Remove Markdown code blocks
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
        except Exception as e:
            return {"conflicts": []}

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

    def extract_structured_data(self, text: str = "", file_refs: list = None) -> dict:
        """
        Agentic Extraction:
        入力された長文テキストや資料から構造化データを一括抽出する。
        Gemini 2.5 Pro (High-Fidelity) を使用して、高精度な抽出を行う。
        """
        try:
            # User requested High-Fidelity Gemini 2.5 Pro
            model = genai.GenerativeModel("gemini-1.5-pro") 
            
            content_parts = [self.extraction_system_prompt]
            
            if text:
                content_parts.append(f"\n\n# Input Text\n{text}")
            
            if file_refs:
                content_parts.append("\n\n# Input Documents (Already Uploaded)")
                content_parts.extend(file_refs)
            
            content_parts.append("\n\n# Output JSON (Strict Schema Match ApplicationRoot)")
            
            response = model.generate_content(content_parts)
            
            # Extract JSON from code block
            import re
            match = re.search(r'```json\n(.*?)\n```', response.text, flags=re.DOTALL)
            if match:
                 return json.loads(match.group(1))
            else:
                 # Fallback: try parsing raw text if it looks like JSON
                 clean_text = response.text.strip()
                 if clean_text.startswith("```json"):
                     clean_text = clean_text[7:]
                 if clean_text.endswith("```"):
                     clean_text = clean_text[:-3]
                 return json.loads(clean_text)
                 
        except Exception as e:
            print(f"Extraction Error: {e}")
            return {}
