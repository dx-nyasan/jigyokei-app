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
import src.api.schemas
import src.core.completion_checker
importlib.reload(src.core.jigyokei_core)
importlib.reload(src.api.schemas)
importlib.reload(src.core.completion_checker)

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
    # Map legacy args to new nav selection
    target = "経営者インタビュー" # Default
    
    if mode_name == "Chat Mode (Interview)":
        if persona_name == "経営者": target = "経営者インタビュー"
        elif persona_name == "従業員": target = "従業員インタビュー"
        elif persona_name == "商工会職員": target = "商工会職員インタビュー"
    elif mode_name == "Main Consensus Room (Resolution)":
        target = "Main Consensus Room (全体合意)"
    elif mode_name == "Dashboard Mode (Progress)":
        target = "Dashboard Mode (Progress)"
         
    st.session_state.app_nav_selection = target

with st.sidebar:
    st.header("Jigyokei Hybrid System")
    st.caption("Cloud Edition ☁️")
    st.text(f"Ver: {APP_VERSION}") # バージョンを常に表示
    
    # Navigation Selection
    if "app_nav_selection" not in st.session_state:
        st.session_state.app_nav_selection = "経営者インタビュー"

    # Determine current index for radio
    interview_options = ["経営者インタビュー", "従業員インタビュー", "商工会職員インタビュー"]
    current_nav = st.session_state.app_nav_selection
    
    radio_index = 0
    if current_nav in interview_options:
        radio_index = interview_options.index(current_nav)
        
    # Callback to update state from radio
    def on_radio_change():
        st.session_state.app_nav_selection = st.session_state.nav_radio_key

    selected_interview = st.radio(
        "インタビュー選択",
        interview_options,
        index=radio_index,
        key="nav_radio_key",
        on_change=on_radio_change
    )
    
    # Logic derivation (Internal)
    nav = st.session_state.app_nav_selection
    
    # --- State Tracking for Navigation Flux (Dashboard Return) ---
    if "last_chat_nav" not in st.session_state:
        st.session_state.last_chat_nav = "経営者インタビュー"

    valid_return_targets = [
        "経営者インタビュー", 
        "従業員インタビュー", 
        "商工会職員インタビュー", 
        "Main Consensus Room (全体合意)"
    ]
    if nav in valid_return_targets:
        st.session_state.last_chat_nav = nav
    # -------------------------------------------------------------

    if nav == "経営者インタビュー":
        mode = "Chat Mode (Interview)"
        persona = "経営者"
    elif nav == "従業員インタビュー":
        mode = "Chat Mode (Interview)"
        persona = "従業員"
    elif nav == "商工会職員インタビュー":
        mode = "Chat Mode (Interview)"
        persona = "商工会職員"
    elif nav == "Main Consensus Room (全体合意)":
        mode = "Main Consensus Room (Resolution)"
        persona = "総合調整役"
    elif nav == "Dashboard Mode (Progress)":
        mode = "Dashboard Mode (Progress)"
        persona = "Viewer"
    else: # Fallback
        mode = "Chat Mode (Interview)"
        persona = "経営者"

    # Manager Menu (Hidden by default)
    with st.expander("管理者メニュー", expanded=False):

        if st.button("全体合意ルーム (Consensus)", use_container_width=True):
             st.session_state.app_nav_selection = "Main Consensus Room (全体合意)"
             st.rerun()
             
        if st.button("ダッシュボード (Progress)", use_container_width=True):
             st.session_state.app_nav_selection = "Dashboard Mode (Progress)"
             st.rerun()

        st.divider()
        st.caption("Data Management")
        
        # --- Upload (Import) ---
        import_owner_label = "データ所有者 (タグ補完用)"
        import_owner = st.selectbox(
            import_owner_label, 
            ["自動 (Auto)", "経営者", "従業員", "商工会職員"], 
            index=0,
            key="import_owner_select", # Changed key to avoid duplicate error if previously rendered? No, component moved.
            help="古いデータを読み込む際、誰の会話データか指定します。「自動」の場合はファイル内の情報を優先します。"
        )
        
        uploaded_file = st.file_uploader("JSONファイルをドラッグ＆ドロップ", type=["json"])
        
        if uploaded_file:
            file_id = f"{uploaded_file.name}_{uploaded_file.size}"
            if st.session_state.get("last_loaded_file_id") != file_id:
                try:
                    uploaded_file.seek(0)
                    data = json.load(uploaded_file)
                    
                    # Handle if data is a list (e.g. raw history list or basic_scenario)
                    if isinstance(data, list):
                        # Check if it looks like a valid history list (items must be dicts with 'role' and 'content')
                        if all(isinstance(m, dict) and "role" in m and "content" in m for m in data):
                             valid_history = data
                             if import_owner != "自動 (Auto)":
                                for msg in valid_history:
                                    if "persona" not in msg: msg["persona"] = import_owner
                                    if "target_persona" not in msg and msg.get("role") == "model": msg["target_persona"] = import_owner
                             
                             st.session_state.ai_interviewer.load_history(valid_history, merge=True)
                             st.session_state.loaded_msg_count = len(st.session_state.ai_interviewer.history)
                             st.toast(f"✅ 会話履歴(リスト形式)を統合しました ({len(valid_history)}件)", icon="📥")
                        else:
                             st.warning("⚠️ 読み込めるデータ形式ではありません (対応形式: 事業計画JSON, または会話履歴リスト)")
                    
                    elif isinstance(data, dict):
                        # 1. History Loading Logic (Existing Wrapper)
                        if "history" in data:
                            valid_history = [m for m in data.get("history", []) if isinstance(m, dict)]
                            
                            if import_owner != "自動 (Auto)":
                                for msg in valid_history:
                                    if "persona" not in msg and msg.get("role") == "user":
                                        msg["persona"] = import_owner
                                    if "target_persona" not in msg and msg.get("role") == "model":
                                        msg["target_persona"] = import_owner
                            
                            st.session_state.ai_interviewer.load_history(valid_history, merge=True)
                            st.session_state.loaded_msg_count = len(st.session_state.ai_interviewer.history)
                            st.toast(f"✅ 会話履歴を統合しました ({len(valid_history)}件)", icon="📥")

                        # 2. Direct Plan Loading Logic (New for Test Data)
                        # Check if 'basic_info' or 'goals' (key fields of ApplicationRoot) exists
                        elif "basic_info" in data or "goals" in data:
                            from src.api.schemas import ApplicationRoot
                            try:
                                # Attempt to validate and load as current plan
                                # Note: validate might fail if partial data, so we might need construct=True or partial validation
                                # But let's try strict first as user said "test data"
                                plan = ApplicationRoot.model_validate(data)
                                st.session_state.current_plan = plan
                                st.toast("✅ 事業計画データを読み込みました (Direct Load)", icon="📄")
                            except Exception as val_e:
                                st.warning(f"データ構造読み込み警告: {val_e}")
                                # Fallback: Load as dict anyway for debugging
                                # st.session_state.current_plan = ApplicationRoot.construct(**data) 
                                pass
                        
                        else:
                            st.warning("⚠️ 読み込めるデータ形式ではありません (history, basic_info, goals キーが見つかりません)")
                    else:
                         st.warning("⚠️ JSON形式が無効です")

                    st.session_state.last_loaded_file_id = file_id
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error loading JSON: {e}")

        # --- Download (Export) ---
        if st.session_state.ai_interviewer.history:
            # 1. Full Backup
            full_history_json = json.dumps({"history": st.session_state.ai_interviewer.history}, indent=2, ensure_ascii=False)
            st.download_button(
                label="📦 全データを保存 (Backup All)",
                data=full_history_json,
                file_name=f"jigyokei_full_backup_{int(time.time())}.json",
                mime="application/json"
            )

            # 1.5 Draft Plan Export (Markdown) - Only if analyzed
            # TEMPORARY: Disabled Markdown Export due to Schema Migration (JigyokeiPlan -> ApplicationRoot)
            if False and "current_plan" in st.session_state and st.session_state.current_plan:
                plan_export = st.session_state.current_plan
                # Simple MD generation
                md_text = f"# 事業継続力強化計画（下書き）\\n\\n"
                md_text += f"## 基本情報\\n- 企業名: {plan_export.basic_info.company_name}\\n- 代表者: {plan_export.basic_info.representative_name}\\n- 住所: {plan_export.basic_info.address}\\n\\n"
                md_text += f"## 事業内容\\n- 顧客: {plan_export.business_content.target_customers}\\n- 商品・サービス: {plan_export.business_content.products_services}\\n- 提供方法: {plan_export.business_content.delivery_methods}\\n- 強み: {plan_export.business_content.core_competence}\\n\\n"
                md_text += f"## 被害想定 (リスク)\\n"
                for r in plan_export.disaster_risks:
                    md_text += f"- {r.risk_type}: {r.impact_description}\\n"
                md_text += f"\\n## 事前対策\\n"
                for m in plan_export.pre_disaster_measures:
                    md_text += f"- {m.item}: {m.content} (担当: {m.in_charge})\\n"
                
                st.download_button(
                    label="📝 下書きシートを保存 (Markdown)",
                    data=md_text,
                    file_name=f"jigyokei_draft_{int(time.time())}.md",
                    mime="text/markdown",
                    help="解析済みの計画書データをテキストファイルとして保存します。"
                )
            
            # 2. Persona Specific Export
            # Note: Need to access 'persona' variable which is derived LATER.
            # CRITICAL: We cannot access 'persona' here because it is defined AFTER this block.
            # Implication: We should calculate 'persona' inside the expander OR rely on session state if available.
            # BUT 'persona' depends on 'nav' which IS available (st.session_state.app_nav_selection).
            # Let's verify 'nav' logic.
             
             

