import sys
import os
import streamlit as st
import json
import time
import importlib
import streamlit.components.v1 as components
import requests
import re

# --- Helper: Zip Code Address Fetcher ---
def fetch_address_from_zip(zip_code):
    """
    Fetch address from ZipCloud API.
    Returns a dict with {pref, city, town} or None.
    """
    if not zip_code: return None
    
    # Normalize: Remove hyphens, half-width
    clean_zip = zip_code.replace("-", "").strip()
    if not clean_zip.isdigit() or len(clean_zip) != 7:
        return None

    try:
        url = f"https://zipcloud.ibsnet.co.jp/api/search?zipcode={clean_zip}"
        res = requests.get(url, timeout=3)
        data = res.json()
        
        if data["status"] == 200 and data["results"]:
            result = data["results"][0]
            return {
                "pref": result["address1"],  # 都道府県
                "city": result["address2"],  # 市区町村
                "town": result["address3"]   # 町域
            }
        return None
    except Exception:
        return None

# --- Page Config (Must be the first Streamlit command) ---
st.set_page_config(
    page_title="Jigyokei Hybrid System",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Reset Toast Logic ---
if "reset_msg" in st.query_params and "reset_toast_shown" not in st.session_state:
    st.toast("✅ データをリセットしました (All Data Cleared)", icon="🗑️")
    st.session_state["reset_toast_shown"] = True
    # Do not clear param to avoid rerun, use session flag to prevent duplicates

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
from src.core.draft_exporter import DraftExporter
from src.core.session_manager import SessionManager

# --- Version Control ---
APP_VERSION = "3.5.0-medium-priority-tasks"

# Initialize Session Manager
if "session_manager" not in st.session_state:
    st.session_state.session_manager = SessionManager()

# --- LocalStorage Auto-Save Helper ---
def inject_localstorage_autosave():
    """
    Inject JavaScript for LocalStorage auto-save functionality.
    Saves plan data to browser's LocalStorage every 30 seconds.
    """
    if "current_plan" in st.session_state:
        try:
            plan_json = st.session_state.current_plan.model_dump_json()
            # Escape for JavaScript string
            plan_json_escaped = plan_json.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")
            
            js_code = f"""
            <script>
            (function() {{
                const key = 'jigyokei_autosave';
                const data = '{plan_json_escaped}';
                try {{
                    localStorage.setItem(key, data);
                    localStorage.setItem(key + '_timestamp', new Date().toISOString());
                    console.log('[Jigyokei] Auto-saved to LocalStorage');
                }} catch(e) {{
                    console.error('[Jigyokei] LocalStorage save failed:', e);
                }}
            }})();
            </script>
            """
            components.html(js_code, height=0)
        except Exception as e:
            pass  # Silently fail

def get_localstorage_data():
    """
    Inject JavaScript to retrieve LocalStorage data and display restore option.
    Returns component that checks for saved data.
    """
    js_code = """
    <div id="ls-restore-container"></div>
    <script>
    (function() {
        const key = 'jigyokei_autosave';
        const data = localStorage.getItem(key);
        const timestamp = localStorage.getItem(key + '_timestamp');
        const container = document.getElementById('ls-restore-container');
        
        if (data && timestamp) {
            const date = new Date(timestamp);
            const formatted = date.toLocaleString('ja-JP');
            container.innerHTML = `
                <div style="background: #e3f2fd; padding: 10px; border-radius: 5px; margin: 5px 0;">
                    <strong>💾 前回のセッションデータが見つかりました</strong><br>
                    <small>保存日時: ${formatted}</small>
                </div>
            `;
        }
    })();
    </script>
    """
    return js_code


# --- Auto Resume Logic ---
# [DISABLED] Automatic loading of shared session file causes data leak between users in Cloud environment.
# if "ai_interviewer" not in st.session_state and "last_resume_check" not in st.session_state:
#     st.session_state.last_resume_check = True
#     saved_data = st.session_state.session_manager.load_session()
#     if saved_data and saved_data.get("history"):
#         st.toast("🔄 前回の中断箇所から復元しました (Session Auto-Resumed)", icon="📂")
#         # Initialize interviewer with history immediately
#         st.session_state.ai_interviewer = AIInterviewer()
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
            st.query_params["reset_msg"] = "true"
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
# Onboarding Wizard (First-time user guidance)
# ==========================================
def show_onboarding_wizard():
    """初回利用者向けオンボーディングウィザード"""
    if st.session_state.get("onboarding_complete", False):
        return True
    
    st.markdown("## 🎉 事業継続力強化計画 策定支援システムへようこそ！")
    st.markdown("---")
    
    st.info("""
    **本システムでは、AIと対話しながら事業継続力強化計画を作成できます。**
    
    3つのステップで進めましょう：
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📝 Step 1")
        st.markdown("**基本情報入力**")
        st.caption("会社名、住所、業種など")
    
    with col2:
        st.markdown("### 💬 Step 2")
        st.markdown("**AIインタビュー**")
        st.caption("災害想定、対策などをヒアリング")
    
    with col3:
        st.markdown("### 📊 Step 3")
        st.markdown("**確認・出力**")
        st.caption("監査→修正→Excel出力")
    
    st.markdown("---")
    
    # Role selection
    st.markdown("### あなたの立場を教えてください")
    role = st.radio(
        "役割を選択",
        ["経営者（事業主）", "従業員", "商工会職員"],
        horizontal=True,
        key="onboarding_role"
    )
    
    # --- Task 1: Industry Template Selector ---
    st.markdown("### 業種を選択してください（テンプレート適用）")
    
    # Load industry templates
    try:
        import json
        template_path = Path(__file__).parent.parent / "data" / "industry_templates.json"
        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                templates_data = json.load(f)
            
            template_options = {
                "テンプレートなし（空白から開始）": None,
                "🏭 製造業": "manufacturing",
                "🏪 小売業": "retail",
                "💼 サービス業": "service",
                "🏗️ 建設業": "construction",
                "🍽️ 飲食業": "restaurant"
            }
            
            selected_template = st.selectbox(
                "業種テンプレート",
                list(template_options.keys()),
                key="onboarding_template",
                help="業種を選択すると、災害想定や事前対策の雛形が自動入力されます"
            )
            
            st.session_state["selected_industry_template"] = template_options.get(selected_template)
            
            # Show preview if template selected
            if template_options.get(selected_template):
                template_key = template_options[selected_template]
                template_info = templates_data.get("templates", {}).get(template_key, {})
                if template_info:
                    with st.expander("📋 テンプレート内容プレビュー", expanded=False):
                        st.caption(f"**災害想定**: {template_info.get('disaster_assumption', '')[:100]}...")
                        st.caption(f"**事業概要**: {template_info.get('business_overview', '')[:100]}...")
        else:
            st.session_state["selected_industry_template"] = None
    except Exception as e:
        st.session_state["selected_industry_template"] = None
    
    st.markdown("---")
    
    col_start, col_manual = st.columns(2)
    
    with col_start:
        if st.button("🚀 はじめる", type="primary", use_container_width=True):
            st.session_state["onboarding_complete"] = True
            # Set appropriate interview mode based on role
            if role == "経営者（事業主）":
                st.session_state.app_nav_selection = "経営者インタビュー"
            elif role == "従業員":
                st.session_state.app_nav_selection = "従業員インタビュー"
            else:
                st.session_state.app_nav_selection = "商工会職員インタビュー"
            st.rerun()
    
    with col_manual:
        if st.button("📖 マニュアルを読む", use_container_width=True):
            st.session_state["show_manual_link"] = True
    
    if st.session_state.get("show_manual_link", False):
        st.markdown("""
        **ユーザーマニュアル**
        - [経営者向けマニュアル](docs/USER_MANUAL_MANAGER.md)
        - [従業員向けマニュアル](docs/USER_MANUAL_EMPLOYEE.md)
        - [商工会職員向けマニュアル](docs/USER_MANUAL_OFFICIAL.md)
        """)
    
    st.caption("💡 ヒント: いつでもサイドバーからDashboardで進捗を確認できます")
    
    return False

# Show onboarding for first-time users
if not show_onboarding_wizard():
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

    # --- Live Progress Indicator (Always Visible) ---
    st.divider()
    
    current_plan_obj = st.session_state.get("current_plan")
    if current_plan_obj:
        try:
            from src.core.completion_checker import CompletionChecker
            checker = CompletionChecker(current_plan_obj)
            missing_count = len(checker.check_missing_fields())
            total_fields = 20 # Estimate
            progress = max(0, min(100, int((20 - missing_count) / 20 * 100)))
            
            st.progress(progress / 100)
            st.caption(f"📊 入力進捗: **{progress}%** (残り{missing_count}項目)")
            
            # --- Task 3: Step Wizard Indicator ---
            current_step = 1  # Default
            if progress >= 75:
                current_step = 4  # 出力
            elif progress >= 50:
                current_step = 3  # 監査
            elif progress >= 25:
                current_step = 2  # インタビュー
            
            step_icons = ["📝", "💬", "🔍", "📤"]
            step_labels = ["基本情報", "インタビュー", "監査", "出力"]
            step_display = ""
            for i in range(4):
                if i + 1 < current_step:
                    step_display += f"✅ "  # Completed
                elif i + 1 == current_step:
                    step_display += f"**{step_icons[i]} {step_labels[i]}** → "
                else:
                    step_display += f"⬜ "  # Future
            
            st.markdown(f"**現在のステップ:** Step {current_step}/4")
            st.caption(step_display.rstrip(" → "))
            
        except:
            st.caption("📊 入力進捗: データ準備中...")
    else:
        st.caption("📊 入力進捗: まだ入力がありません")
        st.markdown("**現在のステップ:** Step 1/4")
        st.caption("📝 **基本情報** → ⬜ ⬜ ⬜")
    
    # Always show the dashboard button
    if st.button("📊 進捗詳細を確認 (Dashboard)", key="sidebar_progress_btn", use_container_width=True):
        st.session_state.app_nav_selection = "Dashboard Mode (Progress)"
        st.rerun()
    
    # --- Save Confirmation (Task 3: Explicit Save) ---
    if st.button("💾 データを保存", key="sidebar_save_btn", use_container_width=True):
        if current_plan_obj:
            st.session_state["_last_saved_at"] = __import__("datetime").datetime.now().strftime("%H:%M:%S")
            st.success(f"✅ 保存しました ({st.session_state['_last_saved_at']})")
        else:
            st.warning("⚠️ 保存するデータがありません")
    
    if "_last_saved_at" in st.session_state:
        st.caption(f"最終保存: {st.session_state['_last_saved_at']}")
    
    # --- Task 2: Session Sharing Button ---
    if st.button("🔗 セッションを共有", key="sidebar_share_btn", use_container_width=True):
        if current_plan_obj:
            try:
                from src.core.session_manager import SessionManager
                sm = SessionManager()
                history = st.session_state.get("ai_interviewer", {})
                history_data = history.history if hasattr(history, "history") else []
                plan_dict = current_plan_obj.model_dump() if hasattr(current_plan_obj, "model_dump") else {}
                share_id = sm.create_shareable_session(history_data, plan_dict)
                share_url = sm.get_share_url(share_id)
                st.session_state["_share_url"] = share_url
                st.success("✅ 共有リンクを生成しました")
            except Exception as e:
                st.error(f"共有エラー: {e}")
        else:
            st.warning("⚠️ 共有するデータがありません")
    
    if "_share_url" in st.session_state:
        st.code(st.session_state["_share_url"], language=None)
        st.caption("👆 このURLをコピーして共有してください")
    
    # --- Task 2: CSV Batch Import UI ---
    with st.expander("📁 CSVバッチインポート（複数企業）", expanded=False):
        st.caption("CSVファイルから複数企業のデータを一括読込できます")
        
        uploaded_csv = st.file_uploader(
            "CSVファイルを選択",
            type=["csv"],
            key="batch_csv_uploader"
        )
        
        if uploaded_csv is not None:
            try:
                from src.core.batch_processor import BatchProcessor, get_sample_template
                
                csv_content = uploaded_csv.read().decode("utf-8")
                processor = BatchProcessor()
                
                # Validate columns first
                import csv
                import io
                reader = csv.reader(io.StringIO(csv_content))
                headers = next(reader, [])
                validation = processor.validate_csv_columns(headers)
                
                if not validation["valid"]:
                    st.error(f"❌ 必須列が不足: {', '.join(validation['missing'])}")
                else:
                    if st.button("🚀 インポート実行", key="batch_import_btn"):
                        result = processor.process_batch(csv_content)
                        st.session_state["_batch_result"] = result
                        st.success(result["summary"])
            except Exception as e:
                st.error(f"インポートエラー: {e}")
        
        # Show sample template
        if st.button("📋 サンプルCSVをダウンロード", key="batch_sample_btn"):
            from src.core.batch_processor import get_sample_template
            st.download_button(
                label="sample_template.csv",
                data=get_sample_template(),
                file_name="sample_template.csv",
                mime="text/csv"
            )
        
        # Display batch results if available
        if "_batch_result" in st.session_state:
            result = st.session_state["_batch_result"]
            st.markdown(f"**処理結果**: ✅{result['success']} ⚠️{result['partial']} ❌{result['error']}")
    
    st.divider()
    
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
    # 1. Header (simplified - progress button moved to sidebar for easier access)
    st.title("🤖 AI Interviewer (Chat Mode)")

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
        
        # Use stable key based on persona only (not time-based)
        uploader_key = f"uploader_{persona}"
        uploaded_refs = st.file_uploader(
            upload_label, 
            type=["pdf", "png", "jpg", "jpeg"], 
            accept_multiple_files=True,
            key=uploader_key
        )
        
        # Show selected files clearly
        if uploaded_refs:
            st.info(f"📎 **{len(uploaded_refs)}件のファイルを選択中**: {', '.join([f.name for f in uploaded_refs])}")
            
            if st.button("🚀 資料を読み込む (Process Files)", key=f"btn_process_{persona}"):
                with st.spinner("資料を解析中..."):
                    try:
                        count = st.session_state.ai_interviewer.process_files(uploaded_refs, target_persona=persona)
                        st.success(f"✅ {count}件の資料を読み込みました！")
                        
                        # Store upload success flag for chat context
                        st.session_state["_last_upload_count"] = count
                        st.session_state["_last_upload_names"] = [f.name for f in uploaded_refs]
                        
                        # --- Agentic Extraction Trigger (File Upload) ---
                        # 資料をアップロードした直後に詳細抽出をかける
                        if count > 0:
                            with st.status("🤖 AI Agent Working: 資料を詳細分析中...", expanded=True) as status:
                                status.write("📝 Gemini 1.5 Pro (High Reasoning) で資料を読み込んでいます...")
                                try:
                                    # 最新のアップロードファイル参照を取得して渡す
                                    all_files = st.session_state.ai_interviewer.uploaded_file_refs
                                    
                                    extracted_data = st.session_state.ai_interviewer.extract_structured_data(text="", file_refs=all_files)
                                    
                                    if extracted_data:
                                        status.write("✅ 構造化データを検出しました。")
                                        status.write("💡 抽出結果は会話コンテキストに保持されました。")
                                    else:
                                        status.write("ℹ️ 新規の構造化データは見つかりませんでした。")
                                except Exception as ex_e:
                                    status.error(f"データ抽出エラー: {ex_e}")
                        
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
    
    # Helper to sanitize content (Shared between history and stream)
    def sanitize_content(text: str) -> str:
        if not text: return ""
        import re
        # 1. Remove <suggestions> tags (Robust regex)
        text = re.sub(r'<\s*suggestions\s*>.*?<\s*/\s*suggestions\s*>', '', text, flags=re.DOTALL)
        # 2. Remove HTML comments (Schema definitions)
        text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
        # 3. Remove raw JSON blocks that look like extraction data
        text = re.sub(r'\{[^{}]*("parameter"|"company_name"|"business_overview")[^{}]*\}', '', text, flags=re.DOTALL)
        # 4. Remove data_for_application xml block
        text = re.sub(r'<\s*data_for_application\s*>.*?<\s*/\s*data_for_application\s*>', '', text, flags=re.DOTALL)
        return text.strip()
    
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
                display_content = sanitize_content(msg["content"])
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
                        st.session_state.auto_trigger_message = example
                        st.rerun()

    # --- Next Action Suggestions (Quick Replies) ---
    # st.caption("👇 クイック返信 (クリックで送信)") -> Removed duplicate
    
    # Prioritize dynamic options
    options = current_suggestions.get("options", [])
    
    # Fallback if no dynamic options - Plan A: Clear start options
    if not options:
        # Check if conversation has started
        has_conversation = len(st.session_state.ai_interviewer.history) > 1
        
        if has_conversation:
            # During conversation - show contextual fallback
            fallback_map = {
                "経営者": ["はい", "いいえ", "詳しく教えてください"],
                "従業員": ["はい", "いいえ", "詳しく教えてください"],
                "商工会職員": ["はい", "いいえ", "詳しく教えてください"]
            }
            options = fallback_map.get(persona, [])
        else:
            # Initial state - Plan A: Simple clear CTAs
            options = ["📋 計画策定を始める", "📂 資料をアップロードして始める"]

    # --- Options Placeholder (UI Improvement from 12/14) ---
    options_placeholder = st.empty()

    def render_options_in_placeholder(placeholder, current_options):
        with placeholder.container():
             # Remove duplicate caption if it exists outside
             if current_options:
                 st.caption("👇 クイック返信 (クリックで送信)")
                 # Ensure horizontal layout - one row
                 cols = st.columns(len(current_options))
                 for idx, opt in enumerate(current_options):
                     with cols[idx]:
                         # Use strict key
                         # Use Markdown coloring for emphasis (Blue Bold)
                         if st.button(f":blue[**{opt}**]", key=f"opt_{idx}_{len(st.session_state.ai_interviewer.history)}", use_container_width=True):
                             st.session_state.auto_trigger_message = opt
                             st.rerun()
    
    # Render Options using new UI
    render_options_in_placeholder(options_placeholder, options)

    # User Input
    # prompt = st.chat_input(f"{persona}として回答を入力...") -> 12/14 uses specific key and logic below

    # Define Mini Dashboard Renderer (UI Improvement from 12/14)
    dashboard_placeholder = st.empty()
    main_chat_container = st.container()

    def render_mini_dashboard_in_placeholder(placeholder):
        # Ensure it renders something even if plan is missing (for debugging/fallback)
        with placeholder.container():
            if "current_plan" in st.session_state and st.session_state.current_plan:
                from src.core.completion_checker import CompletionChecker
                res = CompletionChecker.analyze(st.session_state.current_plan)
                prog = res['mandatory_progress']
                
                # 1. Next Actions (First)
                if res['missing_mandatory']:
                    sec_map = {"BasicInfo": "基本情報", "Goals": "事業概要", "Disaster": "災害想定", "ResponseProcedures": "初動対応", "Measures": "事前対策", "FinancialPlan": "資金計画", "PDCA": "推進体制"}
                    next_items = [sec_map.get(m['section'], m['section']) for m in res['missing_mandatory'][:3]]
                    
                    # Interactive Next Actions
                    st.caption("📌 **テーマを切り替える (クリックで入力を開始):**")
                    cols_next = st.columns(len(next_items))
                    for idx, item in enumerate(next_items):
                        with cols_next[idx]:
                            # Use dynamic key based on history to avoid duplicates
                            hist_len_act = len(st.session_state.ai_interviewer.history) if "ai_interviewer" in st.session_state else 0
                            if st.button(f"📝 {item}", key=f"next_act_{idx}_{hist_len_act}", use_container_width=True):
                                st.session_state.auto_trigger_message = f"{item}の入力を行いたいです。何から始めればよいですか？"
                                st.rerun()
                
                # 2. Progress Bar (Second)
                cols_prog = st.columns([3, 1, 1.5]) # Added column for button
                with cols_prog[0]: st.progress(prog)
                with cols_prog[1]: st.caption(f"**{int(prog*100)}% 完了**")
                with cols_prog[2]:
                    # Use dynamic key to prevent StreamlitDuplicateElementKey when re-rendering in the same run
                    # (Initial Render + In-place Update)
                    hist_len = len(st.session_state.ai_interviewer.history) if "ai_interviewer" in st.session_state else 0
                    if st.button("📊 詳細を確認", key=f"btn_check_prog_dash_{hist_len}", use_container_width=True):
                         change_mode("Dashboard Mode (Progress)")
                         st.rerun()
            else:
                # Debug feedback if plan is missing
                # st.warning("⚠ 事業計画データが見つかりません。")
                pass 

    # Render Dash Initial
    render_mini_dashboard_in_placeholder(dashboard_placeholder)

    # Input Area
    prompt = st.chat_input(f"{persona}として回答を入力...", key="chat_input_main")

    if st.session_state.get("auto_trigger_message"):
        prompt = st.session_state.auto_trigger_message
        st.session_state.auto_trigger_message = None

    if prompt:
        # J-SHIS handling is now done via AI prompt text response (URL and address included in AI output)
        # No special frontend handling needed - AI will include the URL and address as plain text
        final_prompt = prompt
        
        with main_chat_container:
            with st.chat_message("user", avatar="🧑‍🏫" if persona=="商工会職員" else "👤"):
                st.markdown(prompt)

        
        # Prepare metadata for context
        user_name = st.session_state.get("user_name_input", "")
        user_position = st.session_state.get("user_position_input", "")
        user_data = {"name": user_name, "position": user_position}

        # --- Agentic Smart Extraction (Experimental) ---
        if len(final_prompt) > 200 or "資料" in final_prompt:
             with st.status("🤖 AI Agent Working: 情報を抽出中...", expanded=False) as status:
                  status.write("📝 文脈から構造化データを読み取っています (Extracting Facts)...")
                  try:
                      extracted_data = st.session_state.ai_interviewer.extract_structured_data(final_prompt)
                      if extracted_data:
                          status.write("✅ データを検出しました。計画書に反映します。")
                          # Merge Logic (Simplified: Update session state plan)
                          # Merge Logic: Use Helper
                          from src.api.schemas import ApplicationRoot
                          from src.core.merge_helper import deep_merge_plan
                          
                          # Load existing or create new
                          current_obj = st.session_state.get("current_plan")
                          if not current_obj:
                              current_obj = ApplicationRoot()
                          
                          # Perform Deep Merge
                          updated_plan = deep_merge_plan(current_obj, extracted_data)
                          st.session_state.current_plan = updated_plan
                          st.toast("✅ 抽出された情報を計画書に反映しました", icon="📝")
                          
                          # Debug Log (Optional, visible in console)
                          print(f"[SmartExtraction] Merged: {extracted_data.keys()}")
                          
                  except Exception as e:
                      print(f"Extraction failed: {e}")
                      status.update(label="⚠️ Extraction skipped", state="error")

        with st.chat_message("model", avatar="🤖"):
            with st.spinner("AI is thinking..."):
                response = st.session_state.ai_interviewer.send_message(
                    final_prompt, 
                    persona=persona,
                    user_data=user_data
                )
                st.markdown(sanitize_content(response))
                
                # --- Auto-Save Session ---
                current_plan_dict = None
                if "current_plan" in st.session_state and st.session_state.current_plan:
                    current_plan_dict = st.session_state.current_plan.model_dump(mode='json')
                
                st.session_state.session_manager.save_session(
                    history=st.session_state.ai_interviewer.history,
                    current_plan_dict=current_plan_dict
                )
                
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
    
    # Auto-Analyze Logic (User Request: Remove button, auto-run)
    # Check if we need to analyze (e.g. if history changed since last time)
    history_len = len(st.session_state.ai_interviewer.history)
    last_analyzed = st.session_state.get("_last_dashboard_analysis_len", 0)
    
    # Run analysis if there are new messages OR if it's the first load (and we have history)
    # Also ensuring we don't run it if history is empty (nothing to analyze)
    should_analyze = history_len > 0 and (history_len > last_analyzed)

    if should_analyze:
        with st.status("🚀 Auto-Analyzing Chat History...", expanded=True) as status:
            try:
                status.write("⏳ Calling Gemini API for Deep Analysis...")
                extracted_data = st.session_state.ai_interviewer.analyze_history()
                
                status.write(f"✅ Data Type: {type(extracted_data)}")
                
                if extracted_data:
                    status.write("⏳ Merging data into Plan...")
                    from src.core.merge_helper import deep_merge_plan
                    
                    # Safe Merge (Prevent Data Loss)
                    if "current_plan" not in st.session_state:
                         from src.api.schemas import ApplicationRoot
                         st.session_state.current_plan = ApplicationRoot()
                    
                    # Perform Deep Merge
                    st.session_state.current_plan = deep_merge_plan(st.session_state.current_plan, extracted_data)
                    
                    # Update timestamp/flag
                    st.session_state["_last_dashboard_analysis_len"] = history_len
                    
                    status.update(label="🎉 Analysis Complete & Plan Updated!", state="complete", expanded=False)
                    time.sleep(1) # Brief pause to show success
                    st.rerun()

                else:
                    status.update(label="⚠️ No data extracted.", state="complete", expanded=False)
            
            except Exception as e:
                status.update(label=f"❌ Analysis Error: {e}", state="error")
                st.error(f"Details: {e}")
    else:
        if history_len > 0:
            st.caption(f"✅ Analysis up to date (History: {history_len} msgs)")
    
    
    # 解析結果の表示 (Updated for ApplicationRoot key mapping)
    # Ensure plan exists so we can edit it even if analysis hasn't run
    if "current_plan" not in st.session_state:
        from src.api.schemas import ApplicationRoot
        st.session_state.current_plan = ApplicationRoot()
        
    if "current_plan" in st.session_state:
        plan: ApplicationRoot = st.session_state.current_plan
        from src.core.completion_checker import CompletionChecker
        
        # Run Analysis
        result = CompletionChecker.analyze(plan)
        
        # --- Auto-save to LocalStorage ---
        inject_localstorage_autosave()
        
        # --- 1. Status Banner & Header ---
        st.divider()
        st.subheader("📊 Plan Progress Dashboard")
        
        col_m1, col_m2 = st.columns([1, 4])
        with col_m1:
            # Renamed: 認定可能性スコア → 入力進捗度 (to avoid confusion with audit score)
            st.metric(label="📝 入力進捗度", value=f"{result['total_score']}%", help="必須項目の入力完了率")
            
        with col_m2:
            st.caption("必須項目の入力状況 (Mandatory Requirements)")
            st.progress(result['mandatory_progress'])
            st.caption(f"入力完了率: {int(result['mandatory_progress']*100)}%")
        
        # --- History Comparison (WS-4 UI Integration) ---
        try:
            from src.core.history_tracker import HistoryTracker
            history_tracker = HistoryTracker()
            comparison = history_tracker.compare_with_previous(plan, result)
            
            if comparison:
                delta = comparison['change']
                delta_str = f"+{delta}" if delta > 0 else str(delta)
                if delta > 0:
                    st.success(f"📈 前回から **{delta_str}%** 改善しました！")
                elif delta < 0:
                    st.warning(f"📉 前回から **{delta_str}%** 低下しています")
            
            # Save current snapshot for next comparison
            history_tracker.save_snapshot(plan, result)
        except Exception as e:
            pass  # Silent fail if history not available
        
        # --- Task 1: Logic Consistency Warnings (Phase 1 Implementation) ---
        if 'logic_consistency' in result:
            logic_result = result['logic_consistency']
            logic_warnings = logic_result.get('warnings', [])
            logic_suggestions = logic_result.get('suggestions', [])
            consistency_score = logic_result.get('consistency_score', 100)
            
            if logic_warnings or consistency_score < 80:
                with st.expander(f"🔗 セクション間整合性チェック（スコア: {consistency_score}%）", expanded=consistency_score < 70):
                    if consistency_score >= 80:
                        st.success("✅ 整合性は概ね良好です")
                    elif consistency_score >= 50:
                        st.warning("⚠️ 一部の整合性に問題があります")
                    else:
                        st.error("❌ 重要な整合性の問題があります")
                    
                    for warning in logic_warnings:
                        severity = warning.get('severity', 'info')
                        msg = warning.get('message', str(warning))
                        if severity == 'critical':
                            st.error(f"🔴 {msg}")
                        elif severity == 'warning':
                            st.warning(f"🟡 {msg}")
                        else:
                            st.info(f"ℹ️ {msg}")
                    
                    if logic_suggestions:
                        st.markdown("**💡 改善提案:**")
                        for suggestion in logic_suggestions:
                            st.caption(f"・{suggestion}")
            
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
                        st.session_state.auto_trigger_message = (
                            "現在、ダッシュボードで確認した不足項目（focus_fields）について、リストの上から順に一つずつヒアリングしてください。"
                            "基本情報（設立日や法人番号など）が未入力の場合は、最優先で確認してください。"
                            "なお、ユーザーが答えられない場合は「後で確認する」という選択肢も必ず提示し、柔軟にスキップできるようにしてください。"
                        )
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
            # Excel Export - Draft Sheet
            st.caption("📤 **エクスポート**")
            if st.button("📄 下書きシート出力", key="btn_export_draft", use_container_width=True, help="進捗確認用の下書きシート"):
                try:
                    from src.core.draft_exporter import DraftExporter
                    excel_data = DraftExporter.export_to_excel(plan, result)
                    st.download_button(
                        label="⬇️ ダウンロード (下書き)",
                        data=excel_data,
                        file_name=f"jigyokei_draft_{plan.basic_info.corporate_name or 'plan'}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="btn_download_excel_draft"
                    )
                except ImportError as ie:
                     st.error(f"依存ライブラリ不足: {ie}")
                except Exception as e:
                    st.error(f"エクスポートエラー: {e}")
            
            # Excel Export - Application Input (NEW)
            if st.button("📋 電子申請入力用 (Excel)", key="btn_export_app", use_container_width=True, type="primary", help="電子申請システムへのコピペ用"):
                try:
                    from src.core.draft_exporter import DraftExporter
                    excel_data = DraftExporter.export_for_application(plan)
                    st.download_button(
                        label="⬇️ ダウンロード (入力用)",
                        data=excel_data,
                        file_name=f"jigyokei_application_{plan.basic_info.corporate_name or 'plan'}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="btn_download_excel_app"
                    )
                    st.success("✅ 黄色のセルをコピーして電子申請システムに貼り付けてください")
                except ImportError as ie:
                     st.error(f"依存ライブラリ不足: {ie}")
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

        # --- Audit Section (Explicit Button) ---
        with col_exp1:
            st.subheader("🔍 認定品質監査 (AI審査官)")
            st.caption("⚠️ 本スコアは参考値であり、認定を保証するものではありません。最終的な認定可否は審査機関の判断によります。")
            
            if st.button("🚀 監査を実行する", key="btn_run_audit", type="primary", use_container_width=True):
                with st.spinner("AI審査官が申請書を評価中..."):
                    try:
                        from src.core.audit_agent import AuditAgent
                        
                        agent = AuditAgent()
                        app_text = agent.format_application_for_audit(plan)
                        audit_result = agent.audit(app_text)
                        
                        st.session_state["_last_audit_result"] = audit_result
                        
                    except Exception as e:
                        st.error(f"監査エラー: {e}")
            
            # Display cached audit result
            if "_last_audit_result" in st.session_state:
                audit_result = st.session_state["_last_audit_result"]
                
                # Score display
                score_color = "red" if audit_result.total_score < 50 else "orange" if audit_result.total_score < 70 else "green"
                st.markdown(f"### 監査スコア: :{score_color}[**{audit_result.total_score}点 / 100点**]")
                
                # Section breakdown with max scores
                if audit_result.sections:
                    # Define max scores for each section
                    max_scores = {
                        "災害想定": 20, "事業影響": 20, "初動対応": 15,
                        "事前対策": 15, "PDCA体制": 15, "事業概要": 10, "基本情報": 5
                    }
                    
                    with st.expander("📊 セクション別評価", expanded=True):
                        for sec in audit_result.sections:
                            max_score = max_scores.get(sec.name, 10)
                            is_full = sec.score >= max_score
                            status_icon = "✅" if is_full else "⚠️" if sec.score >= max_score * 0.5 else "❌"
                            
                            col_s1, col_s2 = st.columns([3, 1])
                            with col_s1:
                                st.write(f"**{sec.name}**: {sec.reason}")
                            with col_s2:
                                # Show X / Y format with status
                                st.markdown(f"**{sec.score} / {max_score}点** {status_icon}")
                
                # Improvements
                if audit_result.improvements:
                    with st.expander("💡 改善提案", expanded=True):
                        for i, imp in enumerate(audit_result.improvements, 1):
                            st.warning(f"{i}. {imp}")

        # --- Attachments Checklist Section ---
        st.divider()
        with st.expander("📎 添付書類・誓約事項チェックリスト", expanded=False):
            st.caption("電子申請の最終確認事項です。すべてにチェックが必要です。")
            
            # Get or initialize attachments
            att = plan.attachments
            
            col_att1, col_att2 = st.columns(2)
            
            with col_att1:
                st.markdown("**必須確認事項**")
                
                # Certification compliance
                new_cert = st.checkbox(
                    "認定要件への適合を確認しました", 
                    value=att.certification_compliance or False,
                    key="chk_cert_compliance"
                )
                if new_cert != att.certification_compliance:
                    plan.attachments.certification_compliance = new_cert
                
                # No false statements
                new_nofalse = st.checkbox(
                    "虚偽の記載がないことを確認しました",
                    value=att.no_false_statements or False,
                    key="chk_no_false"
                )
                if new_nofalse != att.no_false_statements:
                    plan.attachments.no_false_statements = new_nofalse
                
                # Not anti-social
                new_antisocial = st.checkbox(
                    "反社会的勢力ではないことを確認しました",
                    value=att.not_anti_social or False,
                    key="chk_not_antisocial"
                )
                if new_antisocial != att.not_anti_social:
                    plan.attachments.not_anti_social = new_antisocial
                
                # Legal compliance
                new_legal = st.checkbox(
                    "法令に適合していることを確認しました",
                    value=att.legal_compliance or False,
                    key="chk_legal"
                )
                if new_legal != att.legal_compliance:
                    plan.attachments.legal_compliance = new_legal
            
            with col_att2:
                st.markdown("**追加確認事項**")
                
                # SME requirements
                new_sme = st.checkbox(
                    "中小企業者の要件を満たしています",
                    value=att.sme_requirements or False,
                    key="chk_sme"
                )
                if new_sme != att.sme_requirements:
                    plan.attachments.sme_requirements = new_sme
                
                # Registration consistency
                new_reg = st.checkbox(
                    "登記情報と一致しています",
                    value=att.registration_consistency or False,
                    key="chk_registration"
                )
                if new_reg != att.registration_consistency:
                    plan.attachments.registration_consistency = new_reg
                
                # Not cancellation subject
                new_cancel = st.checkbox(
                    "認定取消対象ではありません",
                    value=att.not_cancellation_subject or False,
                    key="chk_not_cancel"
                )
                if new_cancel != att.not_cancellation_subject:
                    plan.attachments.not_cancellation_subject = new_cancel
            
            # Count completed checks
            checks = [
                att.certification_compliance, att.no_false_statements, att.not_anti_social,
                att.legal_compliance, att.sme_requirements, att.registration_consistency,
                att.not_cancellation_subject
            ]
            completed = sum(1 for c in checks if c)
            total = len(checks)
            
            st.divider()
            if completed == total:
                st.success(f"✅ すべての確認事項が完了しています ({completed}/{total})")
            else:
                st.warning(f"⚠️ 未完了の確認事項があります ({completed}/{total})")

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
        if "Disaster" in missing_sections: tabs_labels["Disaster"] += " ⚠️"  # Changed to specific Disaster section check
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
        
        # TAB 1: Basic Info (Editable)
        with tab1:
            st.caption("📋 様式第1 基本情報 (編集可能)")
            if plan.basic_info:
                bi = plan.basic_info
                
                # --- Auto-Address Logic ---
                def on_zip_change():
                    # Get value directly from session state key
                    z_val = st.session_state.get("bi_input_zip", "")
                    addr = fetch_address_from_zip(z_val)
                    if addr:
                        plan.basic_info.address_zip = z_val # Update model
                        plan.basic_info.address_pref = addr["pref"]
                        plan.basic_info.address_city = addr["city"]
                        plan.basic_info.address_street = addr["town"]
                        
                        # Explicitly update widget state to reflect changes
                        st.session_state["bi_input_pref"] = addr["pref"]
                        st.session_state["bi_input_city"] = addr["city"]
                        st.session_state["bi_input_street"] = addr["town"]
                        
                        st.toast(f"住所を自動入力しました: {addr['pref']}{addr['city']}{addr['town']}", icon="✅")
                    else:
                        plan.basic_info.address_zip = z_val # Update model even if not found
                        
                # --------------------------

                with st.container(border=True):
                    st.caption("企業概要")
                    c1, c2 = st.columns(2)
                    bi.corporate_name = c1.text_input("企業名", value=bi.corporate_name or "", key="bi_input_corp")
                    bi.corporate_number = c2.text_input("法人番号", value=bi.corporate_number or "", key="bi_input_num")
                    
                    c3, c4 = st.columns(2)
                    bi.representative_title = c3.text_input("役職", value=bi.representative_title or "", placeholder="代表取締役", key="bi_input_pos")
                    bi.representative_name = c4.text_input("代表者名", value=bi.representative_name or "", key="bi_input_rep")

                    st.divider()
                    st.caption("所在地 (郵便番号から自動入力)")
                    
                    z_col, p_col = st.columns([1, 2])
                    # Zip Code Input with Callback
                    z_col.text_input("郵便番号 (7桁)", value=bi.address_zip or "", key="bi_input_zip", on_change=on_zip_change, help="ハイフンあり・なし両対応。入力後にEnterで住所を自動補完します。")
                    
                    bi.address_pref = p_col.text_input("都道府県", value=bi.address_pref or "", key="bi_input_pref")
                    
                    c5, c6 = st.columns(2)
                    bi.address_city = c5.text_input("市区町村", value=bi.address_city or "", key="bi_input_city")
                    bi.address_street = c6.text_input("町域・番地", value=bi.address_street or "", key="bi_input_street")
                    
                    bi.address_building = st.text_input("ビル名・階数", value=bi.address_building or "", key="bi_input_bld")
                
                with st.expander("その他の詳細情報 (資本金・従業員数など)"):
                    c7, c8 = st.columns(2)
                    # For integers, use number_input or text_input with conversion
                    cap_input = c7.text_input("資本金 (円)", value=str(bi.capital) if bi.capital else "", key="bi_input_cap")
                    if cap_input.isdigit(): bi.capital = int(cap_input)
                    
                    emp_input = c8.text_input("従業員数 (名)", value=str(bi.employees) if bi.employees else "", key="bi_input_emp")
                    if emp_input.isdigit(): bi.employees = int(emp_input)
                    
                    c9, c10 = st.columns(2)
                    bi.establishment_date = c9.text_input("設立年月日", value=bi.establishment_date or "", placeholder="YYYY-MM-DD", key="bi_input_est")
                    
                    ind_major = c10.text_input("大分類 (業種)", value=bi.industry_major or "", key="bi_input_ind_maj")
                    bi.industry_major = ind_major

                with st.expander("📌 認定レベルの記載例 (基本情報)"):
                    st.success("**法人番号の例**:\n13桁の法人番号（国税庁指定）を正確に記載します。法人番号公表サイトで確認できます。")
                    st.info("**業種の例**:\n日本標準産業分類に基づく大分類コードを記載（例：08 設備工事業、56 宿泊業）")
                    st.warning("**ポイント**: 資本金・従業員数は正確に記載。決算書類と一致させること。")

            else:
                with st.container(border=True):
                    st.warning("⚠️ 基本情報オブジェクトが初期化されていません。")
        
        # Helper to get missing messages for a section
        def get_missing_msgs(section_id):
            return [m['msg'] for m in result['missing_mandatory'] if m['section'] == section_id]

        # TAB 2: Overview & Goals
        with tab2:
            st.caption("📋 様式第2 事業活動の概要・取組目的")
            
            with st.container(border=True):
                st.subheader("事業活動の概要")
                if plan.goals.business_overview:
                    st.info(plan.goals.business_overview)
                    # Character count check
                    char_count = len(plan.goals.business_overview)
                    if char_count < 200:
                        st.warning(f"⚠️ 事業概要が短いです（現在 {char_count} 文字）。認定申請には **200文字以上** を推奨します。")
                    else:
                        st.caption(f"✅ 文字数: {char_count} 文字（推奨: 200文字以上）")
                
                # Show specific errors
                msgs = get_missing_msgs("Goals")
                # Filter for "概要" related
                overview_errs = [m for m in msgs if "概要" in m]
                for err in overview_errs:
                     st.warning(f"⚠️ {err}")
                
                if not plan.goals.business_overview and not overview_errs:
                     st.error("🚨 事業活動の概要が未入力です。")

            with st.container(border=True):
                st.subheader("取組目的")
                if plan.goals.business_purpose:
                    st.info(plan.goals.business_purpose)
                
                # Filter for "目的" related
                purpose_errs = [m for m in msgs if "目的" in m]
                for err in purpose_errs:
                    st.warning(f"⚠️ {err}")
                
                if not plan.goals.business_purpose and not purpose_errs:
                     st.warning("⚠️ 取組目的が未入力です。")

            with st.expander("📌 認定レベルの記載例 (事業概要・目的)"):
                st.success("**事業概要の例**:\n当社は地域で唯一の〇〇製造業者であり、サプライチェーンにおいて不可欠な部品供給を担っている。")
                st.info("**取組目的の例**:\n従業員の安全確保を最優先とし、被災時も早期に供給責任を果たすことで、取引先の操業停止を防ぐ。")
            
            # Auto-refinement for Business Overview (Tab 2 doesn't have a specific prompt, use general)
            if plan.goals.business_overview and len(plan.goals.business_overview) > 10:
                if st.button("✨ 事業概要を認定レベルに自動改善", key="btn_refine_overview", type="secondary"):
                    with st.spinner("AIが事業概要を改善中..."):
                        try:
                            from src.core.auto_refinement import AutoRefinementAgent
                            import google.generativeai as genai
                            
                            # Custom prompt for business overview
                            prompt = f'''事業継続力強化計画の「事業概要」を認定レベルに改善してください。

【改善ポイント】
1. サプライチェーン上の役割を明記
2. 地域経済における重要性を説明
3. 取引先・顧客への影響を具体化
4. **必ず200文字以上にすること**（認定申請の推奨文字数）

【入力テキスト】
{plan.goals.business_overview}

【出力形式】JSON形式で出力:
{{"refined_text": "改善後テキスト（200文字以上）", "improvements_made": ["改善点1"], "confidence_score": 85}}
'''
                            agent = AutoRefinementAgent()
                            model = agent._get_model()
                            response = model.generate_content(prompt)
                            import json
                            result_data = json.loads(response.text)
                            
                            st.session_state["_refined_overview"] = result_data
                            st.success(f"✅ 改善完了 (信頼度: {result_data.get('confidence_score', 50)}%)")
                        except Exception as e:
                            st.error(f"改善エラー: {e}")
                
                if "_refined_overview" in st.session_state:
                    refined = st.session_state["_refined_overview"]
                    with st.container(border=True):
                        st.markdown("### 📝 改善後のテキスト")
                        st.info(refined.get("refined_text", ""))
                        st.caption("**改善点:**")
                        for imp in refined.get("improvements_made", []):
                            st.caption(f"  • {imp}")
                        
                        col_apply, col_cancel = st.columns(2)
                        if col_apply.button("✅ この内容を適用", key="btn_apply_overview"):
                            plan.goals.business_overview = refined.get("refined_text", plan.goals.business_overview)
                            del st.session_state["_refined_overview"]
                            st.rerun()
                        if col_cancel.button("❌ キャンセル", key="btn_cancel_overview"):
                            del st.session_state["_refined_overview"]
                            st.rerun()
        
        # TAB 3: Disaster Scenario
        with tab3:
            st.caption("📋 様式第3 事業活動に影響を与える自然災害等の想定")
            
            with st.container(border=True):
                st.subheader("想定する自然災害等")
                if plan.goals.disaster_scenario.disaster_assumption and plan.goals.disaster_scenario.disaster_assumption != "未設定":
                    st.info(plan.goals.disaster_scenario.disaster_assumption)
                    
                    # J-SHIS validation check
                    try:
                        from src.core.jshis_helper import get_missing_requirements
                        missing_reqs = get_missing_requirements(plan.goals.disaster_scenario.disaster_assumption)
                        if missing_reqs:
                            st.warning("⚠️ **認定要件の不足** - 以下の記載が不足しています：")
                            for req in missing_reqs:
                                st.caption(f"  • {req}")
                        else:
                            st.success("✅ J-SHIS認定レベルの記載要件を満たしています")
                    except ImportError:
                        pass  # Module not available
                
                # Specific errors
                msgs = get_missing_msgs("Disaster")
                for err in msgs:
                    st.error(f"🚨 {err}")
            
            # New Impact Structure Display
            st.subheader("自然災害等の発生が事業活動に与える影響")
            imp = plan.goals.disaster_scenario.impacts
            
            with st.expander("📌 認定レベルの記載例 (想定・影響)"):
                st.success("**災害想定の例**:\n今後30年以内に震度6弱以上の地震が発生する確率が72.3％（J-SHIS地図参照）")
                st.info("**事業影響の例**:\n本館建物の損壊により、宿泊客等の受入が不可能となり、全ての営業が停止することが想定される。")
            
            # Auto-refinement button for Disaster Assumption
            if plan.goals.disaster_scenario.disaster_assumption and len(plan.goals.disaster_scenario.disaster_assumption) > 10:
                if st.button("✨ 災害想定を認定レベルに自動改善", key="btn_refine_disaster", type="secondary"):
                    with st.spinner("AIが災害想定を改善中..."):
                        try:
                            from src.core.auto_refinement import refine_text
                            result = refine_text("disaster_assumption", plan.goals.disaster_scenario.disaster_assumption)
                            if result.confidence_score > 0:
                                st.session_state["_refined_disaster"] = result
                                st.success(f"✅ 改善完了 (信頼度: {result.confidence_score}%)")
                            else:
                                st.error(result.improvements_made[0] if result.improvements_made else "改善に失敗しました")
                        except Exception as e:
                            st.error(f"改善エラー: {e}")
                
                # Show refined result if available
                if "_refined_disaster" in st.session_state:
                    refined = st.session_state["_refined_disaster"]
                    with st.container(border=True):
                        st.markdown("### 📝 改善後のテキスト")
                        st.info(refined.refined_text)
                        st.caption("**改善点:**")
                        for imp in refined.improvements_made:
                            st.caption(f"  • {imp}")
                        
                        col_apply, col_cancel = st.columns(2)
                        if col_apply.button("✅ この内容を適用", key="btn_apply_disaster"):
                            plan.goals.disaster_scenario.disaster_assumption = refined.refined_text
                            del st.session_state["_refined_disaster"]
                            st.rerun()
                        if col_cancel.button("❌ キャンセル", key="btn_cancel_disaster"):
                            del st.session_state["_refined_disaster"]
                            st.rerun()


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
            
            # Specific errors
            msgs = get_missing_msgs("ResponseProcedures")
            for err in msgs:
                st.error(f"🚨 {err}")
            
            with st.expander("📌 認定レベルの記載例 (初動対応)"):
                st.success("""**初動対応3項目の例**:
1. **人命の安全確保**: 従業員の避難誘導、安否確認システムによる全員確認
2. **非常時の緊急時体制の構築**: 代表取締役を本部長とした災害対策本部の設置
3. **被害状況の把握・被害情報の共有**: 施設・設備の目視確認、取引先・自治体への報告""")
                st.warning("""**事前対策の欄（preparation_content）が必須**:
12/17改修により、各初動対応項目に「事前対策の内容」を記載することが必須になりました。
例：「避難場所・避難経路を予め確認し、年1回避難訓練を実施する」""")
                st.info("""**発災直後と事前対策を明確に分離**:
- 発災直後：「揺れがおさまった後、全員で避難」
- 事前対策：「避難場所の周知、定期訓練の実施」""")
            
            # Auto-refinement for Response Procedures
            if plan.response_procedures:
                response_text = "\n".join([f"{p.category}: {p.action_content}" for p in plan.response_procedures if p.action_content])
                if len(response_text) > 10:
                    if st.button("✨ 初動対応を認定レベルに自動改善", key="btn_refine_response", type="secondary"):
                        with st.spinner("AIが初動対応を改善中..."):
                            try:
                                from src.core.auto_refinement import refine_text
                                result = refine_text("response_procedures", response_text)
                                if result.confidence_score > 0:
                                    st.session_state["_refined_response"] = result
                                    st.success(f"✅ 改善完了 (信頼度: {result.confidence_score}%)")
                                else:
                                    st.error(result.improvements_made[0] if result.improvements_made else "改善に失敗しました")
                            except Exception as e:
                                st.error(f"改善エラー: {e}")
                    
                    if "_refined_response" in st.session_state:
                        refined = st.session_state["_refined_response"]
                        with st.container(border=True):
                            st.markdown("### 📝 改善後のテキスト")
                            st.info(refined.refined_text)
                            st.caption("**改善点:**")
                            for imp in refined.improvements_made:
                                st.caption(f"  • {imp}")
                            
                            if st.button("❌ 閉じる", key="btn_cancel_response"):
                                del st.session_state["_refined_response"]
                                st.rerun()
        
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
            
            # Specific errors
            msgs = get_missing_msgs("Measures")
            for err in msgs:
                st.error(f"🚨 {err}")
            
            with st.expander("📌 認定レベルの記載例 (事前対策)"):
                st.success("""**A: 人員体制の整備（ヒト）の例**:
- 現在の取組：多能工化を進め、代替要員を確保している
- 今後の計画：外部研修への参加、スキルマップの整備""")
                st.info("""**B: 建物・設備の保全（モノ）の例**:
- 現在の取組：キャビネットの転倒防止器具を設置済み
- 今後の計画：バックアップ電源（UPS）の導入""")
                st.warning("""**C: 資金調達手段の確保（カネ）の例**:
- 現在の取組：火災保険・地震保険に加入済
- 今後の計画：当座の運転資金として〇ヶ月分を確保""")
                st.info("""**D: 情報の保護（情報）の例**:
- 現在の取組：クラウドバックアップを週次で実施
- 今後の計画：顧客データの外部保管体制構築""")
            
            # Auto-refinement for Measures
            measures_text = f"""
人員: {measures.personnel.current_measure or ''} / {measures.personnel.future_plan or ''}
建物: {measures.building.current_measure or ''} / {measures.building.future_plan or ''}
資金: {measures.money.current_measure or ''} / {measures.money.future_plan or ''}
情報: {measures.data.current_measure or ''} / {measures.data.future_plan or ''}
"""
            if len(measures_text.strip()) > 20:
                if st.button("✨ 事前対策を認定レベルに自動改善", key="btn_refine_measures", type="secondary"):
                    with st.spinner("AIが事前対策を改善中..."):
                        try:
                            from src.core.auto_refinement import refine_text
                            result = refine_text("measures", measures_text)
                            if result.confidence_score > 0:
                                st.session_state["_refined_measures"] = result
                                st.success(f"✅ 改善完了 (信頼度: {result.confidence_score}%)")
                            else:
                                st.error(result.improvements_made[0] if result.improvements_made else "改善に失敗しました")
                        except Exception as e:
                            st.error(f"改善エラー: {e}")
                
                if "_refined_measures" in st.session_state:
                    refined = st.session_state["_refined_measures"]
                    with st.container(border=True):
                        st.markdown("### 📝 改善後のテキスト")
                        st.info(refined.refined_text)
                        st.caption("**改善点:**")
                        for imp in refined.improvements_made:
                            st.caption(f"  • {imp}")
                        
                        if st.button("❌ 閉じる", key="btn_cancel_measures"):
                            del st.session_state["_refined_measures"]
                            st.rerun()


        
        # TAB 6: Finance & PDCA
        with tab6:
            st.caption("📋 様式第6 資金計画・推進体制")
            
            with st.container(border=True):
                st.subheader("💰 資金計画")
                if plan.financial_plan.items:
                    st.table([i.model_dump() for i in plan.financial_plan.items])
                
                # Specific errors
                msgs = get_missing_msgs("FinancialPlan")
                for err in msgs:
                    st.error(f"🚨 {err}")
            
            with st.container(border=True):
                st.subheader("🛠️ 設備リスト (税制優遇) (任意)")
                if plan.equipment.items:
                    st.table([i.model_dump() for i in plan.equipment.items])
                else:
                    st.info("設備リストなし (任意)")
            
            with st.container(border=True):
                st.subheader("🔄 推進体制・訓練 (12/17対応)")
                
                # Management System
                plan.pdca.management_system = st.text_area("平時の推進体制", value=plan.pdca.management_system or "", placeholder="例：代表取締役の指揮の下で、担当者が年1回の会議を開催する...", key="pdca_input_mgmt")
                
                # Training & Month
                c1, c2 = st.columns([3, 1])
                plan.pdca.training_education = c1.text_area("訓練・教育の実施計画", value=plan.pdca.training_education or "", placeholder="例：全従業員を対象とした安否確認訓練及び避難訓練...", key="pdca_input_train")
                plan.pdca.training_month = c2.number_input("実施月 (1-12)", min_value=1, max_value=12, value=plan.pdca.training_month or 1, key="pdca_input_train_month")
                
                # Review & Month
                c3, c4 = st.columns([3, 1])
                plan.pdca.plan_review = c3.text_area("計画の見直し計画", value=plan.pdca.plan_review or "", placeholder="例：訓練結果を踏まえ、毎年1回計画を見直す...", key="pdca_input_review")
                plan.pdca.review_month = c4.number_input("見直し月 (1-12)", min_value=1, max_value=12, value=plan.pdca.review_month or 1, key="pdca_input_review_month")
                
                # Internal Publicity (12/17 New Field)
                plan.pdca.internal_publicity = st.text_area("取組の社内周知 (12/17新設)", value=plan.pdca.internal_publicity or "", placeholder="例：計画書を社内ポータルに掲示し、朝礼で周知を行う...", key="pdca_input_pub")
                
                with st.expander("📌 認定レベルの記載例 (お作法)"):
                    st.success("**教育及び訓練の例**:\n毎年◯月に**教育及び訓練**を実施し、防災知識の向上と初動対応の習熟を図る。")
                    st.info("**社内周知の例**:\n策定した計画を全従業員に配付するとともに、掲示板への提示や朝礼での説明を通じて周知を徹底する。")

                # Specific errors
                msgs = get_missing_msgs("PDCA")
                for err in msgs:
                    st.error(f"🚨 {err}")
                
                # 12/17 新設必須項目チェック
                if not plan.pdca.training_month:
                    st.warning("⚠️ 訓練月が未設定です（年1回以上の実施月を指定してください）")
                if not plan.pdca.review_month:
                    st.warning("⚠️ 見直し月が未設定です（年1回以上の見直し月を指定してください）")
                if not plan.pdca.internal_publicity or len(plan.pdca.internal_publicity) < 10:
                    st.error("🚨 **社内周知方法（12/17新設必須）** が未入力です。認定に必須の項目です。")
                
                # Auto-refinement for PDCA
                pdca_text = f"{plan.pdca.training_education or ''} {plan.pdca.internal_publicity or ''}"
                if len(pdca_text.strip()) > 10:
                    if st.button("✨ PDCA体制を認定レベルに自動改善", key="btn_refine_pdca", type="secondary"):
                        with st.spinner("AIがPDCA体制を改善中..."):
                            try:
                                from src.core.auto_refinement import refine_text
                                result = refine_text("pdca", pdca_text)
                                if result.confidence_score > 0:
                                    st.session_state["_refined_pdca"] = result
                                    st.success(f"✅ 改善完了 (信頼度: {result.confidence_score}%)")
                                else:
                                    st.error(result.improvements_made[0] if result.improvements_made else "改善に失敗しました")
                            except Exception as e:
                                st.error(f"改善エラー: {e}")
                    
                    # Show refined result
                    if "_refined_pdca" in st.session_state:
                        refined = st.session_state["_refined_pdca"]
                        with st.container(border=True):
                            st.markdown("### 📝 改善後のテキスト")
                            st.info(refined.refined_text)
                            st.caption("**改善点:**")
                            for imp in refined.improvements_made:
                                st.caption(f"  • {imp}")
                            
                            col_apply, col_cancel = st.columns(2)
                            if col_apply.button("✅ この内容を適用", key="btn_apply_pdca"):
                                plan.pdca.training_education = refined.refined_text
                                del st.session_state["_refined_pdca"]
                                st.rerun()
                            if col_cancel.button("❌ キャンセル", key="btn_cancel_pdca"):
                                del st.session_state["_refined_pdca"]
                                st.rerun()


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
