"""
LangGraph Integration Module for Streamlit

This module provides the bridge between LangGraph agent workflows
and the Streamlit-based app_hybrid.py frontend.

Key components:
- Session management with checkpointing
- State synchronization between Streamlit and LangGraph
- Human-in-the-loop interrupt handling
- Error handling for production reliability

Part of Phase 5: Production Integration.
"""
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, field
import os
import json


@dataclass
class LangGraphSession:
    """
    Manages a LangGraph session with checkpointing support.
    
    Attributes:
        session_id: Unique identifier for the session
        state: Current graph state dictionary
        checkpoint_path: Path to checkpoint file
    """
    session_id: str
    state: Dict[str, Any] = field(default_factory=dict)
    checkpoint_path: Optional[str] = None
    
    def __post_init__(self):
        if self.checkpoint_path is None:
            checkpoint_dir = os.path.join(
                os.path.dirname(__file__), "..", "..", "checkpoints"
            )
            os.makedirs(checkpoint_dir, exist_ok=True)
            self.checkpoint_path = os.path.join(
                checkpoint_dir, f"{self.session_id}.json"
            )
    
    def save_checkpoint(self) -> None:
        """Save current state to checkpoint file."""
        with open(self.checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)
    
    def load_checkpoint(self) -> bool:
        """Load state from checkpoint file."""
        if os.path.exists(self.checkpoint_path):
            with open(self.checkpoint_path, 'r', encoding='utf-8') as f:
                self.state = json.load(f)
            return True
        return False


def create_langgraph_session(session_id: str) -> LangGraphSession:
    """
    Create a new LangGraph session.
    
    Args:
        session_id: Unique session identifier
        
    Returns:
        New LangGraphSession instance
    """
    return LangGraphSession(session_id=session_id)


def restore_session(session_id: str) -> LangGraphSession:
    """
    Restore a session from checkpoint.
    
    Args:
        session_id: Session ID to restore
        
    Returns:
        Restored LangGraphSession with loaded state
    """
    session = LangGraphSession(session_id=session_id)
    session.load_checkpoint()
    return session


def sync_to_langgraph(streamlit_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert Streamlit session state to LangGraph state format.
    
    Args:
        streamlit_state: Streamlit st.session_state dict
        
    Returns:
        LangGraph-compatible state dictionary
    """
    langgraph_state = {}
    
    # Direct mappings
    direct_keys = ["applicant_name", "location", "current_section"]
    for key in direct_keys:
        if key in streamlit_state:
            langgraph_state[key] = streamlit_state[key]
    
    # Convert interview log to raw text
    if "interview_log" in streamlit_state:
        langgraph_state["raw_interview_text"] = "\n".join(
            streamlit_state["interview_log"]
        )
    
    # Initialize defaults
    langgraph_state.setdefault("revision_count", 0)
    langgraph_state.setdefault("max_revisions", 3)
    langgraph_state.setdefault("critique_list", [])
    langgraph_state.setdefault("human_approved", False)
    langgraph_state.setdefault("status", "pending")
    
    return langgraph_state


def sync_to_streamlit(langgraph_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert LangGraph state back to Streamlit session format.
    
    Args:
        langgraph_state: LangGraph state dictionary
        
    Returns:
        Updates to apply to Streamlit session_state
    """
    updates = {}
    
    # Keys to sync back
    sync_keys = [
        "draft_content",
        "critique_list", 
        "status",
        "current_section",
        "human_approved"
    ]
    
    for key in sync_keys:
        if key in langgraph_state:
            updates[key] = langgraph_state[key]
    
    return updates


class LangGraphRunner:
    """
    Runner for executing LangGraph workflows from Streamlit.
    
    Handles graph execution, human interrupts, and error recovery.
    """
    
    def __init__(self):
        self._graph = None
    
    @property
    def graph(self):
        """Lazy-load the LangGraph graph."""
        if self._graph is None:
            from src.core.langgraph_agent import build_jigyokei_graph
            self._graph = build_jigyokei_graph()
        return self._graph
    
    def run_section(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run section generation workflow.
        
        Args:
            state: Initial state dictionary
            
        Returns:
            Updated state after graph execution
        """
        config = {"configurable": {"thread_id": state.get("session_id", "default")}}
        result = self.graph.invoke(state, config)
        return result
    
    def run_section_safe(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run section generation with error handling.
        
        Args:
            state: Initial state dictionary
            
        Returns:
            Updated state or error state
        """
        try:
            return self.run_section(state)
        except Exception as e:
            return {
                "status": "error",
                "error_message": str(e),
                **state
            }
    
    def is_waiting_for_human(self, state: Dict[str, Any]) -> bool:
        """
        Check if workflow is waiting for human input.
        
        Args:
            state: Current state dictionary
            
        Returns:
            True if human input is required
        """
        return state.get("status") == "needs_human"
    
    def resume_with_input(
        self, 
        state: Dict[str, Any], 
        human_input: str
    ) -> Dict[str, Any]:
        """
        Resume workflow after human provides input.
        
        Args:
            state: Current state dictionary
            human_input: User's revision instructions
            
        Returns:
            Updated state after resuming
        """
        state["user_intent"] = human_input
        state["status"] = "writing"  # Resume writing
        
        return self.run_section(state)


# Singleton runner instance
_runner_instance: Optional[LangGraphRunner] = None


def get_runner() -> LangGraphRunner:
    """Get or create the LangGraph runner instance."""
    global _runner_instance
    if _runner_instance is None:
        _runner_instance = LangGraphRunner()
    return _runner_instance
