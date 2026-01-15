"""
Unit tests for batch_processor.py

Task 3: New Module Tests
"""

import pytest
from src.core.batch_processor import BatchProcessor, BatchResult, get_sample_template


class TestBatchProcessor:
    """Tests for BatchProcessor class."""
    
    def test_processor_initialization(self):
        """Test BatchProcessor initializes correctly."""
        processor = BatchProcessor()
        assert processor.results == []
        assert processor.processed_count == 0
        assert processor.error_count == 0
    
    def test_validate_csv_columns_valid(self):
        """Test column validation with valid headers."""
        processor = BatchProcessor()
        headers = ["corporate_name", "address", "representative", "industry"]
        
        result = processor.validate_csv_columns(headers)
        
        assert result["valid"] is True
        assert result["missing"] == []
        assert "industry" in result["optional_found"]
    
    def test_validate_csv_columns_missing_required(self):
        """Test column validation with missing required columns."""
        processor = BatchProcessor()
        headers = ["corporate_name", "industry"]  # Missing address, representative
        
        result = processor.validate_csv_columns(headers)
        
        assert result["valid"] is False
        assert "address" in result["missing"]
        assert "representative" in result["missing"]
    
    def test_process_row_valid(self):
        """Test processing a valid row."""
        processor = BatchProcessor()
        row = {
            "corporate_name": "テスト株式会社",
            "address": "和歌山県白浜町",
            "representative": "山田太郎",
            "industry": "製造業",
            "employees": "10"
        }
        
        result = processor.process_row(row)
        
        assert result.corporate_name == "テスト株式会社"
        assert result.status in ["success", "partial"]
        assert result.score is not None
        assert result.data is not None
    
    def test_process_row_empty_name(self):
        """Test processing a row with empty corporate name."""
        processor = BatchProcessor()
        row = {
            "corporate_name": "",
            "address": "和歌山県",
            "representative": "山田"
        }
        
        result = processor.process_row(row)
        
        assert result.status == "error"
        assert "企業名が空です" in result.errors
    
    def test_process_batch_success(self):
        """Test processing a complete CSV batch."""
        processor = BatchProcessor()
        csv_content = """corporate_name,address,representative,industry
株式会社A,和歌山県白浜町,山田太郎,製造業
有限会社B,和歌山県田辺市,鈴木花子,小売業
"""
        
        result = processor.process_batch(csv_content)
        
        assert result["total"] == 2
        assert result["error"] == 0
        assert len(result["results"]) == 2
    
    def test_export_results_csv(self):
        """Test exporting results to CSV format."""
        processor = BatchProcessor()
        # Add some results
        processor.results = [
            BatchResult("会社A", "success", 75, None, None),
            BatchResult("会社B", "error", None, ["エラー1"], None)
        ]
        
        csv_output = processor.export_results_csv()
        
        assert "会社A" in csv_output
        assert "会社B" in csv_output
        assert "success" in csv_output
        assert "error" in csv_output


class TestBatchResult:
    """Tests for BatchResult dataclass."""
    
    def test_batch_result_creation(self):
        """Test BatchResult creation with all fields."""
        result = BatchResult(
            corporate_name="テスト会社",
            status="success",
            score=80,
            errors=None,
            data={"basic_info": {"corporate_name": "テスト会社"}}
        )
        
        assert result.corporate_name == "テスト会社"
        assert result.status == "success"
        assert result.score == 80


class TestUtilityFunctions:
    """Tests for utility functions."""
    
    def test_get_sample_template(self):
        """Test sample template generation."""
        template = get_sample_template()
        
        assert "corporate_name" in template
        assert "address" in template
        assert "representative" in template
        # Should have sample data rows
        assert "株式会社サンプル" in template
