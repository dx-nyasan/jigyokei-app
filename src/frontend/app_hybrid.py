import sys
import os
import streamlit as st
import json
import time
import importlib
import streamlit.components.v1 as components

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
import src.core.draft_exporter
importlib.reload(src.core.jigyokei_core)
importlib.reload(src.api.schemas)
importlib.reload(src.core.completion_checker)
importlib.reload(src.core.draft_exporter)

importlib.reload(src.core.draft_exporter)

from src.core.jigyokei_core import AIInterviewer
from src.data.context_loader import ContextLoader
from src.core.completion_checker import CompletionChecker
#         
#         # Restore History
#         history = saved_data["history"]
#         st.session_state.ai_interviewer.load_history(history, merge=False)
#         st.session_state.loaded_msg_count = len(history)
#         
#         # Restore Plan if exists
#         current_plan_dict = saved_data.get("current_plan")
#         if current_plan_dict:
#              try:
#                 from src.api.schemas import ApplicationRoot
#                 plan = ApplicationRoot.model_validate(current_plan_dict)
#                 st.session_state.current_plan = plan
#              except Exception:
#                  pass # Ignore plan restore error

if "app_version" not in st.session_state or st.session_state.app_version != APP_VERSION:
    st.session_state.clear()
    st.session_state.app_version = APP_VERSION
    st.rerun()

# --- Debug / Reset Controls ---
with st.sidebar:
    with st.expander("🔧 System Menu", expanded=False):
        if st.button("🗑️ Reset All Data", key="btn_hard_reset", type="primary", help="警告: すべてのデータを削除して初期化します"):
            st.session_state.clear()
            st.session_state.session_manager.clear_session()
            st.rerun()

# --- Initialize Managers (Standard) ---
if "ai_interviewer" not in st.session_state:
    st.session_state.ai_interviewer = AIInterviewer()
