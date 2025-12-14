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

# --- Check Reset Status ---
if "action" in st.query_params and st.query_params["action"] == "reset":
    st.toast("🗑️ データをリセットしました (Reset Complete)", icon="✅")
    st.query_params.clear()

# --- Custom CSS for Mobile UI ---
st.markdown("""
<style>
    /* Customize Sidebar Toggle (Expanded/Collapsed Control) */
    /* Target Desktop Collapsed Control */
    [data-testid="stSidebarCollapsedControl"] {
        background-color: #ffeaea !important; 
        border: 2px solid #ff4b4b !important;
        border-radius: 8px !important;
        padding: 2px !important;
        width: 44px !important;
        height: auto !important;
        min_height: 80px !important; /* Make it tall and noticeable */
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        z-index: 1000002 !important; /* Higher than Streamlit header overlay */
        opacity: 1 !important;
        visibility: visible !important;
    }

    /* Target Mobile Header Button (Often behaves differently) */
    @media (max-width: 768px) {
        /* On mobile, the toggle might be in the header. 
           We target the first button in the header if specific ID fails, 
           NOTE: Streamlit mobile often uses stSidebarCollapsedControl even in header, 
           but sometimes it is just a button in stHeader. */
        
        [data-testid="stHeader"] button[data-testid="stSidebarCollapsedControl"] {
             background-color: #ffeaea !important;
             border: 2px solid #ff4b4b !important;
             width: auto !important; /* Allow width to expand for text */
             height: auto !important;
             min-height: 44px !important;
             aspect-ratio: auto !important;
             border-radius: 8px !important;
        }
        
        /* Adjust text for mobile (Horizontal 'メニュー') */
        [data-testid="stHeader"] button[data-testid="stSidebarCollapsedControl"]::after {
            content: "メニュー" !important;
            writing-mode: horizontal-tb !important;
            font-size: 16px !important;
            padding: 0 8px !important;
            letter-spacing: 1px !important;
        }
    }

    /* Hide the default '>>' or 'hamburger' icon */
    [data-testid="stSidebarCollapsedControl"] svg, 
    [data-testid="stSidebarCollapsedControl"] img {
        display: none !important;
    }
    
    /* Add 'メニュー' label (Default Vertical for Desktop Sidebar) */
    [data-testid="stSidebarCollapsedControl"]::after {
        content: "メニュー";
        font-family: "Hiragino Sans", "Meiryo", sans-serif;
        font-size: 14px !important;
        font-weight: 900 !important;
        color: #ff4b4b !important;
        writing-mode: vertical-rl;
        text-orientation: upright;
        letter-spacing: 2px;
        white-space: nowrap;
        display: block !important;
    }

    /* --- Sidebar Close Button Improvement --- */
    /* Target the close button inside the sidebar (header button) */
    section[data-testid="stSidebar"] button[kind="header"],
    section[data-testid="stSidebar"] [data-testid="stBaseButton-header"] {
        visibility: visible !important;
        opacity: 1 !important;
        background-color: #ffeaea !important;
        border: 2px solid #ff4b4b !important;
        border-radius: 8px !important;
        color: #ff4b4b !important; /* Icon color */
        min-width: 44px !important;
        min-height: 44px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin-right: 10px !important; /* Spacing from edge */
        transition: none !important; /* Remove fade effect */
    }

    /* Add "閉じる" Label */
    section[data-testid="stSidebar"] button[kind="header"]::before,
    section[data-testid="stSidebar"] [data-testid="stBaseButton-header"]::before {
        content: "閉じる" !important;
        font-size: 12px !important;
        font-weight: bold !important;
        color: #ff4b4b !important;
        margin-right: 4px !important;
        display: inline-block !important;
    }
    
    /* Ensure icon is visible */
    section[data-testid="stSidebar"] button[kind="header"] svg,
    section[data-testid="stSidebar"] [data-testid="stBaseButton-header"] svg {
        display: block !important;
        font-weight: bold !important;
    }
""", unsafe_allow_html=True)

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

from src.core.jigyokei_core import AIInterviewer
from src.data.context_loader import ContextLoader
from src.core.completion_checker import CompletionChecker
from src.core.session_manager import SessionManager

# --- Version Control ---
APP_VERSION = "3.4.2-mobile-ui-polish"

# Initialize Session Manager
if "session_manager" not in st.session_state:
    st.session_state.session_manager = SessionManager()

# --- Auto Resume Logic ---
# [DISABLED] Automatic loading of shared session file causes data leak between users in Cloud environment.
# Note: Mobile persistence is handled via scoped 'mobile_autosave' logic below.


if "app_version" not in st.session_state or st.session_state.app_version != APP_VERSION:
    st.session_state.clear()
    st.session_state.app_version = APP_VERSION
    st.rerun()

