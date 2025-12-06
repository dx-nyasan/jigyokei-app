import os

class ContextLoader:
    """
    専門資料（PDF等から抽出したテキスト）を読み込むクラス。
    Streamlit Cloud環境では data/context フォルダを参照する。
    """
    def __init__(self, context_dir: str):
        self.context_dir = context_dir

    def load_context(self) -> str:
        # フォルダが存在しなければ空文字を返す（エラー回避）
        if not os.path.exists(self.context_dir):
            return ""
        
        context_text = ""
        # 指定フォルダ内の .txt または .md ファイルをすべて読み込む
        try:
            for filename in os.listdir(self.context_dir):
                file_path = os.path.join(self.context_dir, filename)
                if os.path.isfile(file_path) and (filename.endswith(".txt") or filename.endswith(".md")):
                    with open(file_path, "r", encoding="utf-8") as f:
                        context_text += f.read() + "\n\n"
        except Exception as e:
            print(f"Error loading context: {e}")
            return ""
            
        return context_text
