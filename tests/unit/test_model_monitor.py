"""
Unit tests for ModelMonitor.
Covers: Log parsing, statistics calculation, error handling.
TDD Compliance: Restores Red-Green cycle for model_monitor.py.
"""
import pytest
import os
import sys
import tempfile
from datetime import datetime, timedelta

# Add project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.core.model_monitor import get_model_stats


class TestModelMonitor:
    """Test suite for model_monitor module."""

    @pytest.fixture
    def temp_log_file(self):
        """Create a temporary flight log file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            now = datetime.now()
            f.write("# Model Flight Log\n\n")
            f.write("| Timestamp | Task | Model | Tier | Status |\n")
            f.write("| :--- | :--- | :--- | :--- | :--- |\n")
            f.write(f"| {now.strftime('%Y-%m-%d %H:%M:%S')} | reasoning | gemini-2.5-flash | 1 | SUCCESS |\n")
            f.write(f"| {now.strftime('%Y-%m-%d %H:%M:%S')} | draft | gemini-2.5-flash | 1 | SUCCESS |\n")
            f.write(f"| {now.strftime('%Y-%m-%d %H:%M:%S')} | extraction | gemini-1.5-flash | 2 | SUCCESS |\n")
            f.write(f"| {now.strftime('%Y-%m-%d %H:%M:%S')} | reasoning | gemini-1.5-flash | 2 | ERROR: Quota Exceeded |\n")
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)

    def test_get_model_stats_success(self, temp_log_file):
        """Test successful parsing of flight log."""
        stats = get_model_stats(temp_log_file)

        assert stats is not None
        assert stats['total_recent'] == 4
        assert stats['success_rate'] == 75.0  # 3/4 success

    def test_get_model_stats_tier_counts(self, temp_log_file):
        """Test tier count calculation."""
        stats = get_model_stats(temp_log_file)

        assert stats is not None
        tier_counts = stats['tier_counts']
        assert tier_counts.get(1, 0) == 2  # Two Tier 1 calls
        assert tier_counts.get(2, 0) == 2  # Two Tier 2 calls

    def test_get_model_stats_recent_errors(self, temp_log_file):
        """Test error detection."""
        stats = get_model_stats(temp_log_file)

        assert stats is not None
        assert len(stats['recent_errors']) == 1
        assert "Quota Exceeded" in stats['recent_errors'][0]['Status']

    def test_get_model_stats_nonexistent_file(self):
        """Test handling of nonexistent log file."""
        stats = get_model_stats("/nonexistent/path.md")

        assert stats is None

    def test_get_model_stats_empty_file(self):
        """Test handling of empty log file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("# Model Flight Log\n\n")
            f.write("| Timestamp | Task | Model | Tier | Status |\n")
            f.write("| :--- | :--- | :--- | :--- | :--- |\n")
            temp_path = f.name

        try:
            stats = get_model_stats(temp_path)
            assert stats is None  # No data rows
        finally:
            os.unlink(temp_path)

    def test_get_model_stats_latest_model(self, temp_log_file):
        """Test extraction of latest model used."""
        stats = get_model_stats(temp_log_file)

        assert stats is not None
        assert stats['latest_model'] == "gemini-1.5-flash"
