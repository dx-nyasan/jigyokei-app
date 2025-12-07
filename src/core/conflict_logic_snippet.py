
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
            print(f"Conflict detect error: {e}")
            return {"conflicts": []}
