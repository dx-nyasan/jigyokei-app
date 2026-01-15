"""
Frontend Components: Mobile Responsive Utilities

Task 6: Mobile New Feature Display Optimization
Provides responsive CSS and mobile-specific UI helpers.
"""

import streamlit as st
from typing import Optional


def inject_mobile_responsive_css() -> None:
    """
    Inject CSS for mobile-responsive layout optimization.
    
    Optimizes:
    - Sidebar behavior on mobile
    - Button sizing for touch screens
    - Expander behavior
    - Font sizes for readability
    """
    st.markdown("""
    <style>
    /* Mobile Responsive Styles - Task 6 */
    
    /* General mobile breakpoint */
    @media (max-width: 768px) {
        /* Improve button touch targets */
        .stButton > button {
            min-height: 48px !important;
            font-size: 16px !important;
            padding: 12px 16px !important;
        }
        
        /* Make expanders more touch-friendly */
        .streamlit-expanderHeader {
            min-height: 48px !important;
            font-size: 16px !important;
        }
        
        /* Improve form input touch targets */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            font-size: 16px !important;
            min-height: 44px !important;
        }
        
        /* Radio buttons spacing */
        .stRadio > div {
            gap: 12px !important;
        }
        
        .stRadio > div > label {
            min-height: 44px !important;
            display: flex !important;
            align-items: center !important;
        }
        
        /* Progress bar visibility */
        .stProgress > div > div {
            height: 12px !important;
        }
        
        /* Sidebar mobile optimization */
        section[data-testid="stSidebar"] {
            min-width: 280px !important;
        }
        
        section[data-testid="stSidebar"] .stButton > button {
            font-size: 14px !important;
        }
        
        /* File uploader area */
        .stFileUploader > div {
            min-height: 80px !important;
        }
        
        /* Code blocks */
        .stCodeBlock {
            font-size: 12px !important;
            overflow-x: auto !important;
        }
        
        /* Metrics */
        [data-testid="metric-container"] {
            padding: 8px !important;
        }
        
        /* Step wizard on mobile - stack vertically */
        .step-wizard-container {
            flex-direction: column !important;
            gap: 8px !important;
        }
    }
    
    /* Small mobile (phone portrait) */
    @media (max-width: 480px) {
        /* Even larger touch targets */
        .stButton > button {
            min-height: 52px !important;
            width: 100% !important;
        }
        
        /* Simplify layout */
        .element-container {
            padding: 4px 0 !important;
        }
        
        /* Reduce sidebar width */
        section[data-testid="stSidebar"] {
            min-width: 260px !important;
        }
    }
    
    /* Tablet landscape */
    @media (min-width: 769px) and (max-width: 1024px) {
        .stButton > button {
            min-height: 44px !important;
        }
    }
    
    /* Dark mode friendly colors for new features */
    @media (prefers-color-scheme: dark) {
        .help-tooltip {
            background-color: #333 !important;
            color: #fff !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)


def is_mobile_device() -> bool:
    """
    Detect if user is likely on a mobile device.
    
    Note: This is a best-effort detection based on viewport.
    Uses session state for caching.
    
    Returns:
        True if likely mobile, False otherwise
    """
    # Note: Streamlit doesn't provide direct viewport info
    # This would typically be done via JavaScript injection
    # For now, return False as default
    return st.session_state.get("_is_mobile", False)


def render_mobile_friendly_columns(items: list, cols_desktop: int = 3, cols_mobile: int = 1) -> None:
    """
    Render items in columns that adapt to screen size.
    
    Args:
        items: List of items to render (each item should be a callable)
        cols_desktop: Number of columns on desktop
        cols_mobile: Number of columns on mobile
    """
    # For mobile, use single column
    if is_mobile_device():
        for item in items:
            item()
    else:
        # Desktop: use specified columns
        cols = st.columns(cols_desktop)
        for i, item in enumerate(items):
            with cols[i % cols_desktop]:
                item()


def render_mobile_nav_hint() -> None:
    """
    Render navigation hint for mobile users.
    Shows swipe gesture hint on first visit.
    """
    if not st.session_state.get("_mobile_hint_shown", False):
        st.info("💡 サイドバーを開くには左からスワイプ（または ⌄ アイコンをタップ）")
        st.session_state["_mobile_hint_shown"] = True


def render_compact_progress(current: int, total: int, label: str = "") -> None:
    """
    Render compact progress indicator for mobile.
    
    Args:
        current: Current progress value
        total: Total value
        label: Optional label
    """
    progress_pct = min(100, int((current / total) * 100))
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.progress(progress_pct / 100)
    with col2:
        st.caption(f"{progress_pct}%")
    
    if label:
        st.caption(label)


def hide_menu_on_mobile() -> None:
    """
    Hide hamburger menu and footer on mobile for cleaner experience.
    """
    st.markdown("""
    <style>
    @media (max-width: 768px) {
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    }
    </style>
    """, unsafe_allow_html=True)
