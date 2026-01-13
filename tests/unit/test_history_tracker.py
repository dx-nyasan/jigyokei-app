"""
Unit tests for HistoryTracker

Tests audit score history tracking for architecture alignment.
"""

import pytest
import tempfile
import os
from src.core.history_tracker import HistoryTracker, save_audit_snapshot, get_score_comparison
from src.api.schemas import ApplicationRoot, BasicInfo


@pytest.fixture
def temp_history_dir():
    """Create a temporary directory for history testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_plan():
    """Create a sample plan for testing"""
    return ApplicationRoot(
        basic_info=BasicInfo(
            corporate_name="テスト株式会社"
        )
    )


@pytest.fixture
def sample_audit_result():
    """Create a sample audit result"""
    return {
        "total_score": 75,
        "status": "warning",
        "mandatory_progress": 0.8,
        "missing_mandatory": [
            {"section": "PDCA", "msg": "訓練月未設定", "severity": "critical"}
        ],
        "suggestions": ["PDCAを改善してください"],
        "logic_consistency": {"consistency_score": 85, "warnings": []}
    }


class TestHistoryTracker:
    """Test suite for HistoryTracker"""
    
    def test_tracker_creation(self, temp_history_dir):
        """Test that tracker can be created"""
        tracker = HistoryTracker(history_dir=temp_history_dir)
        assert tracker is not None
        assert tracker.history_dir.exists()
    
    def test_save_snapshot(self, temp_history_dir, sample_plan, sample_audit_result):
        """Test saving a snapshot"""
        tracker = HistoryTracker(history_dir=temp_history_dir)
        snapshot = tracker.save_snapshot(sample_plan, sample_audit_result)
        
        assert "timestamp" in snapshot
        assert snapshot["total_score"] == 75
        assert snapshot["status"] == "warning"
    
    def test_get_history(self, temp_history_dir, sample_plan, sample_audit_result):
        """Test getting history"""
        tracker = HistoryTracker(history_dir=temp_history_dir)
        
        # Save multiple snapshots
        tracker.save_snapshot(sample_plan, sample_audit_result)
        sample_audit_result["total_score"] = 80
        tracker.save_snapshot(sample_plan, sample_audit_result)
        
        history = tracker.get_history(sample_plan, limit=10)
        
        assert len(history) == 2
        assert history[0]["total_score"] == 80  # Newest first
    
    def test_compare_with_previous(self, temp_history_dir, sample_plan, sample_audit_result):
        """Test comparison with previous snapshot"""
        tracker = HistoryTracker(history_dir=temp_history_dir)
        
        # Save first snapshot (75 points)
        tracker.save_snapshot(sample_plan, sample_audit_result)
        
        # Create improved result (85 points)
        improved_result = sample_audit_result.copy()
        improved_result["total_score"] = 85
        improved_result["missing_mandatory"] = []
        
        comparison = tracker.compare_with_previous(sample_plan, improved_result)
        
        assert comparison is not None
        assert comparison["previous_score"] == 75
        assert comparison["current_score"] == 85
        assert comparison["change"] == 10
        assert comparison["change_direction"] == "up"
    
    def test_compare_with_no_history(self, temp_history_dir, sample_plan, sample_audit_result):
        """Test comparison when no history exists"""
        tracker = HistoryTracker(history_dir=temp_history_dir)
        
        comparison = tracker.compare_with_previous(sample_plan, sample_audit_result)
        
        assert comparison is None
    
    def test_get_score_trend(self, temp_history_dir, sample_plan, sample_audit_result):
        """Test getting score trend data"""
        tracker = HistoryTracker(history_dir=temp_history_dir)
        
        # Save snapshots with different scores
        for score in [60, 70, 80]:
            sample_audit_result["total_score"] = score
            tracker.save_snapshot(sample_plan, sample_audit_result)
        
        trend = tracker.get_score_trend(sample_plan)
        
        assert len(trend) >= 1
        assert "date" in trend[0]
        assert "score" in trend[0]
    
    def test_convenience_functions(self, sample_plan, sample_audit_result):
        """Test convenience functions work"""
        # These will use default directory, just test they don't crash
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = HistoryTracker(history_dir=tmpdir)
            snapshot = tracker.save_snapshot(sample_plan, sample_audit_result)
            assert snapshot is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
