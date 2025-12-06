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
importlib.reload(src.core.jigyokei_core)

from src.core.jigyokei_core import AIInterviewer
from src.data.context_loader import ContextLoader

# --- Version Control ---
APP_VERSION = "3.1.1-gap-filling-fix"

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

with st.sidebar:
    st.header("Jigyokei Hybrid System")
    st.caption("Cloud Edition ☁️")
    st.text(f"Ver: {APP_VERSION}") # バージョンを常に表示

    st.divider()
    
    # Mode Selection
    mode = st.radio(
        "Select Mode",
        ["Chat Mode (Interview)", "Dashboard Mode (Progress)"],
        index=0
    )
    
    st.divider()

    # Persona Selection
    if mode == "Chat Mode (Interview)":
        st.subheader("Who are you?")
        persona = st.radio(
            "Select Persona",
            ["経営者", "従業員", "商工会職員"],
            index=0
        )
    else:
        persona = "Viewer"

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
        # Prevent infinite rerun loop by checking file ID
        file_id = f"{uploaded_file.name}_{uploaded_file.size}"
        
        if st.session_state.get("last_loaded_file_id") != file_id:
            try:
                uploaded_file.seek(0)
                data = json.load(uploaded_file)
                history = data.get("history", [])
                st.session_state.ai_interviewer.load_history(history)
                
                # Save state to prevent reload
                st.session_state.last_loaded_file_id = file_id
                
                st.success(f"Session Loaded! ({len(history)} messages)")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Failed to load: {e}")

# --- Main Area ---

if mode == "Chat Mode (Interview)":
    st.title("🤖 AI Interviewer (Chat Mode)")
    # st.error("もしこの赤いバーが見えていたら...") # Removed debug marker
    st.markdown("事業計画書の作成に必要な情報をヒアリングします。")

    # 1. チャット履歴表示
    for msg in st.session_state.ai_interviewer.history:
        role = msg["role"]
        persona_name = msg.get("persona", "Unknown")
        
        avatar = "🤖" if role == "model" else "👤"
        if persona_name == "経営者": avatar = "👨‍💼"
        elif persona_name == "従業員": avatar = "👷"
        elif persona_name == "商工会職員": avatar = "🧑‍🏫"
        elif persona_name == "AI Concierge": avatar = "🤖"
        
        with st.chat_message(role, avatar=avatar):
            if role == "user":
                st.caption(f"{persona_name}")
            st.markdown(msg["content"])

    # 2. ユーザー入力
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
    st.title("📊 Progress Dashboard")
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
                
                # --- Gap-Filling Logic ---
                missing_fields = []
                
                # 1. Basic Info Check
                basic_dump = plan.basic_info.model_dump()
                for k, v in basic_dump.items():
                    if not v or v == "未設定":
                        missing_fields.append(f"基本情報-{k}")

                # 2. Business Content Check
                biz_dump = plan.business_content.model_dump()
                for k, v in biz_dump.items():
                    if not v or v == "未設定":
                        missing_fields.append(f"事業内容-{k}")

                # 3. Risks Check
                if not plan.disaster_risks:
                     missing_fields.append("災害リスクの特定")
                
                # 4. Measures Check
                if not plan.pre_disaster_measures:
                     missing_fields.append("事前対策")
                
                if missing_fields:
                    st.session_state.ai_interviewer.set_focus_fields(missing_fields)
                    st.warning(f"🧐 **Next AI Focus:** The AI has detected {len(missing_fields)} missing items. It will proactively ask about these in the chat.")
                    with st.expander("View Missing Items"):
                        st.write(missing_fields)
                else:
                    st.session_state.ai_interviewer.set_focus_fields([])
                    st.balloons()
                    st.success("✨ Incredible! All major items are filled. You are ready to finalize!")

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
             st.json(extracted_data)

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
