"""
Frontend Components: Sidebar Utilities

Task 4: app_hybrid.py Refactoring - Component Extraction
Extracted sidebar logic for better maintainability.
"""

import streamlit as st
from typing import Optional, Dict, Any
from datetime import datetime


def calculate_step_progress(progress: int) -> int:
    """
    Calculate current step based on progress percentage.
    
    Args:
        progress: Progress percentage (0-100)
        
    Returns:
        Current step number (1-4)
    """
    if progress >= 75:
        return 4  # 出力
    elif progress >= 50:
        return 3  # 監査
    elif progress >= 25:
        return 2  # インタビュー
    else:
        return 1  # 基本情報


def render_step_wizard(progress: int) -> None:
    """
    Render step wizard indicator in sidebar.
    
    Args:
        progress: Progress percentage (0-100)
    """
    current_step = calculate_step_progress(progress)
    
    step_icons = ["📝", "💬", "🔍", "📤"]
    step_labels = ["基本情報", "インタビュー", "監査", "出力"]
    step_display = ""
    
    for i in range(4):
        if i + 1 < current_step:
            step_display += "✅ "  # Completed
        elif i + 1 == current_step:
            step_display += f"**{step_icons[i]} {step_labels[i]}** → "
        else:
            step_display += "⬜ "  # Future
    
    st.markdown(f"**現在のステップ:** Step {current_step}/4")
    st.caption(step_display.rstrip(" → "))


def render_save_button(current_plan_obj: Optional[Any]) -> None:
    """
    Render save button with timestamp display.
    
    Args:
        current_plan_obj: Current plan object
    """
    if st.button("💾 データを保存", key="sidebar_save_btn_component", use_container_width=True):
        if current_plan_obj:
            st.session_state["_last_saved_at"] = datetime.now().strftime("%H:%M:%S")
            st.success(f"✅ 保存しました ({st.session_state['_last_saved_at']})")
        else:
            st.warning("⚠️ 保存するデータがありません")
    
    if "_last_saved_at" in st.session_state:
        st.caption(f"最終保存: {st.session_state['_last_saved_at']}")


def render_share_button(current_plan_obj: Optional[Any]) -> None:
    """
    Render session share button with URL generation.
    
    Args:
        current_plan_obj: Current plan object
    """
    if st.button("🔗 セッションを共有", key="sidebar_share_btn_component", use_container_width=True):
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


def render_batch_import_ui() -> None:
    """
    Render CSV batch import expander UI.
    """
    with st.expander("📁 CSVバッチインポート（複数企業）", expanded=False):
        st.caption("CSVファイルから複数企業のデータを一括読込できます")
        
        uploaded_csv = st.file_uploader(
            "CSVファイルを選択",
            type=["csv"],
            key="batch_csv_uploader_component"
        )
        
        if uploaded_csv is not None:
            try:
                from src.core.batch_processor import BatchProcessor
                import csv
                import io
                
                csv_content = uploaded_csv.read().decode("utf-8")
                processor = BatchProcessor()
                
                # Validate columns
                reader = csv.reader(io.StringIO(csv_content))
                headers = next(reader, [])
                validation = processor.validate_csv_columns(headers)
                
                if not validation["valid"]:
                    st.error(f"❌ 必須列が不足: {', '.join(validation['missing'])}")
                else:
                    if st.button("🚀 インポート実行", key="batch_import_btn_component"):
                        result = processor.process_batch(csv_content)
                        st.session_state["_batch_result"] = result
                        st.success(result["summary"])
            except Exception as e:
                st.error(f"インポートエラー: {e}")
        
        # Sample template download
        if st.button("📋 サンプルCSVをダウンロード", key="batch_sample_btn_component"):
            from src.core.batch_processor import get_sample_template
            st.download_button(
                label="sample_template.csv",
                data=get_sample_template(),
                file_name="sample_template.csv",
                mime="text/csv"
            )
        
        # Display results
        if "_batch_result" in st.session_state:
            result = st.session_state["_batch_result"]
            st.markdown(f"**処理結果**: ✅{result['success']} ⚠️{result['partial']} ❌{result['error']}")
