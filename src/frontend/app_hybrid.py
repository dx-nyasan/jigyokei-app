import streamlit as st
import os

st.set_page_config(page_title="File Structure Diagnostic", layout="wide")
st.title("🕵️ ファイル捜索モード")

# 現在の場所を確認
current_file_path = os.path.abspath(__file__)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))

st.write(f"**現在のファイル位置:** `{current_file_path}`")
st.write(f"**プロジェクトルート（と推測される場所）:** `{project_root}`")

st.divider()

st.subheader("📂 サーバー内の全ファイル一覧")
file_tree = []

# ルートディレクトリから下をすべて探索して表示
for root, dirs, files in os.walk(project_root):
    # .git などの隠しフォルダはスキップ
    if ".git" in root:
        continue
        
    level = root.replace(project_root, '').count(os.sep)
    indent = ' ' * 4 * level
    folder_name = os.path.basename(root)
    if folder_name == "": folder_name = "ROOT (jigyokei-app)"
    
    st.text(f"{indent}📂 {folder_name}/")
    
    subindent = ' ' * 4 * (level + 1)
    for f in files:
        st.text(f"{subindent}📄 {f}")

st.divider()
st.info("この画面に表示されているファイル構成を確認してください。")