# --- Main Area ---


if mode == "Chat Mode (Interview)":
    # 1. Dashboard Navigation & Header
    col_head1, col_head2 = st.columns([3, 1])
    with col_head1:
        st.title("🤖 AI Interviewer (Chat Mode)")
    with col_head2:
        st.button(
            "📊 進捗度を確認する",
            on_click=change_mode,
            args=("Dashboard Mode (Progress)",)
        )

    # User Metadata Inputs (Main Panel) - Always visible at top
    with st.container(border=True):
        st.caption(f"📝 {persona}情報入力")
        col_u1, col_u2 = st.columns(2)
        with col_u1:
             pos_placeholder = "例: 代表取締役"
             if persona == "従業員": pos_placeholder = "例: 現場監督"
             elif persona == "商工会職員": pos_placeholder = "例: 経営指導員"
             st.text_input("役職 (Position)", key="user_position_input", placeholder=pos_placeholder)
        with col_u2:
             st.text_input("お名前 (Name)", key="user_name_input", placeholder="例: 山田 太郎")

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
    
    # Helper to render a single message
    def render_message(msg, current_persona):
        if not isinstance(msg, dict): return
        role = msg["role"]
        msg_persona = msg.get("persona", "Unknown")
        target_persona = msg.get("target_persona")
        
        # Filtering Logic
        visible = False
        if role == "user" and msg_persona == current_persona:
            visible = True
        elif role == "model" and target_persona == current_persona:
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
                
                # Sanitize content
                import re
                display_content = re.sub(r'<suggestions>.*?</suggestions>', '', msg["content"], flags=re.DOTALL).strip()
                st.markdown(display_content)

                # Capture suggestions (only from model)
                if role == "model":
                    match = re.search(r'<suggestions>(.*?)</suggestions>', msg["content"], flags=re.DOTALL)
                    if match:
                        try:
                            st.session_state._temp_suggestions = json.loads(match.group(1))
                        except:
                            pass

    # Reset temp suggestions
    if "_temp_suggestions" in st.session_state:
        del st.session_state["_temp_suggestions"]

    history = st.session_state.ai_interviewer.history
    loaded_count = st.session_state.get("loaded_msg_count", 0)

    # 1. Past History (Collapsible)
    if loaded_count > 0:
        with st.expander("🕒 過去のチャット履歴を表示 (Loaded History)", expanded=False):
            for i in range(loaded_count):
                if i < len(history):
                     render_message(history[i], persona)

    # 2. New Session History
    for i in range(loaded_count, len(history)):
        render_message(history[i], persona)
    
    # Retrieve suggestions
    current_dynamic_suggestions = st.session_state.get("_temp_suggestions", None)
        
    # --- Resume Guidance (System Message) ---
    # Only show if loaded history exists and no new messages have been added yet
    if loaded_count > 0 and len(history) == loaded_count:
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
    st.caption("💡 **Quick Replies:** (クリックで返信・トピック選択)")
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
    # Dynamic suggestion logic
    dynamic_list = None
    if current_dynamic_suggestions:
        if isinstance(current_dynamic_suggestions, dict):
            dynamic_list = current_dynamic_suggestions.get("suggested_topics")
        elif isinstance(current_dynamic_suggestions, list):
            dynamic_list = current_dynamic_suggestions

    final_suggestions = dynamic_list if dynamic_list else fallback_map.get(persona, [])
    
    suggested_prompt = None
    
    if final_suggestions:
        for i, topic in enumerate(final_suggestions[:3]):
            if suggestion_cols[i].button(f"🗣️ {topic}", use_container_width=True):
                suggested_prompt = topic

    # User Input
    chat_input_prompt = st.chat_input(f"{persona}として回答を入力...")
    
    # Determine which prompt to use (Button click takes precedence, but st.chat_input is usually None if button clicked)
    # Note: Streamlit execution model means if button clicked, rerun happens, chat_input is None.
    final_prompt = suggested_prompt if suggested_prompt else chat_input_prompt

    if final_prompt:
        with st.chat_message("user", avatar="👤"):
            st.markdown(final_prompt)
        
        # Prepare metadata for context
        user_name = st.session_state.get("user_name_input", "")
        user_position = st.session_state.get("user_position_input", "")
        user_data = {"name": user_name, "position": user_position}

        with st.chat_message("model", avatar="🤖"):
            with st.spinner("AI is thinking..."):
                response = st.session_state.ai_interviewer.send_message(
                    final_prompt, 
                    persona=persona,
                    user_data=user_data
                )
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
        st.button("⬅️ 経営者インタビュー", on_click=change_mode, args=("Chat Mode (Interview)", "経営者"), use_container_width=True)
        st.button("⬅️ 従業員インタビュー", on_click=change_mode, args=("Chat Mode (Interview)", "従業員"), use_container_width=True)
        st.button("⬅️ 商工会職員インタビュー", on_click=change_mode, args=("Chat Mode (Interview)", "商工会職員"), use_container_width=True)

    st.info("チャット履歴から事業計画書の完成度を自動判定します。")
    
    from src.api.schemas import ApplicationRoot
    
    # 解析実行ボタン
    if st.button("解析する", type="primary", use_container_width=True):
        st.info("🚀 Process Started: Checking Modules...")
        
        # スピナーを使わずに逐次実行を表示
        status_placeholder = st.empty()
        
        try:
            status_placeholder.text("⏳ Importing Schema...")
            from src.api.schemas import ApplicationRoot
            
            status_placeholder.text("⏳ Calling Gemini API (This may take 10-20s)...")
            extracted_data = st.session_state.ai_interviewer.analyze_history()
            
            status_placeholder.text(f"✅ API Returned. Data Type: {type(extracted_data)}")
            
            if extracted_data:
                status_placeholder.text("⏳ Validating data with Pydantic...")
                try:
                    plan = ApplicationRoot.model_validate(extracted_data)
                    st.session_state.current_plan = plan
                    status_placeholder.success("🎉 Analysis Complete!")
                except Exception as val_e:
                    status_placeholder.error(f"Validation Error: {val_e}")
                    st.json(extracted_data)
                    st.stop()
                
                # --- Quality Check & Logic (Pending Migration) ---
                # issues = plan.check_quality()
                # missing_fields = []
                # if issues: ...
                
                st.session_state.ai_interviewer.set_focus_fields([]) # Clear focus for now
                
                time.sleep(1)
                st.rerun()

            else:
                status_placeholder.warning("⚠️ No data extracted (Empty result received).")

        except Exception as e:
            status_placeholder.error(f"❌ Critical Error: {e}")
            st.exception(e)
    
    # 解析結果の表示 (Updated for ApplicationRoot key mapping)
    if "current_plan" in st.session_state:
        plan: ApplicationRoot = st.session_state.current_plan
        from src.core.completion_checker import CompletionChecker
        
        # Run Analysis
        result = CompletionChecker.analyze(plan)
        
        # --- 1. Status Banner & Header ---
        st.divider()
        st.subheader("📊 Plan Progress Dashboard")
        
        col_m1, col_m2 = st.columns([1, 4])
        with col_m1:
            st.metric(label="認定可能性スコア (Score)", value=f"{result['total_score']} / 100", help="100点で電子申請の認定要件を満たします")
            
        with col_m2:
            st.caption("認定に向けた必須項目の入力状況 (Mandatory Requirements)")
            st.progress(result['mandatory_progress'])
            st.caption(f"必須項目の達成率: {int(result['mandatory_progress']*100)}% 完了")
            
        # --- 2. Actionable Alerts (Missing Mandatory) ---
        if result['status'] != "success":
            with st.container(border=True): # Red/Error container simulation
                st.error("🚨 申請に向けて、以下の必須項目が不足しています")
                # Define a mapping for section names to Japanese
                section_map = {
                    "BasicInfo": "基本情報",
                    "Goals": "事業概要・目標",
                    "ResponseProcedures": "初動対応",
                    "Measures": "事前対策",
                    "FinancialPlan": "資金計画",
                    "PDCA": "推進体制 (PDCA)"
                }
                for item in result['missing_mandatory']:
                    sec_label = section_map.get(item['section'], item['section'])
                    st.markdown(f"- **{sec_label}**: {item['msg']}")
                
                # Action Buttons (Simulation)
                # Action Buttons (Fixed Logic)
                if st.button("インタビュアーに不足項目を聞いてもらう", type="primary", key="btn_ask_missing"):
                    # 1. Set Focus
                    missing_msgs = [m['msg'] for m in result['missing_mandatory']]
                    st.session_state.ai_interviewer.set_focus_fields(missing_msgs)
                    
                    # 2. Inject System/User Trigger (Optional but helpful)
                    # We want the AI to speak first ideally, or context to be set.
                    # For now, just focus setting is enough as the System Prompt checks focus fields.
                    
                    # 3. Switch Navigation to Chat (Correctly restoring last active persona)
                    st.session_state.app_nav_selection = st.session_state.get("last_chat_nav", "経営者インタビュー")
                    
                    # 4. Rerun to effect change
                    st.rerun()

        elif result['recommended_progress'] < 1.0:
            st.success("✅ 申請要件はクリアしています！ (さらに計画を強化しましょう)")
            with st.expander("💡 さらなる品質向上のヒント (Recommended Actions)", expanded=True):
                for sug in result['suggestions']:
                    st.info(f"Suggestion: {sug}")

        else:
             st.balloons()
             st.success("🏆 Perfect! 計画は完璧です。申請の準備が整いました。")

        # --- 3. Section Breakdown (Application Form Style: 6 Tabs) ---
        st.divider()
        
        # Dynamic Tab Labels (6-tab structure matching electronic application)
        tabs_labels = {
            "BasicInfo": "1️⃣ 基本情報",
            "Goals": "2️⃣ 事業概要・目標",
            "Disaster": "3️⃣ 災害想定",
            "Response": "4️⃣ 初動対応",
            "Measures": "5️⃣ 事前対策",
            "Finance": "6️⃣ 資金・推進体制"
        }
        
        # Check missing items to add warning icons
        missing_sections = [m['section'] for m in result['missing_mandatory']]
        
        if "BasicInfo" in missing_sections: tabs_labels["BasicInfo"] += " ⚠️"
        if "Goals" in missing_sections: tabs_labels["Goals"] += " ⚠️"
        if "Goals" in missing_sections: tabs_labels["Disaster"] += " ⚠️"  # Disaster is part of Goals
        if "ResponseProcedures" in missing_sections: tabs_labels["Response"] += " ⚠️"
        if "Measures" in missing_sections: tabs_labels["Measures"] += " ⚠️"
        if "FinancialPlan" in missing_sections or "PDCA" in missing_sections: tabs_labels["Finance"] += " ⚠️"

        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            tabs_labels["BasicInfo"], 
            tabs_labels["Goals"], 
            tabs_labels["Disaster"],
            tabs_labels["Response"],
            tabs_labels["Measures"],
            tabs_labels["Finance"]
        ])
        
        # TAB 1: Basic Info
        with tab1:
            st.caption("📋 様式第1 基本情報")
            if plan.basic_info:
                bi = plan.basic_info
                full_address = f"{bi.address_pref or ''}{bi.address_city or ''}{bi.address_street or ''}{bi.address_building or ''}"
                
                display_data = {
                    "会社名": bi.corporate_name,
                    "代表者": f"{bi.representative_title or ''} {bi.representative_name or ''}".strip(),
                    "資本金": f"{bi.capital:,}円" if bi.capital else "-",
                    "従業員数": f"{bi.employees}名" if bi.employees else "-",
                    "郵便番号": bi.address_zip,
                    "住所": full_address,
                    "業種": f"{bi.industry_major or ''} / {bi.industry_middle or ''}".strip(" /"),
                    "法人番号": bi.corporate_number or "-"
                }
                st.table([{"項目": k, "内容": v} for k, v in display_data.items() if v and v != "-"])
            else:
                with st.container(border=True):
                    st.warning("⚠️ 基本情報が未入力です。")
        
        # TAB 2: Overview & Goals
        with tab2:
            st.caption("📋 様式第2 事業活動の概要・取組目的")
            
            with st.container(border=True):
                st.subheader("事業活動の概要")
                if plan.goals.business_overview:
                    st.info(plan.goals.business_overview)
                else:
                    st.error("🚨 事業活動の概要が未入力です。")
                    st.caption("自社の事業内容、サプライチェーン上の役割、地域経済への貢献を具体的に記述してください。")
            
            with st.container(border=True):
                st.subheader("取組目的")
                if plan.goals.business_purpose:
                    st.info(plan.goals.business_purpose)
                else:
                    st.warning("⚠️ 取組目的が未入力です。")
        
        # TAB 3: Disaster Scenario
        with tab3:
            st.caption("📋 様式第3 想定される自然災害等のリスク")
            
            with st.container(border=True):
                st.subheader("想定する災害")
                if plan.goals.disaster_scenario.disaster_assumption:
                    st.info(plan.goals.disaster_scenario.disaster_assumption)
                else:
                    st.error("🚨 災害想定が未入力です。")
                    st.caption("ハザードマップやJ-SHISを参照し、「震度○○」「浸水深○○m」など具体的な数値を記載してください。")
            
            if plan.goals.disaster_scenario.impact_list:
                st.subheader(f"影響評価（{len(plan.goals.disaster_scenario.impact_list)}件）")
                st.table([i.model_dump() for i in plan.goals.disaster_scenario.impact_list])
            else:
                st.info("影響評価データなし (任意)")
        
        # TAB 4: First Response
        with tab4:
            st.caption(f"📋 様式第4 初動対応手順等: {result['counts']['procedures']}件登録済")
            if plan.response_procedures:
                st.table([m.model_dump() for m in plan.response_procedures])
            else:
                with st.container(border=True):
                    st.error("🚨 初動対応が未登録です。")
                    st.caption("災害発生直後に誰が何をするか（例：安否確認、避難誘導）を決めてください。")
        
        # TAB 5: Measures
        with tab5:
            st.caption(f"📋 様式第5 平時の取組: {result['counts']['measures']}件登録済")
            if plan.measures:
                st.table([m.model_dump() for m in plan.measures])
            else:
                with st.container(border=True):
                    st.error("🚨 事前対策がまだ登録されていません。")
                    st.caption("リスクを軽減するための具体的な対策（例：在庫分散、棚の固定、クラウドバックアップ）を登録してください。")
        
        # TAB 6: Finance & PDCA
        with tab6:
            st.caption("📋 様式第6 資金計画・推進体制")
            
            with st.container(border=True):
                st.subheader("💰 資金計画")
                if plan.financial_plan.items:
                    st.table([i.model_dump() for i in plan.financial_plan.items])
                else:
                    st.warning("⚠️ 資金計画が未入力です。")
                    st.caption("復旧にかかる費用の目安と、その調達方法（保険、自己資金、借入など）を検討してください。")
            
            with st.container(border=True):
                st.subheader("🛠️ 設備リスト (税制優遇)")
                if plan.equipment.items:
                    st.table([i.model_dump() for i in plan.equipment.items])
                else:
                    st.info("設備リストなし (任意)")
            
            with st.container(border=True):
                st.subheader("🔄 推進体制・訓練")
                pdca_data = {
                    "管理体制": plan.pdca.management_system or "-",
                    "訓練・教育": plan.pdca.training_education or "-"
                }
                st.table([{"項目": k, "内容": v} for k, v in pdca_data.items()])

        # --- 4. Sidebar Tools (Injected here dynamically or rely on static layout) ---
        # Note: Sidebar is already rendered at top of script. We can add to it here or just leave as is.
        # Adding a dedicated "Tools" expander in main area for visibility
        with st.expander("🛠️ お役立ちツール (External Tools)"):
            c1, c2, c3 = st.columns(3)
            c1.link_button("🌍 ハザードマップポータル", "https://disaportal.gsi.go.jp/")
            c2.link_button("📉 J-SHIS 地震予測", "https://www.j-shis.bosai.go.jp/")
            c3.link_button("💴 BCPポータル (リスクファイナンス等)", "https://kyoujinnka.smrj.go.jp/")

    else:
        st.info("☝️ Click the button to analyze current chat history.")

    st.divider()
    with st.expander("Show Raw Chat History"):
        st.json(st.session_state.ai_interviewer.history)