# --- Debug / Reset Controls ---
with st.sidebar:
    with st.expander("🔧 System Menu", expanded=False):
        if st.button("🗑️ Reset All Data", key="btn_hard_reset", type="primary", help="警告: すべてのデータを削除して初期化します"):
            # 1. Clear persistence (Disk)
            if "session_manager" in st.session_state:
                st.session_state.session_manager.clear_session()
            
            # 2. Clear Session State (Memory)
            st.session_state.clear()
            
            # 3. Notification & Rerun
            # We set a query param to show the toast after reload
            st.query_params["action"] = "reset"
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
        time.sleep(5)
        st.rerun()

if "context_loader" not in st.session_state:
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    context_dir = os.path.join(root_dir, "data", "context")
    st.session_state.context_loader = ContextLoader(context_dir)

# --- Helper: Auto-Save ---
def perform_auto_save():
    """
    Save the current session state (history & plan) to local storage.
    Used for mobile persistence and crash recovery.
    """
    if "session_manager" in st.session_state and "ai_interviewer" in st.session_state:
        # Prepare plan data if exists
        plan_data = None
        if "current_plan" in st.session_state and st.session_state.current_plan:
            try:
                plan_data = st.session_state.current_plan.model_dump()
            except:
                pass # Fail silently on serialization

        # Save to 'mobile_autosave' slot
        st.session_state.session_manager.save_session(
            history=st.session_state.ai_interviewer.history,
            current_plan_dict=plan_data,
            session_id="mobile_autosave"
        )

# --- Incremental Update Logic (Smart Mapper & Deep Merge) ---
class SmartUpdateMapper:
    """
    Translates simplified AI update JSON into strict Pydantic Schema structure.
    Allows AI to use simple keys like 'human_safety' instead of complex list objects.
    """
    @staticmethod
    def map_response_procedures(simple_dict):
        """Maps flat keys to ResponseProcedures list items."""
        mapped_items = []
        
        # Mapping Rules: Simple Key -> (Category, Action Content)
        # Note: We append to existing likely, or overwrite specific categories?
        # Strategy: We construct objects. Merging logic handles the rest? 
        # No, replacing list items by category is hard with deep_merge.
        # Strategy: Return a LIST of dicts that matches the structure. 
        # But deep_update on lists usually appends or overwrites index. 
        # HACK: We will load current plan, find the matching item, and update its content.
        
        # Actually, let's just return the logic for `apply_incremental_update` to handle.
        # This mapper will return a "Standardized Dict" that matches the Schema structure
        # as much as possible, or return specific instructions.
        pass

def deep_update(base_dict, update_dict):
    """Recursively update dict."""
    import collections.abc
    for k, v in update_dict.items():
        if isinstance(v, collections.abc.Mapping):
            base_dict[k] = deep_update(base_dict.get(k, {}), v)
        else:
            base_dict[k] = v
    return base_dict