else:
    # Check for outdated instance (missing 'analyze_history')
    if not hasattr(st.session_state.ai_interviewer, "analyze_history"):
        st.warning("🔄 Upgrading AI Brain to latest version...")
        
        # Preserve old history
        old_history = getattr(st.session_state.ai_interviewer, "history", [])
        
        # Re-initialize with new class definition
        st.session_state.ai_interviewer = AIInterviewer()
        
        # Restore history logic... (simplified for this block, as load_history handles it)
        st.session_state.ai_interviewer.load_history(old_history)
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

    # --- Live Progress Indicator ---
    from src.core.completion_checker import CompletionChecker
    
    current_plan_obj = st.session_state.get("current_plan")
    if current_plan_obj:
        try:
             checker = CompletionChecker(current_plan_obj)
             # Basic Info is Step 1, Goals Step 2... Let's use overall completeness
             missing_count = len(checker.check_missing_fields())
             total_fields = 20 # Estimate
             progress = max(0, min(100, int((20 - missing_count) / 20 * 100)))
             
             st.divider()
             st.progress(progress / 100)
             st.caption(f"現在の進捗: {progress}% (残り項目: {missing_count})")
             
             if st.button("📊 進捗詳細を確認 (Dashboard)", key="sidebar_progress_btn"):
                 st.session_state.app_nav_selection = "Dashboard Mode (Progress)"
                 st.rerun()
             st.divider()
        except:
             pass
    
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
                                # Migration Step
                                clean_data = ApplicationRoot.migrate_legacy_data(data)
                                
                                # Attempt to validate and load as current plan
                                plan = ApplicationRoot.model_validate(clean_data)
                                st.session_state.current_plan = plan
                                st.toast("✅ 事業計画データを読み込みました (Direct Load)", icon="📄")
                            except Exception as val_e:
                                st.error(f"データ構造読み込みエラー: {val_e}")
                                # Stop execution so user sees the error
                                st.stop()


                        
                        else:
                            st.warning("⚠️ 読み込めるデータ形式ではありません (history, basic_info, goals キーが見つかりません)")
                    else:
                         st.warning("⚠️ JSON形式が無効です")

                    st.session_state.last_loaded_file_id = file_id
                    time.sleep(1)
                    # Only rerun if successful (toast would persist?) - actually Streamlit recommends rerun on state change
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
            key=f"uploader_{persona}" # Remove timestamp to keep uploader stable
        )
        
        # --- Auto-Process Logic ---
        if "processed_file_ids" not in st.session_state:
            st.session_state.processed_file_ids = set()

        if uploaded_refs:
            new_files_to_process = []
            for file in uploaded_refs:
                # Create a simple unique ID for the file instance
                file_id = f"{file.name}_{file.size}"
                if file_id not in st.session_state.processed_file_ids:
                    new_files_to_process.append(file)
                    st.session_state.processed_file_ids.add(file_id)
            
                if new_files_to_process:
                # Automatically process new files
                 with st.spinner("資料を解析中... (Auto-Processing)"):
                    try:
                        count = st.session_state.ai_interviewer.process_files(new_files_to_process, target_persona=persona)
                        st.success(f"{count}件の新しい資料を読み込みました！")
                        
                        # --- Agentic Extraction Trigger (File Upload) ---
                        if count > 0:
                            with st.status("🤖 AI Agent Working: 資料を詳細分析中...", expanded=True) as status:
                                 status.write("📝 Gemini 1.5 Pro (High Reasoning) で資料を読み込んでいます...")
                                 try:
                                     all_files = st.session_state.ai_interviewer.uploaded_file_refs
                                     extracted_data = st.session_state.ai_interviewer.extract_structured_data(text="", file_refs=all_files)
                                     
                                     if extracted_data:
                                         status.write("✅ 構造化データを検出しました。")
                                         status.write("💡 抽出結果は会話コンテキストに保持されました。")
                                     else:
                                         status.write("ℹ️ 新規の構造化データは見つかりませんでした。")
                                 except Exception as ex_e:
                                     status.error(f"Extraction Error: {ex_e}")
                        
                        time.sleep(1)
                        perform_auto_save()
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
                            pass
    # Reset temp suggestions
    if "_temp_suggestions" in st.session_state:
        del st.session_state["_temp_suggestions"]

    # --- Auto-Scroll Logic ---
    # Check if a new message has been added
    current_len = len(st.session_state.ai_interviewer.history)
    last_len = st.session_state.get("last_history_len", 0)

    if current_len > last_len:
        # Inject JavaScript to scroll to the top of the last message
        js = """
        <script>
            var elements = window.parent.document.querySelectorAll('.stChatMessage');
            if (elements.length > 0) {
                var last = elements[elements.length - 1];
                last.scrollIntoView({behavior: "smooth", block: "start"});
            }
        </script>
        """
        components.html(js, height=0)
        st.session_state["last_history_len"] = current_len
    
    # Ensure baseline is set if it's the first run or reset
    if "last_history_len" not in st.session_state:
        st.session_state["last_history_len"] = current_len

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

    # --- Rendering Contextual Support (Hints & Examples) ---
    # Retrieve suggestions from LAST message if it was from model
    last_msg = history[-1] if history else None
    current_suggestions = {}
    
    if last_msg and last_msg["role"] == "model":
        import re
        match = re.search(r'<suggestions>(.*?)</suggestions>', last_msg["content"], flags=re.DOTALL)
        if match:
            try:
                current_suggestions = json.loads(match.group(1))
            except:
                pass

    suggested_prompt = None

    if current_suggestions:
        hints = current_suggestions.get("hints")
        example = current_suggestions.get("example")
        
        if hints or example:
            with st.container(border=True): # Distinct box for AI assistance
                st.caption("💡 AIからのアドバイス")
                if hints:
                    st.info(f"**ヒント**: {hints}")
                if example:
                    st.success(f"**回答例**: {example}")
                    # Improvement: Button to use the example as answer
                    # Use stable key based on content hash AND history length to ensure uniqueness per turn
                    import hashlib
                    # Include length of history to differentiate "Yes" at turn 1 vs "Yes" at turn 5
                    unique_str = f"{example}_{len(st.session_state.ai_interviewer.history)}"
                    stable_key = hashlib.md5(unique_str.encode()).hexdigest()
                    if st.button("📋 回答例の通り回答する", key=f"use_example_{stable_key}"):
                        suggested_prompt = example

    # --- Next Action Suggestions (Quick Replies) ---
    st.caption("👇 クイック返信 (クリックで送信)")
    
    # Prioritize dynamic options
    options = current_suggestions.get("options", [])
    
    # Fallback if no dynamic options
    if not options:
        fallback_map = {
            "経営者": ["事業の強みについて", "自然災害への懸念", "重要な設備・資産"],
            "従業員": ["緊急時の連絡体制", "避難経路の確認", "顧客対応マニュアル"],
            "商工会職員": ["ハザードマップ確認", "損害保険の加入状況", "地域防災計画との連携"]
        }
        options = fallback_map.get(persona, [])

    # Render Options
    if options:
        cols = st.columns(min(len(options), 4))
        for i, opt in enumerate(options[:4]):
            # Use stable key based on option content and index to prevent state loss
            if cols[i].button(opt, use_container_width=True, key=f"quick_reply_{i}_{opt}"):
                suggested_prompt = opt
                          # Since it's nested Pydantic, this is non-trivial without a proper recursive merge.
                          # Plan B: Just store it in "latest_extracted" and let the Dashboard "Analyze" button handle the full merge?
                          # No, user wants immediate effect.
                          
                          # Validating directly
                          # Note: logic here is risky without deep matching.
                          # For this iteration, let's just toast that we 'Understood' and rely on the AI's short-term memory (Context)
                          # because sending it to the chat history (which we do below) is the primary way the Chat AI knows about it.
                          # The "Structuring" happens when we hit "Analyze" or when we export.
                          # BUT, the user said "Gemini 3.0... text to it... then Gemini 2.5".
                          # The `extract_structured_data` USES a separate model (implied).
                          # AND we inject the result back into history?
                          pass
                          
                  except Exception as e:
                      print(f"Extraction failed: {e}")
                      status.update(label="⚠️ Extraction skipped", state="error")
        
        # Determine who responds: Model or just UI update (Wait, logic flow check)
        # The structure here is: if we have a prompt (user input or suggestion), we send it.
        
        with st.chat_message("model", avatar="🤖"):
            with st.spinner("AI is thinking..."):
                response = st.session_state.ai_interviewer.send_message(
                    final_prompt, 
                    persona=persona,
                    user_data=user_data
                )
                st.markdown(response)
                
                # --- Auto-Save Hook ---
                perform_auto_save()
                
                # Feedback Toast
                st.toast("📝 会話ログを更新しました (Log Saved)", icon="✅")
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
                    # Robust Migration for Legacy/Loose Formats
                    migrated = ApplicationRoot.migrate_legacy_data(extracted_data)
                    plan = ApplicationRoot.model_validate(migrated)
                    
                    st.session_state.current_plan = plan
                    status_placeholder.success("🎉 Analysis Complete & Plan Updated!")
                    
                    # Auto-Save after Analysis
                    perform_auto_save()
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
            
        # --- 2. Actionable Alerts (Missing Mandatory) - SEVERITY-BASED ---
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
                
                # ... (Logic omitted for brevity in tool call, but context needs to match) ...
                # Group by severity for clearer display
                critical_items = [m for m in result['missing_mandatory'] if m.get('severity') == 'critical']
                warning_items = [m for m in result['missing_mandatory'] if m.get('severity') == 'warning']
                
                if critical_items:
                    st.markdown("### 🔴 **Critical (未入力)**")
                    for item in critical_items:
                        sec_label = section_map.get(item['section'], item['section'])
                        st.error(f"**{sec_label}**: {item['msg']}", icon="🔴")
                
                if warning_items:
                    st.markdown("### 🟡 **Warning (入力不足)**")
                    for item in warning_items:
                        sec_label = section_map.get(item['section'], item['section'])
                        st.warning(f"**{sec_label}**: {item['msg']}", icon="🟡")
                
                with st.columns(2)[0]:
                    if st.button("インタビュアーに不足項目を聞いてもらう", type="primary", key="btn_ask_missing"):
                        missing_msgs = [m['msg'] for m in result['missing_mandatory']]
                        st.session_state.ai_interviewer.set_focus_fields(missing_msgs)
                        st.session_state.app_nav_selection = st.session_state.get("last_chat_nav", "経営者インタビュー")
                        # Set flag to auto-start conversation on redirect
                        st.session_state.auto_trigger_message = "現在、ダッシュボードで確認した不足項目（focus_fields）について、具体的な質問を開始してください。ユーザーに選択肢を提示し、回答しやすくしてください。"
                        st.session_state.auto_trigger_persona = st.session_state.get("last_chat_nav", "経営者インタビュー").replace("インタビュー", "") # Rough parse
                        st.rerun()

        elif result['recommended_progress'] < 1.0:
            st.success("✅ 申請要件はクリアしています！ (さらに計画を強化しましょう)")
            with st.expander("💡 さらなる品質向上のヒント (Recommended Actions)", expanded=True):
                for sug in result['suggestions']:
                    st.info(f"Suggestion: {sug}")

        else:
             st.balloons()
             st.success("🏆 Perfect! 計画は完璧です。申請の準備が整いました。")
        
        st.divider()
        col_exp1, col_exp2 = st.columns([3, 1])
        with col_exp2:
            # Excel Export
            if st.button("📄 下書きシート出力 (Excel)", key="btn_export_draft", use_container_width=True):
                try:
                    from src.core.draft_exporter import DraftExporter
                    excel_data = DraftExporter.export_to_excel(plan, result)
                    st.download_button(
                        label="⬇️ ダウンロード開始",
                        data=excel_data,
                        file_name=f"jigyokei_draft_{plan.basic_info.corporate_name or 'plan'}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="btn_download_excel_real"
                    )
                    st.success("Excel生成完了！上のダウンロードボタンを押してください。")
                except ImportError as ie:
                     st.error(f"依存ライブラリ不足: {ie} (pip install openpyxl が必要です)")
                except Exception as e:
                    st.error(f"エクスポートエラー: {e}")

            # JSON Export (For Commerce Society / Backup)
            st.divider()
            json_str = plan.model_dump_json(indent=2)
            st.download_button(
                label="💾 計画データを保存 (JSON)",
                data=json_str,
                file_name=f"jigyokei_data_{plan.basic_info.corporate_name or 'plan'}.json",
                mime="application/json",
                help="商工会連携用、またはバックアップとして保存します。",
                use_container_width=True
            )

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
            st.caption("📋 様式第3 事業活動に影響を与える自然災害等の想定")
            
            with st.container(border=True):
                st.subheader("想定する自然災害等")
                if plan.goals.disaster_scenario.disaster_assumption:
                    st.info(plan.goals.disaster_scenario.disaster_assumption)
                else:
                    st.error("🚨 災害想定が未入力です。")
                    st.caption("ハザードマップを参照し、「震度○○」「浸水深○○m」など具体的な数値を記載してください。")
            
            # New Impact Structure Display
            st.subheader("自然災害等の発生が事業活動に与える影響")
            imp = plan.goals.disaster_scenario.impacts
            impact_data = {
                "人員": imp.impact_personnel,
                "建物・設備": imp.impact_building,
                "資金繰り": imp.impact_funds,
                "情報": imp.impact_info
            }
            # Filter non-empty
            impact_rows = [{"項目": k, "内容": v} for k, v in impact_data.items() if v]
            if impact_rows:
                st.table(impact_rows)
            else:
                st.warning("⚠️ 影響詳細が未入力です。")
        
        # TAB 4: First Response
        with tab4:
            st.caption(f"📋 様式第4 初動対応手順等: {len(plan.response_procedures)}件登録済")
            if plan.response_procedures:
                st.table([m.model_dump() for m in plan.response_procedures])
            else:
                with st.container(border=True):
                    st.error("🚨 初動対応が未登録です。")
                    st.caption("災害発生直後に誰が何をするか（例：安否確認、避難誘導）を決めてください。")
        
        # TAB 5: Measures (A/B/C/D)
        with tab5:
            st.caption(f"📋 様式第5 平時の推進体制 (4カテゴリ)")
            
            measures = plan.measures
            
            # Helper to display MeasureDetail
            def show_measure(label, item):
                with st.expander(label, expanded=True):
                    c1, c2 = st.columns(2)
                    c1.markdown("**現在の取組**")
                    if item.current_measure: c1.info(item.current_measure)
                    else: c1.warning("未入力")
                    
                    c2.markdown("**今後の計画**")
                    if item.future_plan: c2.success(item.future_plan)
                    else: c2.caption("なし")

            show_measure("A: 人員体制の整備 (ヒト)", measures.personnel)
            show_measure("B: 建物・設備の保全 (モノ)", measures.building)
            show_measure("C: 資金調達手段の確保 (カネ)", measures.money)
            show_measure("D: 情報の保護 (情報)", measures.data)

        
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
                st.subheader("🛠️ 設備リスト (税制優遇) (任意)")
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

    # --- File Upload for Consensus (New) ---
    with st.expander("📂 資料の追加アップロード (Upload Documents)", expanded=False):
        uploaded_refs_consensus = st.file_uploader(
            "全体合意用資料をアップロード (PDF/画像)", 
            type=["pdf", "png", "jpg", "jpeg"], 
            accept_multiple_files=True,
            key="uploader_consensus"
        )
        
        # --- Auto-Process Logic (Consensus) ---
        if "processed_file_ids" not in st.session_state:
            st.session_state.processed_file_ids = set()

        if uploaded_refs_consensus:
            new_files_to_process = []
            for file in uploaded_refs_consensus:
                file_id = f"{file.name}_{file.size}"
                if file_id not in st.session_state.processed_file_ids:
                    new_files_to_process.append(file)
                    st.session_state.processed_file_ids.add(file_id)
            
            if new_files_to_process:
                 with st.spinner("資料を解析中... (Processing for Consensus)"):
                    try:
                        # Process files as "総合調整役" (Coordinator)
                        count = st.session_state.ai_interviewer.process_files(new_files_to_process, target_persona="総合調整役")
                        st.success(f"{count}件の資料を全体合意用に読み込みました！")
                        
                        # Agentic Extraction Trigger (Optional but good for consistency)
                        if count > 0:
                             with st.status("🤖 AI Agent Working: 資料を詳細分析中...", expanded=True) as status:
                                 status.write("📝 Gemini 1.5 Pro (High Reasoning) で資料を読み込んでいます...")
                                 try:
                                     all_files = st.session_state.ai_interviewer.uploaded_file_refs
                                     extracted_data = st.session_state.ai_interviewer.extract_structured_data(text="", file_refs=all_files)
                                     if extracted_data:
                                         status.write("✅ 構造化データを検出しました。")
                                     else:
                                         status.write("ℹ️ 新規の構造化データは見つかりませんでした。")
                                 except Exception as ex_e:
                                     status.error(f"Extraction Error: {ex_e}")

                        time.sleep(1)
                        perform_auto_save()
                        st.rerun()
                    except Exception as e:
                        st.error(f"読み込みエラー: {e}")

    
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
    
    # Helper for rendering messages in Consensus Mode (Duplicate of Chat Mode helper to avoid scope issues)
    def render_message_consensus(msg, current_persona):
        if not isinstance(msg, dict): return
        role = msg["role"]
        msg_persona = msg.get("persona", "Unknown")
        target_persona = msg.get("target_persona")
        
        # In Consensus, we generally want to see everything, OR filter by "General" context.
        # However, to be safe and match user expectation: show messages relevant to '総合調整役' or public.
        # Let's show everything for now as it is a "Consensus" room.
        # But if we want to be strict: 
        visible = True # Default to visible in Consensus
        # Apply filter if needed:
        # if role == "model" and target_persona and target_persona != "総合調整役": visible = False
        
        if visible:
            avatar = "🤖" if role == "model" else "👤"
            if msg_persona == "経営者": avatar = "👨‍💼"
            elif msg_persona == "従業員": avatar = "👷"
            elif msg_persona == "商工会職員": avatar = "🧑‍🏫"
            elif msg_persona == "AI Concierge": avatar = "🤖"
            elif msg_persona == "総合調整役": avatar = "⚖️"
            
            with st.chat_message(role, avatar=avatar):
                st.caption(f"{msg_persona}")
                st.markdown(msg["content"])

    # Show history using rendered helper
    for i in range(len(history)):
         render_message_consensus(history[i], "総合調整役") 
    
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
                perform_auto_save()
                st.rerun()
