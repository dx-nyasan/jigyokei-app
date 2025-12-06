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
from src.core.jigyokei_core import AIInterviewer
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

# ==========================================
# Main App Logic
# ==========================================
    
    st.subheader("Current Context Data")
    # 仮のデータ表示
    st.json(st.session_state.chat_manager.history)