elif mode == "Main Consensus Room (Resolution)":
    st.title("⚖️ Consensus Room (全体合意)")
    st.caption("各ペルソナの意見を調整し、最終的な方針を決定します。")
    
    # Conflict Detection
    with st.expander("🧐 矛盾・未合意事項の検知 (Conflict Detection)", expanded=True):
        if st.button("矛盾を再スキャンする", type="primary"):
            with st.spinner("Analyzing conflicts..."):
                conflicts = st.session_state.ai_interviewer.detect_conflicts()
                st.session_state._conflicts_cache = conflicts
        
        # Retrieve cache
        current_conflicts_data = st.session_state.get("_conflicts_cache", {})
        current_conflicts = current_conflicts_data.get("conflicts", [])
        
        if current_conflicts:
            st.warning(f"{len(current_conflicts)}件の矛盾または未合意事項が見つかりました。")
            for i, c in enumerate(current_conflicts):
                st.markdown(f"#### {i+1}. {c.get('topic', 'Topic')}")
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"**A: {c.get('persona_A')}**\n\n{c.get('statement_A')}")
                with col2:
                    st.info(f"**B: {c.get('persona_B')}**\n\n{c.get('statement_B')}")
                st.success(f"💡 **AI Suggestion**: {c.get('suggestion')}")
                st.divider()
        else:
             st.info("矛盾は見つかりませんでした (未スキャンまたは解消済み)")

    st.divider()
    st.subheader("💬 全体方針の決定")
    
    # Chat History
    history = st.session_state.ai_interviewer.history
    
    # Show history using rendered helper
    for i in range(len(history)):
         render_message(history[i], "総合調整役") 
    
    # Input
    if prompt := st.chat_input("全体方針を入力してください (例: 避難場所は高台の公園とします)"):
         with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
         
         # Metadata
         user_name = st.session_state.get("user_name_input", "")
         user_position = st.session_state.get("user_position_input", "")
         user_data = {"name": user_name, "position": user_position}
         
         with st.chat_message("model", avatar="🤖"):
            with st.spinner("AI Facilitator is recording..."):
                response = st.session_state.ai_interviewer.send_message(
                    prompt, 
                    persona="総合調整役",
                    user_data=user_data
                )
                st.markdown(response)
                st.rerun()