def apply_incremental_update(update_json):
    """
    Apply a partial JSON update with Smart Mapping.
    """
    try:
        if "current_plan" not in st.session_state or not st.session_state.current_plan:
             from src.api.schemas import ApplicationRoot
             st.session_state.current_plan = ApplicationRoot()
        
        plan = st.session_state.current_plan
        
        # --- SMART MAPPING LOGIC (Manual Handling for Complex Lists) ---
        
        # 1. Response Procedures (List handling)
        if "response_procedures" in update_json:
            rp_data = update_json["response_procedures"]
            # Map simplified keys to specific list items
            # We assume the plan already has the 4 fixed items (initialized or empty)
            # If not, we create them? Schema defaults to empty list. 
            # Better to find by category or create.
            
            # Helper to find or create
            def update_proc(category, content):
                # Find existing
                found = False
                if not plan.response_procedures: plan.response_procedures = []
                for p in plan.response_procedures:
                    if p.category == category:
                        p.action_content = content
                        found = True
                        break
                if not found:
                    from src.api.schemas import FirstResponse
                    plan.response_procedures.append(FirstResponse(category=category, action_content=content, timing="発災直後"))

            if isinstance(rp_data, dict):
                if "human_safety" in rp_data:
                    # Split into Evacuation and Confirmation? AI prompt said "human_safety" as one?
                    # Wait, prompt example showed output splitting? 
                    # Actually prompt example in previous turn showed: 
                    # "human_safety": "..." (Combined?)
                    # If combined, we might put same content in both or ask AI to split?
                    # Let's put in 'Evacuation' for now or split if clear.
                    txt = rp_data["human_safety"]
                    update_proc("1. 人命の安全確保", txt) 
                    # ideally we want specific keys. Prompt update will enforce 'evacuation' and 'safety_check' keys next.
                    
                if "evacuation" in rp_data: update_proc("1. 人命の安全確保", rp_data["evacuation"]) # Specific
                if "safety_check" in rp_data: update_proc("1. 人命の安全確保", rp_data["safety_check"]) # Specific (needs differentiating? Category name is same)
                # Actually Schema allows duplicate Category names. 
                # To distinguish: We check content or rely on order? 
                # Let's just update the *first* match for 'Evacuation' and *second* for 'Safety Check' if strictly ordered?
                # Risky. 
                # SAFER STRATEGY: Update Prompt to use EXACT keys matching Schema is best, 
                # BUT user wants "Simple".
                # Let's map "emergency_structure" -> "2. 非常時の緊急時体制の構築"
                if "emergency_structure" in rp_data: update_proc("2. 非常時の緊急時体制の構築", rp_data["emergency_structure"])
                if "damage_assessment" in rp_data: update_proc("3. 被害状況の把握・被害情報の共有", rp_data["damage_assessment"])
            
            # Remove from update_json so deep_update doesn't overwrite the whole list with a dict
            del update_json["response_procedures"]

        # 2. Financial Plan (List handling)
        if "finance_plan" in update_json:
            fp_data = update_json["finance_plan"] # { estimated_amount, source, details }
            # Construct a single item for now
            if not plan.financial_plan.items: plan.financial_plan.items = []
            
            # Create a "summary" item
            from src.api.schemas import FinancialPlanItem
            item_content = fp_data.get("details", "資金対策")
            amount = fp_data.get("estimated_amount", 0)
            method = fp_data.get("source", "")
            
            # Upsert logic: if item exists, update it, else append
            if plan.financial_plan.items:
                plan.financial_plan.items[0].item = item_content
                plan.financial_plan.items[0].amount = amount
                plan.financial_plan.items[0].method = method
            else:
                plan.financial_plan.items.append(FinancialPlanItem(item=item_content, amount=amount, method=method))
            
            del update_json["finance_plan"]
            
        # 3. PDCA (Implementation System)
        if "implementation_system" in update_json:
            pdca = update_json["implementation_system"]
            if "training_review" in pdca:
                plan.pdca.training_education = pdca["training_review"]
                plan.pdca.plan_review = pdca["training_review"] # Map to both for robust
            
            del update_json["implementation_system"]
            
        # 4. Contact Info
        if "contact_info" in update_json:
            ci = update_json["contact_info"]
            plan.applicant_info.contact_name = ci.get("name")
            plan.applicant_info.email = ci.get("email")
            plan.applicant_info.phone = ci.get("phone")
            del update_json["contact_info"]

        # --- Revert to Dict and Validate ---
        # Apply remaining simple updates (basic_info, measures etc.)
        current_dump = plan.model_dump()
        merged = deep_update(current_dump, update_json)
        
        # Save back
        from src.api.schemas import ApplicationRoot
        st.session_state.current_plan = ApplicationRoot(**merged)
        return True

    except Exception as e:
        print(f"Smart Update Failed: {e}")
        st.toast(f"⚠️ 更新エラー: {e}", icon="🐛") # Debug info
        return False

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

# --- Flash Message System ---
def set_flash_message(message, icon="INFO"):
    """Set a message to be shown after the next rerun."""
    st.session_state.flash_toast_message = message
    st.session_state.flash_toast_icon = icon

def check_flash_message():
    """Check and display pending flash messages."""
    if "flash_toast_message" in st.session_state:
        msg_str = st.session_state.flash_toast_message
        icon = st.session_state.get("flash_toast_icon", "INFO")
        
        # Support split messages for "Separate Parallel Display"
        msgs = msg_str.split("|||")
        
        for m in msgs:
            if m.strip():
                st.toast(m.strip(), icon=icon)
                time.sleep(1) # Stagger slightly
        
        # Halt execution to ensure visibility (User Requirement: 5s total)
        time.sleep(4)
        
        # Clear after showing
        del st.session_state["flash_toast_message"]
        if "flash_toast_icon" in st.session_state:
            del st.session_state["flash_toast_icon"]

def trigger_missing_items_chat():
    """Callback to trigger missing items chat flow securely before rerun."""
    # We need to access result, so we'll grab it from session state or re-calculate?
    # Actually, we can pass args to callback.
    pass

# Helper to be used in button args
def on_click_ask_missing(missing_msgs):
    st.session_state.ai_interviewer.set_focus_fields(missing_msgs)
    st.session_state.app_nav_selection = st.session_state.get("last_chat_nav", "経営者インタビュー")
    st.session_state.auto_trigger_message = "不足項目の入力を行いたいです。何から始めればよいですか？"
    st.session_state.app_nav_selection = st.session_state.get("last_chat_nav", "経営者インタビュー")
    st.session_state.auto_trigger_message = "不足項目の入力を行いたいです。何から始めればよいですか？"
    st.session_state.auto_trigger_persona = st.session_state.get("last_chat_nav", "経営者インタビュー").replace("インタビュー", "")

