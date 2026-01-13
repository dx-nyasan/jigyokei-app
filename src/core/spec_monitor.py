"""
Specification Monitor for Government System Changes

Monitors government websites for specification changes that may affect
the electronic application system requirements.

Part of WS-3: Architecture Alignment 100% Initiative (持続性 +15%)
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


class SpecMonitor:
    """
    Monitors government specification changes for Jigyokei system.
    
    理念対応:
    - 「持続性」: 政府仕様変更への迅速対応
    """
    
    # Known specification sources
    SPEC_SOURCES = [
        {
            "name": "電子申請システム",
            "url": "https://www.chusho.meti.go.jp/keiei/antei/bousai/jigyo_keizoku.htm",
            "check_keywords": ["システム改修", "入力必須", "様式変更", "改訂"]
        },
        {
            "name": "認定手引き",
            "url": "https://www.chusho.meti.go.jp/bousai/keizokuryoku/",
            "check_keywords": ["改訂", "更新", "新様式"]
        }
    ]
    
    # Known specification versions (from historical changes)
    KNOWN_CHANGES = [
        {
            "date": "2024-12-17",
            "change_id": "12-17-reform",
            "description": "教育・訓練と計画見直しの実施月が入力必須に変更",
            "affected_fields": ["training_month", "review_month", "internal_publicity"],
            "status": "implemented"
        }
    ]
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the specification monitor.
        
        Args:
            data_dir: Directory to store spec version data. Defaults to src/data.
        """
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data"
        self.data_dir = Path(data_dir)
        self.version_file = self.data_dir / "spec_version.json"
        
        # Load or create version tracking
        self.current_version = self._load_version()
    
    def _load_version(self) -> Dict[str, Any]:
        """Load current specification version from file."""
        if self.version_file.exists():
            try:
                with open(self.version_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        # Default version structure
        return {
            "last_check": None,
            "current_version": "2024-12-17",
            "known_changes": self.KNOWN_CHANGES,
            "pending_updates": []
        }
    
    def _save_version(self) -> None:
        """Save current version state to file."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with open(self.version_file, 'w', encoding='utf-8') as f:
            json.dump(self.current_version, f, ensure_ascii=False, indent=2)
    
    def get_current_status(self) -> Dict[str, Any]:
        """
        Get the current specification status.
        
        Returns:
            {
                "current_version": str,
                "last_check": str or None,
                "known_changes_count": int,
                "all_implemented": bool,
                "pending_updates": List[dict]
            }
        """
        known = self.current_version.get("known_changes", [])
        all_implemented = all(c.get("status") == "implemented" for c in known)
        
        return {
            "current_version": self.current_version.get("current_version"),
            "last_check": self.current_version.get("last_check"),
            "known_changes_count": len(known),
            "all_implemented": all_implemented,
            "pending_updates": self.current_version.get("pending_updates", [])
        }
    
    def register_change(self, change_id: str, description: str, 
                       affected_fields: List[str], date: Optional[str] = None) -> None:
        """
        Register a new specification change manually.
        
        Args:
            change_id: Unique identifier for the change
            description: Human-readable description
            affected_fields: List of schema fields affected
            date: Date of the change (defaults to today)
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        new_change = {
            "date": date,
            "change_id": change_id,
            "description": description,
            "affected_fields": affected_fields,
            "status": "pending"
        }
        
        # Check if already exists
        existing_ids = [c["change_id"] for c in self.current_version.get("known_changes", [])]
        if change_id not in existing_ids:
            self.current_version["known_changes"].append(new_change)
            self.current_version["pending_updates"].append(new_change)
            self._save_version()
    
    def mark_implemented(self, change_id: str) -> bool:
        """
        Mark a specification change as implemented.
        
        Args:
            change_id: The change ID to mark as implemented
            
        Returns:
            True if change was found and updated, False otherwise
        """
        for change in self.current_version.get("known_changes", []):
            if change["change_id"] == change_id:
                change["status"] = "implemented"
                # Remove from pending
                self.current_version["pending_updates"] = [
                    p for p in self.current_version.get("pending_updates", [])
                    if p["change_id"] != change_id
                ]
                self._save_version()
                return True
        return False
    
    def check_for_updates(self) -> Dict[str, Any]:
        """
        Check for specification updates (placeholder for future web scraping).
        
        Currently returns manual check status. In future versions,
        this could integrate with web scraping to auto-detect changes.
        
        Returns:
            {
                "checked_at": str,
                "updates_found": bool,
                "message": str,
                "sources_checked": List[dict]
            }
        """
        checked_at = datetime.now().isoformat()
        self.current_version["last_check"] = checked_at
        self._save_version()
        
        # Placeholder: In production, this would scrape the government websites
        return {
            "checked_at": checked_at,
            "updates_found": False,
            "message": "手動確認が必要です。中小企業庁のウェブサイトをご確認ください。",
            "sources_checked": [
                {"name": s["name"], "url": s["url"]} 
                for s in self.SPEC_SOURCES
            ]
        }
    
    def get_affected_schema_fields(self) -> List[str]:
        """
        Get all schema fields affected by known changes.
        
        Returns:
            List of field names that have been modified by spec changes
        """
        fields = set()
        for change in self.current_version.get("known_changes", []):
            fields.update(change.get("affected_fields", []))
        return sorted(list(fields))


# Convenience functions
def get_spec_status() -> Dict[str, Any]:
    """Get current specification status."""
    monitor = SpecMonitor()
    return monitor.get_current_status()


def check_spec_updates() -> Dict[str, Any]:
    """Check for specification updates."""
    monitor = SpecMonitor()
    return monitor.check_for_updates()
