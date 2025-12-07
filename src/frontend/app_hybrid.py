import sys
import os
import streamlit as st
import json
import time
import importlib

# --- Page Config (Must be the first Streamlit command) ---
st.set_page_config(
    page_title="Jigyokei Hybrid System",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Path Setup ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# --- Module Reloading for Streamlit Cloud ---
import src.core.jigyokei_core
import src.core.jigyokei_schema
importlib.reload(src.core.jigyokei_core)
importlib.reload(src.core.jigyokei_schema)

from src.core.jigyokei_core import AIInterviewer
from src.data.context_loader import ContextLoader

# --- Version Control ---
APP_VERSION = "3.3.1-multimodal-fix"

if "app_version" not in st.session_state or st.session_state.app_version != APP_VERSION:
    st.session_state.clear()
    st.session_state.app_version = APP_VERSION
    st.rerun()

# --- Initialize Managers ---
if "ai_interviewer" not in st.session_state:
    st.session_state.ai_interviewer = AIInterviewer()
else:
    # Check for outdated instance (missing 'analyze_history')
    # クラス定義がリロードされても、セッション内のインスタンスは古いままなので、ここで検知して再生成する
    if not hasattr(st.session_state.ai_interviewer, "analyze_history"):
        st.warning("🔄 Upgrading AI Brain to latest version...")
        
        # Preserve old history
        old_history = getattr(st.session_state.ai_interviewer, "history", [])
        
        # Re-initialize with new class definition
        st.session_state.ai_interviewer = AIInterviewer()
        
        # Restore history
        # 新しいクラスのload_historyを使うか、直接代入するか。
        # ここでは安全に直接代入しつつ、Geminiセッション再構築はload_historyに任せるのがベストだが、
        # 簡易的にload_historyを呼ぶ。
        if hasattr(st.session_state.ai_interviewer, "load_history"):
             st.session_state.ai_interviewer.load_history(old_history)
        else:
             st.session_state.ai_interviewer.history = old_history
             
        st.success("✅ AI Brain Upgraded! Please reload one last time.")
        time.sleep(1)
        st.rerun()

if "context_loader" not in st.session_state:
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    context_dir = os.path.join(root_dir, "data", "context")
    st.session_state.context_loader = ContextLoader(context_dir)

# --- Authentication ---
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

# State Transition Helper
def change_mode(mode_name, persona_name=None):
    st.session_state.app_mode_selection = mode_name
    if persona_name:
        st.session_state.app_persona_selection = persona_name

with st.sidebar:
    st.header("Jigyokei Hybrid System")
    st.caption("Cloud Edition ☁️")
    st.text(f"Ver: {APP_VERSION}") # バージョンを常に表示

    st.divider()
    
    # Mode Selection
    # Mode Selection
    if "app_mode_selection" not in st.session_state:
        st.session_state.app_mode_selection = "Chat Mode (Interview)"

    mode = st.radio(
        "Select Mode",
        ["Chat Mode (Interview)", "Dashboard Mode (Progress)"],
        index=0,
        key="app_mode_selection"
    )
    
    st.divider()

    # Persona Selection
    if mode == "Chat Mode (Interview)":
        st.subheader("Who are you?")
        # Initialize key if needed
        if "app_persona_selection" not in st.session_state:
            st.session_state.app_persona_selection = "経営者"
            
        persona = st.radio(
            "Select Persona",
            ["経営者", "従業員", "商工会職員"],
            index=0,
            key="app_persona_selection"
        )
    else:
        persona = "Viewer"

    # Recommended Documents based on Persona
    # (Moved to Main Area Landing Page)
    
    # File Uploader
    # (Moved to Main Area Landing Page)

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
        # Prevent infinite rerun loop by checking file ID
        file_id = f"{uploaded_file.name}_{uploaded_file.size}"
        
        if st.session_state.get("last_loaded_file_id") != file_id:
            try:
                uploaded_file.seek(0)
                data = json.load(uploaded_file)
                history = data.get("history", [])
                
                # Merge Mode: Add to existing history instead of overwriting
                st.session_state.ai_interviewer.load_history(history, merge=True)
                
                # Save state to prevent reload
                st.session_state.last_loaded_file_id = file_id
                
                st.success(f"Session Merged! ({len(history)} messages added)")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Failed to load: {e}")

# --- Main Area ---


if mode == "Chat Mode (Interview)":
    # 1. Dashboard Navigation & Header
    col_head1, col_head2 = st.columns([3, 1])
    with col_head1:
        st.title("🤖 AI Interviewer (Chat Mode)")
    with col_head2:
        st.button(
            "📊 Go to Dashboard",
            on_click=change_mode,
            args=("Dashboard Mode (Progress)",)
        )

    # 2. Document Upload Area (Always Available)
    with st.expander("📂 資料の追加アップロード (Upload Documents)", expanded=not st.session_state.ai_interviewer.history):
        # Persona-specific Guidance
        upload_label = "資料をアップロード (PDF/画像)"
        if persona == "経営者":
            st.info("🏢 **経営者の方へ**: 会社案内、事業計画書、ハザードマップなど")
            upload_label = "🏢 経営者用資料をアップロード"
        elif persona == "従業員":
            st.info("👷 **従業員の方へ**: 業務マニュアル、緊急連絡網、現場写真など")
            upload_label = "👷 現場・業務資料をアップロード"
        elif persona == "商工会職員":
            st.info("🧑‍🏫 **商工会職員の方へ**: 共済パンフレット、地域防災計画など")
            upload_label = "🧑‍🏫 支援・制度資料をアップロード"
        
        uploaded_refs = st.file_uploader(
            upload_label, 
            type=["pdf", "png", "jpg", "jpeg"], 
            accept_multiple_files=True,
            key=f"uploader_{persona}_{int(time.time())}" # Add timestamp to reset key slightly if needed
        )
        
        if uploaded_refs and st.button("🚀 資料を読み込む (Process Files)"):
             with st.spinner("資料を解析中..."):
                try:
                    count = st.session_state.ai_interviewer.process_files(uploaded_refs)
                    st.success(f"{count}件の資料を読み込みました！")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"読み込みエラー: {e}")

    # 3. Chat Interface
    st.divider()
    
    # History Display
    if not st.session_state.ai_interviewer.history:
        st.markdown(
            "👋 **こんにちは。事業継続力強化計画の策定を支援します。**\n\n"
            "まずは上の「資料アップロード」から資料を読み込ませるか、"
            "下の入力欄から会話を始めてください。"
        )
    
    for msg in st.session_state.ai_interviewer.history:
        role = msg["role"]
        msg_persona = msg.get("persona", "Unknown")
        target_persona = msg.get("target_persona")
        
        # Filtering Logic: Only show relevant messages for current persona
        visible = False
        if role == "user" and msg_persona == persona:
            visible = True
        elif role == "model" and target_persona == persona:
            visible = True
        
        if visible:
            avatar = "🤖" if role == "model" else "👤"
            if msg_persona == "経営者": avatar = "👨‍💼"
            elif msg_persona == "従業員": avatar = "👷"
            elif msg_persona == "商工会職員": avatar = "🧑‍🏫"
            elif msg_persona == "AI Concierge": avatar = "🤖"
            
            with st.chat_message(role, avatar=avatar):
                if role == "user":
                    st.caption(f"{msg_persona}")
                st.markdown(msg["content"])

    # User Input
    prompt = st.chat_input(f"{persona}として回答を入力...")

    if prompt:
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
        
        with st.chat_message("model", avatar="🤖"):
            with st.spinner("AI is thinking..."):
                response = st.session_state.ai_interviewer.send_message(prompt, persona=persona)
                st.markdown(response)
                st.rerun()
