"""
History Tracker for Audit Score Tracking

Tracks changes in audit scores over time and provides comparison
functionality for transparency in score evolution.

Part of WS-4: Architecture Alignment 100% Initiative (透明性 +15%)
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import hashlib


class HistoryTracker:
    """
    Tracks audit score history and provides comparison functionality.
    
    理念対応:
    - 「透明性」: スコア変動の根拠を明示
    """
    
    def __init__(self, history_dir: Optional[str] = None):
        """
        Initialize the history tracker.
        
        Args:
            history_dir: Directory to store history data.
        """
        if history_dir is None:
            # Use userdata/history as default
            history_dir = Path(__file__).parent.parent.parent / "userdata" / "history"
        self.history_dir = Path(history_dir)
        self.history_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_plan_id(self, plan) -> str:
        """Generate a unique ID for a plan based on company name."""
        company = ""
        if hasattr(plan, 'basic_info') and plan.basic_info:
            company = plan.basic_info.corporate_name or ""
        
        if not company:
            company = "anonymous"
        
        # Create hash for privacy
        return hashlib.md5(company.encode()).hexdigest()[:12]
    
    def _get_history_file(self, plan_id: str) -> Path:
        """Get the history file path for a plan."""
        return self.history_dir / f"history_{plan_id}.json"
    
    def _load_history(self, plan_id: str) -> List[Dict[str, Any]]:
        """Load history for a specific plan."""
        history_file = self._get_history_file(plan_id)
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return []
    
    def _save_history(self, plan_id: str, history: List[Dict[str, Any]]) -> None:
        """Save history for a specific plan."""
        history_file = self._get_history_file(plan_id)
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    
    def save_snapshot(self, plan, audit_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save a new snapshot of the current audit state.
        
        Args:
            plan: ApplicationRoot instance
            audit_result: Result from CompletionChecker.analyze()
            
        Returns:
            The snapshot that was saved
        """
        plan_id = self._get_plan_id(plan)
        history = self._load_history(plan_id)
        
        # Create snapshot
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "total_score": audit_result.get("total_score", 0),
            "status": audit_result.get("status", "unknown"),
            "mandatory_progress": audit_result.get("mandatory_progress", 0),
            "missing_count": len(audit_result.get("missing_mandatory", [])),
            "section_scores": self._extract_section_scores(audit_result),
            "logic_consistency_score": audit_result.get("logic_consistency", {}).get("consistency_score", 100)
        }
        
        # Append to history (keep last 50 snapshots)
        history.append(snapshot)
        if len(history) > 50:
            history = history[-50:]
        
        self._save_history(plan_id, history)
        return snapshot
    
    def _extract_section_scores(self, audit_result: Dict[str, Any]) -> Dict[str, int]:
        """Extract section-level scores from audit result."""
        # Approximate section scores from missing items
        sections = {
            "BasicInfo": 100,
            "Goals": 100,
            "Disaster": 100,
            "ResponseProcedures": 100,
            "Measures": 100,
            "FinancialPlan": 100,
            "PDCA": 100
        }
        
        for item in audit_result.get("missing_mandatory", []):
            section = item.get("section", "")
            severity = item.get("severity", "warning")
            
            if section in sections:
                if severity == "critical":
                    sections[section] = max(0, sections[section] - 30)
                elif severity == "warning":
                    sections[section] = max(0, sections[section] - 15)
        
        return sections
    
    def get_history(self, plan, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent history for a plan.
        
        Args:
            plan: ApplicationRoot instance
            limit: Maximum number of snapshots to return
            
        Returns:
            List of historical snapshots (newest first)
        """
        plan_id = self._get_plan_id(plan)
        history = self._load_history(plan_id)
        return list(reversed(history[-limit:]))
    
    def compare_with_previous(self, plan, current_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Compare current result with the previous snapshot.
        
        Args:
            plan: ApplicationRoot instance
            current_result: Current audit result
            
        Returns:
            Comparison dict or None if no previous history
        """
        plan_id = self._get_plan_id(plan)
        history = self._load_history(plan_id)
        
        if not history:
            return None
        
        previous = history[-1]
        current_score = current_result.get("total_score", 0)
        previous_score = previous.get("total_score", 0)
        
        change = current_score - previous_score
        
        # Determine change reasons
        reasons = []
        
        # Check section changes
        current_sections = self._extract_section_scores(current_result)
        previous_sections = previous.get("section_scores", {})
        
        for section, current_val in current_sections.items():
            prev_val = previous_sections.get(section, 100)
            diff = current_val - prev_val
            
            if diff > 0:
                reasons.append(f"✅ {section}: +{diff}点 (改善)")
            elif diff < 0:
                reasons.append(f"⚠️ {section}: {diff}点 (低下)")
        
        return {
            "previous_score": previous_score,
            "current_score": current_score,
            "change": change,
            "change_direction": "up" if change > 0 else ("down" if change < 0 else "same"),
            "previous_timestamp": previous.get("timestamp"),
            "reasons": reasons,
            "improvement_rate": f"{abs(change):.1f}%" if previous_score > 0 else "N/A"
        }
    
    def get_score_trend(self, plan, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get score trend data for visualization.
        
        Args:
            plan: ApplicationRoot instance
            days: Number of days to include
            
        Returns:
            List of {date, score} dicts for charting
        """
        plan_id = self._get_plan_id(plan)
        history = self._load_history(plan_id)
        
        # Group by date and take latest for each day
        daily_scores = {}
        for snapshot in history:
            date = snapshot.get("timestamp", "")[:10]  # YYYY-MM-DD
            daily_scores[date] = snapshot.get("total_score", 0)
        
        return [{"date": k, "score": v} for k, v in sorted(daily_scores.items())]


# Convenience functions for easy import
def save_audit_snapshot(plan, audit_result: Dict[str, Any]) -> Dict[str, Any]:
    """Save an audit snapshot."""
    tracker = HistoryTracker()
    return tracker.save_snapshot(plan, audit_result)


def get_score_comparison(plan, current_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get comparison with previous audit."""
    tracker = HistoryTracker()
    return tracker.compare_with_previous(plan, current_result)