def auto_complete_interview(json_str):
    """Callback to parse interview data and redirect to dashboard."""
    try:
        data_dict = json.loads(json_str)
        from src.api.schemas import ApplicationRoot
        # Migrate & Validate
        migrated = ApplicationRoot.migrate_legacy_data(data_dict)
        plan = ApplicationRoot.model_validate(migrated)
        st.session_state.current_plan = plan
        
        # Redirect
        st.session_state.app_nav_selection = "Dashboard Mode (Progress)"
        
        # Set Flash Message for next screen
        set_flash_message("✅ 自動解析が完了しました (Auto Analysis Complete)", icon="🤖")
        
    except Exception as e:
        st.error(f"Data Processing Error: {e}")

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

                                # --- Context Injection for Multi-Disaster Support ---
                                # Load the plan into history so the AI knows the baseline for subsequent discussions (e.g. Tsunami)
                                context_content = f"""
【システム通知: 既存計画データの読み込み】
ユーザーが以下の事業計画書データをアップロードしました。
このデータを「現在の決定事項」として認識し、今後の会話（追加の災害対策など）と統合してください。

```json
{json.dumps(clean_data, ensure_ascii=False, indent=2)}
```
"""
                                st.session_state.ai_interviewer.history.append({
                                    "role": "model", 
                                    "content": context_content,
                                    "persona": "AI Concierge",
                                    "target_persona": "General" # Visible to all
                                })
                            except Exception as val_e:
                                st.error(f"データ構造読み込みエラー: {val_e}")
                                # Stop execution so user sees the error
                                st.stop()


                        
                        else:
                            st.warning("⚠️ 読み込めるデータ形式ではありません (history, basic_info, goals キーが見つかりません)")
                    else:
                         st.warning("⚠️ JSON形式が無効です")

                    st.session_state.last_loaded_file_id = file_id
                    
                    # Auto-Redirect to Dashboard if Plan Loaded
                    if "current_plan" in st.session_state and st.session_state.current_plan:
                        st.session_state.app_nav_selection = "Dashboard Mode (Progress)"
                        
                        # Set Flash Message instead of immediate toast + sleep
                        company_name = st.session_state.current_plan.basic_info.corporate_name or "未設定"
                        # Multi-line flash message via split toast
                        msg = f"✅ 事業計画データを読み込みました (Plan: {company_name})|||🚀 ダッシュボードへ移動します"
                        set_flash_message(msg, icon="➡️")
                        
                    else:
                        st.toast("DEBUG: No Plan Loaded", icon="🐛")
                        time.sleep(2) # Keep debug visible
                        
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
             
             # --- Sidebar: Recommended Actions (Mirrors Dashboard) ---
    with st.sidebar:
        st.divider()
        st.subheader("💡 推奨アクション (Recommended)")
        
        # 1. From Consensus Chat Suggestions
        if "_consensus_suggestions" in st.session_state:
            sugg = st.session_state._consensus_suggestions
            if "options" in sugg and sugg["options"]:
                st.caption("🤖 AIからの提案:")
                for opt in sugg["options"]:
                    st.info(f"👉 {opt}")
        
        # 2. From Missing Items (Static Analysis)
        if "current_plan" in st.session_state and st.session_state.current_plan:
             from src.core.completion_checker import CompletionChecker
             # Fix: Use static method directly
             result = CompletionChecker.analyze(st.session_state.current_plan)
             if result["missing_mandatory"]:
                 st.caption("⚠️ 未定の必須項目:")
                 for m in result["missing_mandatory"][:3]: # Show top 3
                     st.warning(f"📌 {m['section']}")
        else:
            st.caption("ℹ️ 計画データ未読み込み")

    # --- Main Area ---


# --- Main Area ---

# Check Flash Messages at Start of Render Cycle
check_flash_message()

