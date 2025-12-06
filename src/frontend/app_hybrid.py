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
from src.core.ai_interviewer import ChatManager  # クラス名はChatManagerのまま維持（変更コスト削減）またはファイルに合わせて変更
# 今回はファイル名変更によるキャッシュクリアが目的なので、import元を変えるだけで十分。
# ただし混乱を避けるためエイリアスを使うか、中身も変えるか。
# ここでは from src.core.ai_interviewer import ChatManager とする。
# 実体ファイルの中身のクラス名も ChatManager のままならこれで動く。
from src.data.context_loader import ContextLoader
# from src.core.document_reminder import DocumentReminder # まだない場合はコメントアウト

# --- Page Config (Must be first) ---
st.set_page_config(
    page_title="Jigyokei Hybrid System",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Version Control for Session State ---
APP_VERSION = "2.5.1-rename"  # Update this to force session reset

if "app_version" not in st.session_state or st.session_state.app_version != APP_VERSION:
    st.session_state.clear()
    st.session_state.app_version = APP_VERSION
    st.rerun()

# --- Initialize Managers (Singleton-like) ---
if "chat_manager" not in st.session_state:
    st.session_state.chat_manager = ChatManager()
if "context_loader" not in st.session_state:
    # データなどを読み込むローダークラス
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    context_dir = os.path.join(root_dir, "data", "context")
    st.session_state.context_loader = ContextLoader(context_dir)

# --- 認証機能 (Simple Password) ---
def check_password():
    """Returns `True` if the user had the correct password."""
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    def password_entered():
        if st.session_state["password"] == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password
        else:
            st.session_state["password_correct"] = False

    st.text_input("Password", type="password", on_change=password_entered, key="password")
    
    # 認証未完了時はここで止める
    return False

if not check_password():
    st.stop()  # 認証されていない場合はここで処理終了（画面描画も止まる）

# ==========================================
# Main App Logic
# ==========================================

# --- Sidebar ---
with st.sidebar:
    st.header("Jigyokei Hybrid System")
    st.caption("Cloud Edition ☁️")
    
    st.divider()
    
    # Mode Selection
    mode = st.radio(
        "Select Mode",
        ["Chat Mode (Pre-Interview)", "Editor Mode (Support Day)"],
        index=0
    )
    
    st.divider()

    st.subheader("Data Management")
    uploaded_file = st.file_uploader("Load Previous Session (JSON)", type=["json"])
    
    if uploaded_file:
        try:
            data = json.load(uploaded_file)
            st.session_state.chat_manager.load_history(data.get("history", []))
            st.success("Session Loaded!")
        except Exception as e:
            st.error(f"Failed to load: {e}")

    # Download Button
    if st.session_state.chat_manager.history:
        history_json = json.dumps({"history": st.session_state.chat_manager.history}, indent=2, ensure_ascii=False)
        st.download_button(
            label="💾 Download Session (JSON)",
            data=history_json,
            file_name=f"session_{int(time.time())}.json",
            mime="application/json"
        )

    if uploaded_file:
        try:
            # ファイルポインタを先頭に戻す（重要）
            uploaded_file.seek(0)
            data = json.load(uploaded_file)
            history = data.get("history", [])
            st.session_state.chat_manager.load_history(history)
            
            st.success(f"Session Loaded! ({len(history)} messages)")
            # 読み込みを反映させるためにリプレイなどが必要かもしれないが、
            # Streamlitの描画フロー的に、ここでstateが変わればメインエリアで描画されるはず。
            # 念のため、変数が変わったことをUIに反映させきれていない疑いがあるのでrerunする手もあるが、
            # 無限ループを避けるため、ボタン押下時のみにするなどの工夫がいる。
            # ここでは file_uploader がある限り毎回通るので、チェックを入れる。
            
        except Exception as e:
            st.error(f"Failed to load: {e}")

# --- Main Area ---

if mode == "Chat Mode (Pre-Interview)":
    st.title("🤖 AI Interviewer (Chat Mode)")
    st.markdown("事業計画書の作成に必要な情報をヒアリングします。")

    # 1. チャット履歴の表示
    #    (st.chat_messageを使ってループ表示)
    for msg in st.session_state.chat_manager.history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 2. ユーザー入力 (st.chat_input)
    #    ★重要★ これを条件分岐や `if` の中に入れないこと。
    #    常にレンダリングされる場所に配置する。
    prompt = st.chat_input("回答や指示を入力してください...")

    # 3. 入力があった場合の処理
    if prompt:
        # User message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # AI Response
        with st.chat_message("model"):
            with st.spinner("AI is thinking..."):
                response = st.session_state.chat_manager.send_message(prompt)
                st.markdown(response)



elif mode == "Editor Mode (Support Day)":
    st.title("📝 Editor Mode")
    st.info("このモードは現在開発中です。JSONデータの確認などができます。")
    
    st.subheader("Current Context Data")
    # 仮のデータ表示
    st.json(st.session_state.chat_manager.history)
