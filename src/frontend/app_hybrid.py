import sys
import os

# --- パス解決用のおまじない（最優先で実行） ---
# 現在のファイル (src/frontend/app_hybrid.py) の場所から、
# 2つ上の階層 (jigyokei-app/) をシステムパスに追加して、srcモジュールを認識させる
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
# ---------------------------------------------

import streamlit as st
import json
import time
from src.core.chat_manager import ChatManager
from src.core.data_converter import DataConverter
from src.data.context_loader import ContextLoader
from src.core.document_reminder import DocumentReminder

# --- Configuration ---
# Note: Streamlit Cloud has ephemeral storage. We use st.session_state and File Upload/Download.
CONTEXT_DIR = "data/context"

# --- Authentication ---
def check_password():
    """Returns `True` if the user had the correct password."""
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True

if not check_password():
    st.stop()

# --- Session State ---
if "mode" not in st.session_state:
    st.session_state.mode = "Chat Mode"
if "chat_manager" not in st.session_state:
    st.session_state.chat_manager = ChatManager()
if "form_data" not in st.session_state:
    st.session_state.form_data = {}
if "doc_reminder" not in st.session_state:
    st.session_state.doc_reminder = DocumentReminder()
if "progress" not in st.session_state:
    st.session_state.progress = 0

# --- Sidebar ---
with st.sidebar:
    st.title("Jigyokei Hybrid System")
    st.caption("Cloud Edition ☁️")
    mode = st.radio("Select Mode", ["Chat Mode (Pre-Interview)", "Editor Mode (Support Day)"])
    
    if mode != st.session_state.mode:
        st.session_state.mode = mode
        st.rerun()

    st.divider()
    
    # File Operations (Cloud Friendly)
    st.subheader("Data Management")
    
    # Upload (Resume)
    uploaded_file = st.file_uploader("📂 Load Previous Session (JSON)", type=["json"])
    if uploaded_file is not None:
        try:
            data = json.load(uploaded_file)
            # Restore State
            if "history" in data:
                # Re-init chat manager with history
                st.session_state.chat_manager.history = data["history"]
                # Force re-creation of chat session in manager if needed
                # (ChatManager.load_history logic adapted here)
                # For now, just setting history is enough for display, 
                # but for continuation we might need to re-send context if using API.
                # Our ChatManager.send_message appends to history, so we are good.
                pass
            
            if "pending_docs" in data:
                st.session_state.doc_reminder.pending_documents = set(data["pending_docs"])
            
            if "progress" in data:
                st.session_state.progress = data["progress"]
                
            st.success("Session Loaded Successfully!")
        except Exception as e:
            st.error(f"Error loading file: {e}")

# --- Main Content ---