if mode == "Chat Mode (Interview)":
    # --- Ensure Initial State for Optimization (Empty Plan + Dashboard) ---
    if "current_plan" not in st.session_state:
        from src.api.schemas import ApplicationRoot
        # Initialize blank plan object (not dict) for CompletionChecker compatibility
        st.session_state.current_plan = ApplicationRoot()
    
    # 1. Dashboard Navigation & Header
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
                                 status.write("📝 Gemini Experimental (High Reasoning Preview) で資料を読み込んでいます...")
                                 try:
                                     all_files = st.session_state.ai_interviewer.uploaded_file_refs
                                     extracted_data = st.session_state.ai_interviewer.extract_structured_data(text="", file_refs=all_files)
                                     
                                     if extracted_data:
                                         status.write("✅ 構造化データを検出しました。計画書に反映します...")
                                         
                                         # Merge Logic
                                         try:
                                             # Convert to Schema if not already (assuming dict return)
                                             from src.api.schemas import ApplicationRoot
                                             
                                             # Initialize plan if None
                                             if not st.session_state.get("current_plan"):
                                                  st.session_state.current_plan = ApplicationRoot() # Empty Init
                                             
                                             # Update fields (Recursive merge or Pydantic copy?)
                                             # Ideally we use a merge utility, but for now we re-validate the merged dict.
                                             current_dict = st.session_state.current_plan.model_dump()
                                             
                                             # Simple recursive merge helper
                                             def deep_merge(base, update):
                                                 for k, v in update.items():
                                                     if isinstance(v, dict) and k in base and isinstance(base[k], dict):
                                                         deep_merge(base[k], v)
                                                     elif v is not None: # Only overwrite if not None
                                                         base[k] = v
                                                 return base
                                             
                                             merged_dict = deep_merge(current_dict, extracted_data)
                                             st.session_state.current_plan = ApplicationRoot.model_validate(merged_dict)
                                             
                                             status.write("💡 読み込んだ情報を計画書に統合しました。")
                                             
                                             # Add Context to History
                                             context_msg = f"【システム通知: 自動抽出完了】\n資料から以下の情報を抽出し、計画書に反映しました。\n{json.dumps(extracted_data, ensure_ascii=False, indent=2)}"
                                             st.session_state.ai_interviewer.history.append({
                                                "role": "model", 
                                                "content": context_msg,
                                                "persona": "AI Concierge",
                                                "target_persona": "General"
                                             })
                                             
                                         except Exception as merge_e:
                                             status.error(f"Merge Error: {merge_e}")

                                     else:
                                         status.write("ℹ️ 新規の構造化データは見つかりませんでした。")
                                 except Exception as ex_e:
                                     status.error(f"Extraction Error: {ex_e}")
                        
                                     status.error(f"Extraction Error: {ex_e}")
                        
                        time.sleep(5)
                        # Inline Auto-Save (Fix NameError)
                        if "session_manager" in st.session_state:
                             p_data = st.session_state.current_plan.model_dump() if st.session_state.get("current_plan") else None
                             st.session_state.session_manager.save_session(
                                 history=st.session_state.ai_interviewer.history,
                                 current_plan_dict=p_data,
                                 session_id="mobile_autosave"
                             )
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
                # Sanitize content
                import re
                
                # Check for <data> block (Final Output)
                data_match = re.search(r'<data>(.*?)</data>', msg["content"], flags=re.DOTALL)
                
                if data_match:
                    # Hide the raw data from display
                    display_content = re.sub(r'<data>.*?</data>', '', msg["content"], flags=re.DOTALL).strip()
                    st.markdown(display_content)
                    
                    # Show "Check Progress" button
                    st.button(
                        "📊 ヒアリング完了: 進捗を確認する (Check Progress)", 
                        key=f"btn_complete_{len(msg['content'])}", 
                        type="primary",
                        on_click=auto_complete_interview,
                        args=(data_match.group(1).strip(),)
                    )
                else:
                    # Standard display (Hide suggestions and updates)
                    display_content = re.sub(r'<suggestions>.*?</suggestions>', '', msg["content"], flags=re.DOTALL)
                    display_content = re.sub(r'<update>.*?</update>', '', display_content, flags=re.DOTALL).strip()
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
    # [DISABLED] User requested to prevent auto-scrolling to verify AI response content comfortably.
    # The previous JS injection has been removed.
    
    # Ensure baseline is set if it's the first run or reset
    current_len = len(st.session_state.ai_interviewer.history)
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

    # 2. Main Chat Area Container (To ensure new messages appear above the dashboard)
    main_chat_container = st.container()
    
    with main_chat_container:
        # New Session History
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
                # Persist valid suggestions
                st.session_state.last_valid_suggestions = current_suggestions
            except:
                pass
    
    # Fallback to last valid suggestions if current parsing failed (to maintain Optimized Layout)
    if not current_suggestions and "last_valid_suggestions" in st.session_state:
        current_suggestions = st.session_state.last_valid_suggestions

    suggested_prompt = None

    # --- Render Advice in Placeholder (In-place Update) ---
    advice_placeholder = st.empty()

    def render_advice_in_placeholder(placeholder, suggestions):
        """Renders the AI hints and example box inside a placeholder."""
        if not suggestions:
            placeholder.empty()
            return

        hints = suggestions.get("hints")
        example = suggestions.get("example")
        
        if hints or example:
            with placeholder.container():
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
                        
                        # Note: Buttons inside placeholders might have issues if not handled carefully during rerun?
                        # Actually if we don't rerun, the button callback won't trigger standard rerun?
                        # Wait, button click triggers rerun. If we don't rerun here, the button appears. 
                        # Clicking it triggers rerun -> script runs -> placeholder re-renders.
                        # It should work.
                        if st.button("📋 回答例の通り回答する", key=f"use_example_{stable_key}"):
                            # Setting session state for prompt pre-fill?
                            # prompt = st.chat_input... can't be pre-filled easily without key manipulation.
                            # Standard pattern: specific variable
                            # But st.chat_input doesn't support 'value'.
                            # Workaround: We can't easily prefill chat_input.
                            # Solution: We treat clicking the button AS SENDING the message?
                            # "回答例の通り回答する" -> Submit immediately. 
                            st.session_state.auto_trigger_message = example
                            st.rerun()
                            # return example
        return None

    # Initial Render
    clicked_example = render_advice_in_placeholder(advice_placeholder, current_suggestions)
    if clicked_example:
        suggested_prompt = clicked_example

    # --- Next Action Suggestions (Quick Replies) ---
    # Prioritize dynamic options
    options = current_suggestions.get("options")
    if not options: # Handle None or Empty list
        options = []
    
    # Fallback if no dynamic options (Double check to ensure buttons always appear)
    if not options:
        # --- Context-Aware Dynamic Fallback ---
        # Analyze the last message content to provide relevant options
        last_content = last_msg["content"] if last_msg else ""
        
        context_options = []
        if "役職" in last_content:
            context_options = ["代表取締役", "店長", "工場長", "社員"]
        elif "名前" in last_content:
            context_options = ["確認して入力"] # 'Same as above' is often confusing if nothing above
        elif "避難" in last_content:
             context_options = ["指定避難所へ徒歩で", "高台へ車で", "社屋の2階へ垂直避難", "自宅待機"]
        elif "安否" in last_content:
             context_options = ["安否確認システム", "LINEグループ", "電話連絡", "一斉メール"]
        elif "被害" in last_content and ("想定" in last_content or "影響" in last_content):
             context_options = ["浸水被害", "建物の倒壊", "停電・断水", "物流の停止"]
        
        if context_options:
            options = context_options
        else:
            # Standard Fallback if no context detected
            fallback_map = {
                "経営者": ["事業の強みについて", "自然災害への懸念", "重要な設備・資産"],
                "従業員": ["緊急時の連絡体制", "避難経路の確認", "顧客対応マニュアル"],
                "商工会職員": ["ハザードマップ確認", "損害保険の加入状況", "地域防災計画との連携"]
            }
            # Default to "経営者" if persona key missing
            options = fallback_map.get(persona, fallback_map["経営者"])
        
        # Inject standard options into current suggestion to persist them
        if not current_suggestions:
            current_suggestions = {"options": options}
            st.session_state.last_valid_suggestions = current_suggestions

    # --- Options Placeholder (After Advice) ---
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
                         if st.button(opt, key=f"opt_{idx}_{len(st.session_state.ai_interviewer.history)}", use_container_width=True):
                             st.session_state.auto_trigger_message = opt
                             st.rerun()

    # Render Options
    render_options_in_placeholder(options_placeholder, options)

    # --- Mini Progress Dashboard (Placeholder) - MOVED TO BOTTOM ---
    dashboard_placeholder = st.empty()

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
                    st.caption("📌 **次のアクション (クリックで入力を開始):**")
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



    # Input Area
    prompt = st.chat_input(f"{persona}として回答を入力...", key="chat_input_main")

    if st.session_state.get("auto_trigger_message"):
        prompt = st.session_state.auto_trigger_message
        st.session_state.auto_trigger_message = None

    if prompt:
        with main_chat_container:
            with st.chat_message("user", avatar="🧑‍🏫" if persona=="商工会職員" else "👤"):
                st.markdown(prompt)
        
        final_prompt = prompt
        
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
                          pass # Logic handled inside AIInterviewer parsing for now
                  except Exception as e:
                      print(f"Extraction failed: {e}")
                      status.update(label="⚠️ Extraction skipped", state="error")
        
        # Determine who responds: Model or just UI update (Wait, logic flow check)
        # The structure here is: if we have a prompt (user input or suggestion), we send it.
        
        with main_chat_container:
            # Inject Anchor for Scroll (Target for Auto-Scroll)
            st.markdown('<div id="latest-response"></div>', unsafe_allow_html=True)
            
            with st.chat_message("model", avatar="🤖"):
                with st.spinner("AI is thinking..."):
                    response = st.session_state.ai_interviewer.send_message(
                    final_prompt, 
                    persona=persona,
                    user_data=user_data
                )
                    
                    # Scroll to Anchor using JS (Wait for render > 500ms)
                    import streamlit.components.v1 as components
                    js_code = """
                        <script>
                        setTimeout(function() {
                            const element = window.parent.document.getElementById('latest-response');
                            if (element) {
                                element.scrollIntoView({behavior: 'smooth', block: 'start'});
                            }
                        }, 500);
                        </script>
                    """
                    components.html(js_code, height=0)
                # Sanitize content for display (Hide <suggestions> block implementation)
                import re
                
                # Extract and Apply <update> Incremental Data
                update_match = re.search(r'<update>(.*?)</update>', response, flags=re.DOTALL)
                if update_match:
                    try:
                        update_json_str = update_match.group(1).strip()
                        update_data = json.loads(update_json_str)
                        if apply_incremental_update(update_data):
                            print("Applied Incremental Update")
                            st.toast("⚡ データを更新しました", icon="📝")
                    except Exception as e:
                        print(f"Update Parse Failed: {e}")
                
                 # Force Dashboard Update (In-place) after every response (to reflect new state/progress)
                render_mini_dashboard_in_placeholder(dashboard_placeholder)
                
                # Strip tags for display
                display_response = re.sub(r'<suggestions>.*?</suggestions>', '', response, flags=re.DOTALL)
                display_response = re.sub(r'<update>.*?</update>', '', display_response, flags=re.DOTALL).strip()
                
                st.markdown(display_response)

                # --- Auto-Save Hook ---
                perform_auto_save()
                
                # Update Options & Advice if suggestions found
                # Typically options update requires rerun because button keys must be unique or handled.
                # But we used length-based key. History length increased by 2 (User+AI).
                # So keys will be unique.
                # We DO NOT RERUN to prevent scroll.
                match_sugg = re.search(r'<suggestions>(.*?)</suggestions>', response, flags=re.DOTALL)
                if match_sugg:
                    try:
                        new_sugg = json.loads(match_sugg.group(1))
                        
                        # Update Advice & Options ONLY if history length changed (to avoid duplicate key error with Initial Render)
                        # The keys for buttons depend on history length. 
                        # If len hasn't changed (e.g. history update issues), rendering again crashes Streamlit.
                        new_hist_len = len(st.session_state.ai_interviewer.history)
                        if new_hist_len > current_len:
                            render_advice_in_placeholder(advice_placeholder, new_sugg)
                            
                            new_opts = new_sugg.get("options", [])
                            # Logic to fallback if options missing in update
                            if not new_opts:
                                fallback_map = {
                                    "経営者": ["事業の強みについて", "自然災害への懸念", "重要な設備・資産"],
                                    "従業員": ["緊急時の連絡体制", "避難経路の確認", "顧客対応マニュアル"],
                                    "商工会職員": ["ハザードマップ確認", "損害保険の加入状況", "地域防災計画との連携"]
                                }
                                new_opts = fallback_map.get(persona, [])
                            
                            render_options_in_placeholder(options_placeholder, new_opts)
                        else:
                            print(f"Skipping placeholder update: History length {new_hist_len} == {current_len}")
                    except: pass
