"""
Frontend Components: Loading State Utilities

Task 7: Loading Spinner for Heavy Operations
Provides user feedback during long-running operations.
"""

import streamlit as st
from typing import Optional, Callable, Any
from contextlib import contextmanager


@contextmanager
def loading_spinner(message: str = "処理中..."):
    """
    Context manager for displaying a loading spinner.
    
    Usage:
        with loading_spinner("データを保存中..."):
            heavy_operation()
    
    Args:
        message: Message to display during loading
    """
    with st.spinner(message):
        yield


def with_progress_feedback(
    operation: Callable,
    start_message: str = "処理を開始しました...",
    success_message: str = "✅ 完了しました",
    error_message: str = "❌ エラーが発生しました"
) -> Any:
    """
    Execute an operation with progress feedback.
    
    Args:
        operation: Function to execute
        start_message: Message shown during operation
        success_message: Message shown on success
        error_message: Message shown on error
        
    Returns:
        Result of the operation
    """
    try:
        with st.spinner(start_message):
            result = operation()
        st.success(success_message)
        return result
    except Exception as e:
        st.error(f"{error_message}: {e}")
        return None


def render_progress_bar(
    current: int,
    total: int,
    label: str = "",
    show_percentage: bool = True
) -> None:
    """
    Render a progress bar with optional label.
    
    Args:
        current: Current progress value
        total: Total value
        label: Optional label text
        show_percentage: Whether to show percentage
    """
    if total == 0:
        return
    
    progress = min(1.0, max(0.0, current / total))
    st.progress(progress)
    
    if show_percentage:
        pct = int(progress * 100)
        if label:
            st.caption(f"{label}: {pct}%")
        else:
            st.caption(f"{pct}%")


def show_loading_message(message: str, icon: str = "⏳") -> None:
    """
    Show a loading message with icon.
    
    Args:
        message: Message to display
        icon: Icon to show
    """
    st.info(f"{icon} {message}")


def show_operation_status(
    operation_name: str,
    status: str,
    details: Optional[str] = None
) -> None:
    """
    Show operation status with appropriate styling.
    
    Args:
        operation_name: Name of the operation
        status: One of 'pending', 'running', 'success', 'error'
        details: Optional details text
    """
    icons = {
        "pending": "⏸️",
        "running": "🔄",
        "success": "✅",
        "error": "❌"
    }
    
    icon = icons.get(status, "📋")
    text = f"{icon} **{operation_name}**: {status}"
    
    if details:
        text += f" - {details}"
    
    if status == "error":
        st.error(text)
    elif status == "success":
        st.success(text)
    elif status == "running":
        st.info(text)
    else:
        st.caption(text)


class ProgressTracker:
    """
    Track multi-step progress with status updates.
    
    Usage:
        tracker = ProgressTracker(total_steps=3)
        tracker.start_step("Loading data")
        # ... do work ...
        tracker.complete_step()
        tracker.start_step("Processing")
        # ... do work ...
        tracker.complete_step()
    """
    
    def __init__(self, total_steps: int, title: str = "進捗状況"):
        self.total_steps = total_steps
        self.current_step = 0
        self.title = title
        self.placeholder = st.empty()
    
    def start_step(self, step_name: str) -> None:
        """Start a new step."""
        self.current_step += 1
        self._update_display(step_name, "running")
    
    def complete_step(self, message: str = "") -> None:
        """Mark current step as complete."""
        self._update_display(message or "完了", "success")
    
    def fail_step(self, error_message: str) -> None:
        """Mark current step as failed."""
        self._update_display(error_message, "error")
    
    def _update_display(self, message: str, status: str) -> None:
        """Update the progress display."""
        with self.placeholder.container():
            progress = self.current_step / self.total_steps
            st.progress(progress)
            
            icon = "✅" if status == "success" else "🔄" if status == "running" else "❌"
            st.caption(f"{icon} Step {self.current_step}/{self.total_steps}: {message}")
