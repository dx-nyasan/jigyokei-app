"""
Review Panel Component for Human-in-the-loop UI

This module provides Streamlit components for:
- Displaying critique lists from the Reviewer AI
- Highlighting issues in draft text
- Showing manual reference examples
- Handling user revision input

Part of Phase 3: Human-in-the-loop implementation.
"""
from typing import List, Dict, Optional
import html


def render_critique_list(critiques: List[Dict]) -> str:
    """
    Render a list of critique items as HTML.
    
    Args:
        critiques: List of critique dictionaries with 'issue' and 'manual_reference' keys
        
    Returns:
        HTML string for display
    
    Example:
        >>> critiques = [{"issue": "数値不足", "manual_reference": "例: 70%"}]
        >>> html = render_critique_list(critiques)
    """
    if not critiques:
        return "<p>✅ 指摘事項はありません</p>"
    
    html_parts = ['<div class="critique-list">']
    html_parts.append('<h4>📋 審査員からの指摘事項</h4>')
    html_parts.append('<ul>')
    
    for i, critique in enumerate(critiques, 1):
        issue = html.escape(critique.get("issue", ""))
        reference = html.escape(critique.get("manual_reference", ""))
        is_resolved = critique.get("is_resolved", False)
        
        status_icon = "✅" if is_resolved else "⚠️"
        style = "text-decoration: line-through; color: gray;" if is_resolved else ""
        
        html_parts.append(f'<li style="{style}">')
        html_parts.append(f'<strong>{status_icon} {i}. {issue}</strong>')
        if reference:
            html_parts.append(f'<br><small>📖 参考: {reference}</small>')
        html_parts.append('</li>')
    
    html_parts.append('</ul>')
    html_parts.append('</div>')
    
    return '\n'.join(html_parts)


def highlight_issues(draft: str, issues: List[str]) -> str:
    """
    Highlight problematic sections in draft text.
    
    Args:
        draft: Original draft text
        issues: List of issue descriptions to flag
        
    Returns:
        HTML string with highlighted sections
        
    Note:
        Currently adds a warning banner. Future versions may highlight
        specific text spans based on NLP analysis.
    """
    if not draft:
        return ""
    
    if not issues:
        return html.escape(draft)
    
    # Add warning banner for issues
    warning_html = '<div class="issue-banner" style="background: #fff3cd; padding: 8px; margin-bottom: 10px; border-radius: 4px;">'
    warning_html += f'<strong>⚠️ {len(issues)}件の改善点があります</strong>'
    warning_html += '</div>'
    
    # Escape the draft text
    escaped_draft = html.escape(draft)
    
    return warning_html + f'<div class="draft-content">{escaped_draft}</div>'


def render_manual_panel(examples: List[str]) -> str:
    """
    Render manual reference examples in a side panel format.
    
    Args:
        examples: List of example texts from the certification manual
        
    Returns:
        HTML string for the reference panel
    """
    if not examples:
        return '<div class="manual-panel"><p>参考例がありません</p></div>'
    
    html_parts = ['<div class="manual-panel" style="background: #e7f3ff; padding: 12px; border-radius: 8px;">']
    html_parts.append('<h4>📚 マニュアルの記載例</h4>')
    
    for i, example in enumerate(examples, 1):
        escaped = html.escape(example)
        html_parts.append(f'<div class="example-item" style="margin-bottom: 8px; padding: 8px; background: white; border-radius: 4px;">')
        html_parts.append(f'<strong>例{i}:</strong> {escaped}')
        html_parts.append('</div>')
    
    html_parts.append('</div>')
    
    return '\n'.join(html_parts)


def get_pending_critiques(state: Dict) -> List[Dict]:
    """
    Extract pending (unresolved) critiques from graph state.
    
    Args:
        state: LangGraph state dictionary
        
    Returns:
        List of critique dictionaries that are not resolved
    """
    critiques = state.get("critique_list", [])
    return [c for c in critiques if not c.get("is_resolved", False)]


def apply_user_revision(state: Dict, user_input: str) -> Dict:
    """
    Apply user's revision input to the state.
    
    Args:
        state: Current graph state
        user_input: User's revision comments or instructions
        
    Returns:
        Updated state with user_intent set
    """
    updated = state.copy()
    updated["user_intent"] = user_input
    return updated


def mark_resolved(critiques: List[Dict], index: int) -> List[Dict]:
    """
    Mark a specific critique as resolved.
    
    Args:
        critiques: List of critique dictionaries
        index: Index of the critique to mark as resolved
        
    Returns:
        Updated list with the specified critique marked as resolved
    """
    if not 0 <= index < len(critiques):
        return critiques
    
    updated = [c.copy() for c in critiques]
    updated[index]["is_resolved"] = True
    return updated


# Streamlit-specific helper functions
def render_streamlit_review_panel(state: Dict):
    """
    Render the complete review panel in Streamlit.
    
    This is a convenience function that combines all panel components.
    Should be called from app_hybrid.py.
    
    Args:
        state: LangGraph state dictionary
    """
    try:
        import streamlit as st
        
        critiques = get_pending_critiques(state)
        draft = state.get("draft_content", "")
        
        # Main content area
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📝 下書き内容")
            issues = [c.get("issue", "") for c in critiques]
            highlighted = highlight_issues(draft, issues)
            st.markdown(highlighted, unsafe_allow_html=True)
            
            # Critique list
            critique_html = render_critique_list(state.get("critique_list", []))
            st.markdown(critique_html, unsafe_allow_html=True)
        
        with col2:
            st.subheader("📚 参考資料")
            # Would integrate with RAG here
            st.info("マニュアルの記載例がここに表示されます")
        
        # User input area
        st.subheader("✏️ 修正指示")
        user_input = st.text_area(
            "修正したい内容を入力してください",
            placeholder="例: 南海トラフ地震の発生確率70%を追記してください"
        )
        
        if st.button("修正を適用", type="primary"):
            if user_input:
                st.session_state["user_revision"] = user_input
                st.success("修正指示を保存しました。「続行」ボタンで処理を再開します。")
                
    except ImportError:
        # Not running in Streamlit context
        pass
