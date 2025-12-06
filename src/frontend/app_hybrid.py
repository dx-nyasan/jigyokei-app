import sys
import os

# --- パス解決 ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
# ----------------

import streamlit as st
import json
import time
from src.core.chat_manager import ChatManager
# 他のimportは一旦無効化（エラー要因排除のため）
# from src.core.data_converter import DataConverter
# from src.data.context_loader import ContextLoader
# from src.core.document_reminder import DocumentReminder

# --- 簡易設定 ---
if "chat_manager" not in st.session_state:
    st.session_state.chat_manager = ChatManager()

# --- 認証機能 ---
def check_password():
    if st.session_state.get("password_correct", False):
        return True
        
    def password_entered():
        if st.session_state["password"] == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    st.text_input("Password", type="password", on_change=password_entered, key="password")
    return False

if not check_password():
    st.stop()

# --- メイン画面 ---
st.title("🛠️ UI Debug Mode")
st.write("現在、チャット入力欄の表示テスト中です。")

# デバッグ表示
st.write("State Check:", "OK")

# チャット履歴の表示
for msg in st.session_state.chat_manager.history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ★★★ ここが表示されるか確認してください ★★★
st.divider()
st.write("👇 この下にチャット入力欄があるはずです")

prompt = st.chat_input("テスト入力：ここに文字が打てますか？")

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 応答生成
    with st.spinner("AI Thinking..."):
        response = st.session_state.chat_manager.send_message(prompt)
        
    with st.chat_message("model"):
        st.markdown(response)