elif mode == "Dashboard Mode (Progress)":
    # Navigation Header for Dashboard
    col_dash_head1, col_dash_head2 = st.columns([3, 1])
    with col_dash_head1:
        st.title("📊 Progress Dashboard")
    with col_dash_head2:
        # 3-Way Back Navigation
        st.button("⬅️ 経営者チャットへ", on_click=change_mode, args=("Chat Mode (Interview)", "経営者"))
        st.button("⬅️ 従業員チャットへ", on_click=change_mode, args=("Chat Mode (Interview)", "従業員"))
        st.button("⬅️ 商工会チャットへ", on_click=change_mode, args=("Chat Mode (Interview)", "商工会職員"))

    st.info("チャット履歴から事業計画書の完成度を自動判定します。")
    
    from src.core.jigyokei_schema import JigyokeiPlan
    
    # 解析実行ボタン
    if st.button("🔄 Analyze & Update Dashboard", type="primary"):
        st.info("🚀 Process Started: Checking Modules...")
        
        # スピナーを使わずに逐次実行を表示
        status_placeholder = st.empty()
        
        try:
            status_placeholder.text("⏳ Importing Schema...")
            from src.core.jigyokei_schema import JigyokeiPlan
            
            status_placeholder.text("⏳ Calling Gemini API (This may take 10-20s)...")
            extracted_data = st.session_state.ai_interviewer.analyze_history()
            
            status_placeholder.text(f"✅ API Returned. Data Type: {type(extracted_data)}")
            st.write("Raw API Data:", extracted_data) # Show raw data for debug
            
            if extracted_data:
                status_placeholder.text("⏳ Validating data with Pydantic...")
                plan = JigyokeiPlan(**extracted_data)
                st.session_state.current_plan = plan
                status_placeholder.success("🎉 Analysis Complete!")
                
                status_placeholder.success("🎉 Analysis Complete!")
                
                # --- Quality Check & Gap-Filling Logic ---
                issues = plan.check_quality()
                missing_fields = []
                
                if issues:
                    st.warning(f"🧐 **Quality Advisor:** {len(issues)} suggestions found.")
                    for issue in issues:
                        icon = "🚫" if issue.severity == "critical" else "⚠️"
                        st.markdown(f"{icon} **{issue.section} - {issue.field_name}**: {issue.message}")
                        
                        # AIへの誘導リストにも追加
                        if issue.issue_type in ["missing", "insufficient_length"]:
                            missing_fields.append(f"{issue.section}の{issue.field_name}について（{issue.message}）")
                
                if missing_fields:
                    st.session_state.ai_interviewer.set_focus_fields(missing_fields)
                    st.info(f"🤖 AI is ready to ask about: {', '.join([i.split('の')[1].split('について')[0] for i in missing_fields[:3]])}...")
                else:
                    st.session_state.ai_interviewer.set_focus_fields([])
                    st.balloons()
                    st.success("✨ Incredible! The plan looks solid. You are ready for the final review!")

            else:
                status_placeholder.warning("⚠️ No data extracted (Empty result received).")
        except Exception as e:
            status_placeholder.error(f"❌ Critical Error: {e}")
            st.exception(e)
    
    # 解析結果の表示
    if "current_plan" in st.session_state:
        plan: JigyokeiPlan = st.session_state.current_plan
        
        st.metric(label="Total Progress", value=f"{plan.progress_score()}%")
        st.progress(plan.progress_score() / 100)
        
        with st.expander("🔍 Show Raw API Data (Debug)"):
             # st.json(extracted_data) # This causes NameError if not immediately after analysis
             st.json(plan.model_dump())

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🏢 Basic Info")
            st.table([plan.basic_info.model_dump()])
            
            st.subheader("🌩️ Disaster Risks")
            if plan.disaster_risks:
                st.table([r.model_dump() for r in plan.disaster_risks])
            else:
                st.info("No risks identified.")
            
        with col2:
            st.subheader("💼 Business Content")
            st.json(plan.business_content.model_dump())

        st.divider()
        col3, col4 = st.columns(2)
        with col3:
            st.subheader("🛡️ Pre-Disaster Measures")
            if plan.pre_disaster_measures:
                st.table([m.model_dump() for m in plan.pre_disaster_measures])
            else:
                st.info("No measures identified.")
                
        with col4:
            st.subheader("🚨 Post-Disaster Measures")
            if plan.post_disaster_measures:
                st.table([m.model_dump() for m in plan.post_disaster_measures])
            else:
                st.info("No measures identified.")

    else:
        st.info("☝️ Click the button to analyze current chat history.")

    st.divider()
    with st.expander("Show Raw Chat History"):
        st.json(st.session_state.ai_interviewer.history)
