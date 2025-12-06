import sys
import os

# --- パス解決用のおまじない（最優先で実行） ---
# 現在のファイル (src/frontend/app_hybrid.py) の場所から、
# プロジェクトルート (jigyokei-copilot/) を sys.path に追加する
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
# ----------------------------------------------

import streamlit as st
import json
import time
from src.core.ai_interviewer import AIInterviewer
from src.data.context_loader import ContextLoader

# --- Page Config (Must be first) ---
st.set_page_config(
    page_title="Jigyokei Hybrid System",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Version Control for Session State ---
APP_VERSION = "2.6.0-class-rename"

if "app_version" not in st.session_state or st.session_state.app_version != APP_VERSION:
    st.session_state.clear()
    st.session_state.app_version = APP_VERSION
    st.rerun()

# --- Initialize Managers (Singleton-like) ---
if "ai_interviewer" not in st.session_state:
    st.session_state.ai_interviewer = AIInterviewer()
if "context_loader" not in st.session_state:
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    context_dir = os.path.join(root_dir, "data", "context")
    st.session_state.context_loader = ContextLoader(context_dir)

# --- 認証機能 (Simple Password) ---
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

# ==========================================
# Main App Logic
# ==========================================

with st.sidebar:
    st.header("Jigyokei Hybrid System")
    st.caption("Cloud Edition ☁️")
    
    st.divider()
    
    mode = st.radio(
        "Select Mode",
        ["Chat Mode (Pre-Interview)", "Editor Mode (Support Day)"],
        index=0
    )
    
    st.divider()

    st.subheader("Data Management")
    uploaded_file = st.file_uploader("Load Previous Session (JSON)", type=["json"])
    
    # Download Button
    if st.session_state.ai_interviewer.history:
        history_json = json.dumps({"history": st.session_state.ai_interviewer.history}, indent=2, ensure_ascii=False)
        st.download_button(
            label="💾 Download Session (JSON)",
            data=history_json,
            file_name=f"session_{int(time.time())}.json",
            mime="application/json"
        )

    if uploaded_file:
        try:
            uploaded_file.seek(0)
            data = json.load(uploaded_file)
            history = data.get("history", [])
            st.session_state.ai_interviewer.load_history(history)
            st.success(f"Session Loaded! ({len(history)} messages)")
        except Exception as e:
            st.error(f"Failed to load: {e}")

# --- Main Area ---

if mode == "Chat Mode (Pre-Interview)":
    st.title("🤖 AI Interviewer (Chat Mode)")
    st.markdown("事業計画書の作成に必要な情報をヒアリングします。")

    for msg in st.session_state.ai_interviewer.history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("回答や指示を入力してください...")

    if prompt:
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("model"):
            with st.spinner("AI is thinking..."):
                response = st.session_state.ai_interviewer.send_message(prompt)
                st.markdown(response)



elif mode == "Editor Mode (Support Day)":
    st.title("📝 Editor Mode")
    st.info("このモードは現在開発中です。JSONデータの確認などができます。")
    
    st.subheader("Current Context Data")
    # 仮のデータ表示
    st.json(st.session_state.chat_manager.history)
