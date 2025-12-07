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

    st.subheader("Data Management")
    
    # --- Upload (Import) ---
    st.caption("📤 Import Session")
    import_owner_label = "データ所有者 (タグ補完用)"
    import_owner = st.selectbox(
        import_owner_label, 
        ["自動 (Auto)", "経営者", "従業員", "商工会職員"], 
        index=0,
        help="古いデータを読み込む際、誰の会話データか指定します。「自動」の場合はファイル内の情報を優先します。"
    )
    
    uploaded_file = st.file_uploader("JSONファイルをドラッグ＆ドロップ", type=["json"])
    
    if uploaded_file:
        file_id = f"{uploaded_file.name}_{uploaded_file.size}"
        if st.session_state.get("last_loaded_file_id") != file_id:
            try:
                uploaded_file.seek(0)
                data = json.load(uploaded_file)
                
                # Tag Injection Logic
                # Validate history items are dicts
                valid_history = [m for m in data.get("history", []) if isinstance(m, dict)]
                
                if import_owner != "自動 (Auto)":
                    for msg in valid_history:
                        if "persona" not in msg and msg.get("role") == "user":
                            msg["persona"] = import_owner
                        if "target_persona" not in msg and msg.get("role") == "model":
                            msg["target_persona"] = import_owner
                
                # Load with merge=True (Pass dict with 'history' key)
                st.session_state.ai_interviewer.load_history({"history": valid_history}, merge=True)
                st.session_state.last_loaded_file_id = file_id
                
                st.toast(f"✅ データを統合しました ({import_owner})", icon="📥")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Error loading JSON: {e}")

    st.divider()

    # --- Download (Export) ---
    st.caption("💾 Save Session")
    if st.session_state.ai_interviewer.history:
        # 1. Full Backup
        full_history_json = json.dumps({"history": st.session_state.ai_interviewer.history}, indent=2, ensure_ascii=False)
        st.download_button(
            label="📦 全データを保存 (Backup All)",
            data=full_history_json,
            file_name=f"jigyokei_full_backup_{int(time.time())}.json",
            mime="application/json"
        )
        
        # 2. Persona Specific Export
        my_history = []
        for msg in st.session_state.ai_interviewer.history:
            if not isinstance(msg, dict): continue
            p = msg.get("persona")
            tp = msg.get("target_persona")
            if (msg["role"] == "user" and p == persona) or (msg["role"] == "model" and tp == persona):
                my_history.append(msg)
        
        if my_history:
            my_history_json = json.dumps({"history": my_history}, indent=2, ensure_ascii=False)
            st.download_button(
                label=f"💾 {persona}のデータを保存 (Submission)",
                data=my_history_json,
                file_name=f"jigyokei_{persona}_{int(time.time())}.json",
                mime="application/json",
                type="primary"
            )
        else:
            st.caption(f"※ {persona}のデータはまだありません")
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
        if not isinstance(msg, dict): continue
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
                
                # Sanitize content for display (remove suggestions block)
                import re
                display_content = re.sub(r'<suggestions>.*?</suggestions>', '', msg["content"], flags=re.DOTALL).strip()
                st.markdown(display_content)

                # Capture suggestions from the latest model message
                if role == "model":
                    match = re.search(r'<suggestions>(.*?)</suggestions>', msg["content"], flags=re.DOTALL)
                    if match:
                        try:
                            # Store in session state or logic variable to be used below
                            # Since we are in a loop, this will naturally overwrite with the latest valid suggestions
                            current_dynamic_suggestions = json.loads(match.group(1))
                        except:
                            pass
        
    # --- Resume Guidance (System Message) ---
    if st.session_state.ai_interviewer.history:
        with st.container(border=True):
            st.markdown(f"**🤖 System Notification**")
            st.write("以前のチャット履歴を読み込みました。続きから始めましょう。")
            
            # Simple missing info heuristic or static guidance
            if persona == "経営者":
                st.caption("💡 **ヒント**: 会社案内や事業計画書をアップロードすると、入力の手間が省けます。")
            elif persona == "従業員":
                st.caption("💡 **ヒント**: 現場の写真や業務マニュアルがあれば、アップロードしてください。")
            elif persona == "商工会職員":
                st.caption("💡 **ヒント**: 地域防災計画やハザードマップの情報を共有してください。")

    # --- Next Action Suggestions (Above Chat Input) ---
    st.write("💡 **Next Topics:** (クリックで提案トピックについて話します)")
    suggestion_cols = st.columns(3)
    
    # 簡易的なペルソナ別提案リスト (Fallback)
    fallback_map = {
        "経営者": ["事業の強みについて", "自然災害への懸念", "重要な設備・資産"],
        "従業員": ["緊急時の連絡体制", "避難経路の確認", "顧客対応マニュアル"],
        "商工会職員": ["ハザードマップ確認", "損害保険の加入状況", "地域防災計画との連携"]
    }
    
    # Use dynamic if available, else fallback
    # Note: 'current_dynamic_suggestions' needs to be initialized before loop if we want to be safe, 
    # but practically we can just init it here if not found.
    # Actually, Python variable scope in script means 'current_dynamic_suggestions' from loop might be unbound if loop didn't run or define it.
    # Better to initialize it before loop. 
    # BUT, since I can't edit "before loop" easily in this chunk without big context, 
    # I will use a safe access pattern or `locals().get`. 
    
    # Just to be safe and clean, let's use the fallback lookup.
    final_suggestions = locals().get("current_dynamic_suggestions", fallback_map.get(persona, []))
    
    suggested_prompt = None
    
    for i, topic in enumerate(final_suggestions):
        if i < 3: # Limit to 3 columns
            # ボタンテキストはそのままトピック名
            if suggestion_cols[i].button(f"🗣️ {topic}", use_container_width=True):
                # ユーザーの要望「選択肢を選ぶだけで良い」-> トピックテキストをそのまま回答とする
                # ただし、「〜について」のような抽象的な話題の場合は補完してもよいが、AIが「はい」「いいえ」を出す場合はそのままが良い。
                # 汎用的にするため、そのまま送る。
                suggested_prompt = topic

    # User Input
    chat_input_prompt = st.chat_input(f"{persona}として回答を入力...")
    
    # Determine which prompt to use (Button click takes precedence, but st.chat_input is usually None if button clicked)
    # Note: Streamlit execution model means if button clicked, rerun happens, chat_input is None.
    final_prompt = suggested_prompt if suggested_prompt else chat_input_prompt

    if final_prompt:
        with st.chat_message("user", avatar="👤"):
            st.markdown(final_prompt)
        
        with st.chat_message("model", avatar="🤖"):
            with st.spinner("AI is thinking..."):
                response = st.session_state.ai_interviewer.send_message(final_prompt, persona=persona)
                st.markdown(response)
                
                # Feedback Toast
                st.toast("📝 会話ログを更新しました (Conversation Log Updated)", icon="✅")
                time.sleep(1) # Wait for toast to be seen briefly
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