if st.session_state.mode == "Chat Mode":
    st.header("💬 事前Webインタビュー")
    
    # Progress & Encouragement
    col_prog, col_msg = st.columns([3, 2])
    with col_prog:
        st.progress(st.session_state.progress / 100)
    with col_msg:
        st.caption("🌟 100%にならなくても大丈夫！残りは当日の支援担当者が一緒に埋めます")

    # Display Chat
    for msg in st.session_state.chat_manager.history:
        role = msg.get("role", "model")
        with st.chat_message(role):
            st.markdown(msg.get("content", ""))
            
    # Input Area
    col_input, col_skip = st.columns([4, 1])
    
    with col_input:
        prompt = st.chat_input("回答を入力してください...", key="chat_input")
        
    # Skip Button (Simulated)
    if col_skip.button("スキップ ⏭️"):
        prompt = "SKIP_QUESTION" 

    if prompt:
        # Handle Skip
        if prompt == "SKIP_QUESTION":
            skipped_field = "basic_info" # Mock
            doc_name = st.session_state.doc_reminder.check_reminder(skipped_field)
            
            user_msg = "（スキップしました）"
            with st.chat_message("user"):
                st.markdown(user_msg)
            st.session_state.chat_manager.history.append({"role": "user", "content": user_msg})
            
            if doc_name:
                reminder_msg = st.session_state.doc_reminder.get_reminder_message(doc_name)
                with st.chat_message("model"):
                    st.markdown(reminder_msg)
                st.session_state.chat_manager.history.append({"role": "model", "content": reminder_msg})
            else:
                response = "承知しました。次の質問に進みます。"
                with st.chat_message("model"):
                    st.markdown(response)
                st.session_state.chat_manager.history.append({"role": "model", "content": response})

        else:
            # Normal Chat Flow
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Generate Response
            with st.spinner("Thinking..."):
                response = st.session_state.chat_manager.send_message(prompt)
                st.session_state.progress = min(st.session_state.progress + 10, 100)
            
            with st.chat_message("model"):
                st.markdown(response)
        
        # Rerun to update chat history display properly if needed
        # st.rerun() 

    # Download Button (Handover)
    st.divider()
    
    # Prepare Data for Download
    current_data = {
        "history": st.session_state.chat_manager.history,
        "pending_docs": list(st.session_state.doc_reminder.get_summary_list()), # Convert set to list for JSON serialization
        "progress": st.session_state.progress
    }
    json_str = json.dumps(current_data, indent=2, ensure_ascii=False)
    
    st.download_button(
        label="📥 データを保存 (中断・引継ぎ用)",
        data=json_str,
        file_name="jigyokei_chat_log.json",
        mime="application/json",
        help="このファイルをダウンロードして保存してください。次回『Load Previous Session』から読み込むことで再開できます。"
    )
    
    # Show Bring List
    docs = st.session_state.doc_reminder.get_summary_list()
    if docs:
        with st.expander("🎒 当日の持ち物リスト"):
            for doc in docs:
                st.write(f"- {doc}")


elif st.session_state.mode == "Editor Mode":
    st.header("📝 申請書作成支援エディタ")
    
    # Convert Button (if loaded from chat)
    if st.session_state.chat_manager.history and not st.session_state.form_data:
        if st.button("🔄 チャット履歴からデータを抽出・変換"):
            converter = DataConverter()
            with st.spinner("Converting chat to structured data..."):
                # Pass history directly
                data = converter.convert_chat_to_structured_data(chat_history_data=st.session_state.chat_manager.history)
                st.session_state.form_data = data
            st.success("Conversion Complete!")

    if not st.session_state.form_data:
        st.info("チャット履歴をロードするか、変換を実行してください。")
    else:
        # Basic Info Editor (Simplified)
        st.subheader("1. 基本情報")
        basic_info = st.session_state.form_data.get("basic_info", {})
        if basic_info is None: basic_info = {} # Handle null
        
        col1, col2 = st.columns(2)
        with col1:
            basic_info["corporate_name"] = st.text_input("事業者名", value=basic_info.get("corporate_name", ""))
            basic_info["representative_name"] = st.text_input("代表者名", value=basic_info.get("representative_name", ""))
        with col2:
            basic_info["address_pref"] = st.text_input("都道府県", value=basic_info.get("address_pref", ""))
            basic_info["industry_major"] = st.text_input("業種", value=basic_info.get("industry_major", ""))
            
        # Expert Advice Button
        if st.button("🤖 AIアドバイス (基本情報)"):
            loader = ContextLoader(CONTEXT_DIR)
            context = loader.load_context()
            converter = DataConverter()
            with st.spinner("Analyzing..."):
                advice = converter.get_expert_advice(basic_info, context, "Basic Information")
            st.info(advice)

        st.divider()
        st.subheader("2. 事業継続力強化の目標")
        goals = st.session_state.form_data.get("goals", {})
        if goals is None: goals = {}
        
        goals["business_purpose"] = st.text_area("取り組む目的", value=goals.get("business_purpose", ""), height=150)
        
        if st.button("🤖 AIアドバイス (目標)"):
            loader = ContextLoader(CONTEXT_DIR)
            context = loader.load_context()
            converter = DataConverter()
            with st.spinner("Analyzing..."):
                advice = converter.get_expert_advice(goals, context, "Goals")
            st.info(advice)
            
        st.divider()
        st.json(st.session_state.form_data) # Debug view