elif mode == "Dashboard Mode (Progress)":
    # Navigation Header for Dashboard
    col_dash_head1, col_dash_head2 = st.columns([3, 1])
    with col_dash_head1:
        st.title("📊 進捗ダッシュボード")
    with col_dash_head2:
        # 3-Way Back Navigation
        st.button("⬅️ 経営者インタビュー", on_click=change_mode, args=("Chat Mode (Interview)", "経営者"), use_container_width=True)
        st.button("⬅️ 従業員インタビュー", on_click=change_mode, args=("Chat Mode (Interview)", "従業員"), use_container_width=True)
        st.button("⬅️ 商工会職員インタビュー", on_click=change_mode, args=("Chat Mode (Interview)", "商工会職員"), use_container_width=True)

    st.info("チャット履歴から事業計画書の完成度を自動判定します。")
    
    from src.api.schemas import ApplicationRoot
    
    # Auto-Analysis / Display Logic (No Manual Button)
    if "current_plan" in st.session_state:
        plan: ApplicationRoot = st.session_state.current_plan
        from src.core.completion_checker import CompletionChecker
        
        # Run Analysis
        result = CompletionChecker.analyze(plan)
        
        # --- 1. Status Banner & Header ---
        st.divider()
        st.subheader("📊 事業計画書 完成度診断")
        
        col_m1, col_m2 = st.columns([1, 4])
        with col_m1:
            st.metric(label="認定可能性スコア", value=f"{result['total_score']} / 100", help="100点で電子申請の認定要件を満たします")
            
        with col_m2:
            st.caption("認定に向けた必須項目の入力状況")
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
                    st.markdown("### 🔴 **未入力 (必須)**")
                    for item in critical_items:
                        sec_label = section_map.get(item['section'], item['section'])
                        st.error(f"**{sec_label}**: {item['msg']}", icon="🔴")
                
                if warning_items:
                    st.markdown("### 🟡 **入力不足 (要確認)**")
                    for item in warning_items:
                        sec_label = section_map.get(item['section'], item['section'])
                        st.warning(f"**{sec_label}**: {item['msg']}", icon="🟡")
                
                with st.columns(2)[0]:
                    # Prepare args for callback
                    missing_msgs = [m['msg'] for m in result['missing_mandatory']]
                    
                    st.button(
                        "インタビュアーに不足項目を聞いてもらう", 
                        type="primary", 
                        key="btn_ask_missing",
                        on_click=on_click_ask_missing,
                        args=(missing_msgs,)
                    )

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
            c1, c2 = st.columns(2)
            c1.link_button("🌍 ハザードマップ", "https://disaportal.gsi.go.jp/", use_container_width=True)
            c2.link_button("📉 J-SHIS 地震予測", "https://www.j-shis.bosai.go.jp/", use_container_width=True)
            
            c3, c4 = st.columns(2)
            c3.link_button("💴 金融支援 (Risk Finance)", "https://www.chusho.meti.go.jp/keiei/antei/bousai/keizokuryoku.html", use_container_width=True)
            c4.link_button("🏛️ 税制優遇 (Tax)", "https://www.chusho.meti.go.jp/keiei/antei/bousai/keizokuryoku.html#zeisei", use_container_width=True)

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
                
                # Sanitize content
                import re
                content = msg["content"]
                
                # 1. Hide <suggestions> block
                content = re.sub(r'<suggestions>.*?</suggestions>', '', content, flags=re.DOTALL).strip()
                
                # 2. Hide Raw JSON System Notification
                if "【システム通知: 既存計画データの読み込み】" in content:
                    import json
                    try:
                         json_match = re.search(r'```json\n(.*?)\n```', content, flags=re.DOTALL)
                         if json_match:
                             data = json.loads(json_match.group(1))
                             c_name = data.get("basic_info", {}).get("corporate_name", "Unknown")
                             st.success(f"✅ 既存の事業計画データを読み込みました (対象企業: {c_name})")
                             with st.expander("詳細データを確認 (View Raw Data)"):
                                 st.json(data)
                             return
                    except:
                        pass

                # 3. Final Confirmation Block (<verify>)
                verify_match = re.search(r'<verify>(.*?)</verify>', content, flags=re.DOTALL)
                if verify_match:
                    # Render the verification block in a specific colored container
                    verify_text = verify_match.group(1).strip()
                    # Remove the verify block from main content to avoid double rendering
                    main_text = re.sub(r'<verify>.*?</verify>', '', content, flags=re.DOTALL).strip()
                    
                    if main_text:
                        st.markdown(main_text)
                    
                    # Render Verification Card
                    with st.container(border=True):
                        st.info("📋 **以下の内容で登録します。確認をお願いします**")
                        st.markdown(verify_text) # Markdown inside supports bold etc.
                        
                else:
                    # Normal render
                    st.markdown(content)

    # Move Recommended Actions to Main Area (Expander at Top)
    with st.expander("💡 推奨アクション (Recommended Actions)", expanded=True):
        # 1. From Consensus Chat Suggestions
        if "_consensus_suggestions" in st.session_state:
            sugg = st.session_state._consensus_suggestions
            if "options" in sugg and sugg["options"]:
                st.caption("🤖 AIからの提案:")
                cols = st.columns(len(sugg["options"]))
                for i, opt in enumerate(sugg["options"]):
                    cols[i].info(f"👉 {opt}")
        
        # 2. From Missing Items (Static Analysis)
        if "current_plan" in st.session_state and st.session_state.current_plan:
             from src.core.completion_checker import CompletionChecker
             result = CompletionChecker.analyze(st.session_state.current_plan)
             if result["missing_mandatory"]:
                 st.caption("⚠️ 未定の必須項目:")
                 for m in result["missing_mandatory"][:3]: 
                     st.warning(f"📌 {m['section']}")
        else:
            st.caption("ℹ️ 計画データ未読み込み")

    # Show history using rendered helper
    for i in range(len(history)):
         render_message_consensus(history[i], "総合調整役") 
    
    # Input
    
    # --- Mini Progress Dashboard (Placeholder) ---
    dashboard_placeholder = st.empty()

    def render_consensus_dashboard(placeholder):
        if "current_plan" in st.session_state and st.session_state.current_plan:
             # Logic is same, but inside container
             with placeholder.container():
                from src.core.completion_checker import CompletionChecker
                res = CompletionChecker.analyze(st.session_state.current_plan)
                prog = res['mandatory_progress']
                
                cols_prog = st.columns([3, 1])
                with cols_prog[0]: st.progress(prog)
                with cols_prog[1]: st.caption(f"**{int(prog*100)}% 完了**")
                
                if res['missing_mandatory']:
                    sec_map = {"BasicInfo": "基本情報", "Goals": "事業概要", "Disaster": "災害想定", "ResponseProcedures": "初動対応", "Measures": "事前対策", "FinancialPlan": "資金計画", "PDCA": "推進体制"}
                    next_items = [sec_map.get(m['section'], m['section']) for m in res['missing_mandatory'][:3]]
                    st.write("📌 **次のアクション:** " + "  ".join([f"`{item}`" for item in next_items]))

    render_consensus_dashboard(dashboard_placeholder)

    if prompt := st.chat_input("全体方針を入力してください (例: 避難場所は高台の公園とします)"):
         with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

         # Send Message
         user_data = {"name": "Consensus", "position": "Manager"}
         with st.chat_message("model", avatar="🤖"):
             with st.spinner("調整中..."):
                response = st.session_state.ai_interviewer.send_message(
                    prompt, 
                    persona="全体合意",
                    user_data=user_data
                )
                
                # --- Incremental Plan Analysis (Consensus) ---
                import re
                update_match = re.search(r'<update>(.*?)</update>', response, flags=re.DOTALL)
                
                if update_match:
                    try:
                        update_json_str = update_match.group(1).strip()
                        update_data = json.loads(update_json_str)
                        if apply_incremental_update(update_data):
                            # Update dashboard in-place
                            render_consensus_dashboard(dashboard_placeholder)
                            st.toast("⚡ 全体方針を反映しました", icon="✅")
                    except Exception as e:
                        print(f"Update Parse Failed: {e}")
                
                # Strip and display
                display_response = re.sub(r'<update>.*?</update>', '', response, flags=re.DOTALL).strip()
                st.markdown(display_response)

                perform_auto_save()
                # NO RERUN
