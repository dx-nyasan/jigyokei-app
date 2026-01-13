"""
Batch Processor for Multi-Enterprise Processing

Task 5: Phase 3 Implementation
Enables CSV import for bulk enterprise data processing.
"""

import csv
import json
import io
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class BatchResult:
    """Result for a single enterprise in batch processing."""
    corporate_name: str
    status: str  # "success", "error", "partial"
    score: Optional[int] = None
    errors: Optional[List[str]] = None
    data: Optional[Dict] = None


class BatchProcessor:
    """
    Processes multiple enterprises from CSV import.
    
    理念対応:
    - 「寄り添い」: 商工会職員の業務効率化
    - 「引き出し」: 複数企業の一括データ収集
    """
    
    # Expected CSV columns
    REQUIRED_COLUMNS = [
        "corporate_name",  # 企業名
        "address",         # 住所
        "representative",  # 代表者名
    ]
    
    OPTIONAL_COLUMNS = [
        "industry",           # 業種
        "employees",          # 従業員数
        "phone",              # 電話番号
        "disaster_assumption", # 災害想定
        "business_overview",   # 事業概要
    ]
    
    def __init__(self):
        self.results: List[BatchResult] = []
        self.processed_count = 0
        self.error_count = 0
    
    def validate_csv_columns(self, headers: List[str]) -> Dict[str, Any]:
        """
        Validate CSV headers against required columns.
        
        Returns:
            {
                "valid": bool,
                "missing": List[str],
                "extra": List[str],
                "optional_found": List[str]
            }
        """
        headers_lower = [h.lower().strip() for h in headers]
        
        missing = [col for col in self.REQUIRED_COLUMNS 
                   if col.lower() not in headers_lower]
        
        optional_found = [col for col in self.OPTIONAL_COLUMNS 
                         if col.lower() in headers_lower]
        
        known_cols = self.REQUIRED_COLUMNS + self.OPTIONAL_COLUMNS
        extra = [h for h in headers if h.lower() not in [c.lower() for c in known_cols]]
        
        return {
            "valid": len(missing) == 0,
            "missing": missing,
            "extra": extra,
            "optional_found": optional_found
        }
    
    def parse_csv(self, csv_content: str) -> List[Dict[str, str]]:
        """
        Parse CSV content into list of dictionaries.
        
        Args:
            csv_content: Raw CSV string content
            
        Returns:
            List of row dictionaries
        """
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)
        return rows
    
    def process_row(self, row: Dict[str, str]) -> BatchResult:
        """
        Process a single row from CSV into ApplicationRoot format.
        
        Args:
            row: Dictionary of column->value
            
        Returns:
            BatchResult with processing outcome
        """
        corporate_name = row.get("corporate_name", "").strip()
        
        if not corporate_name:
            return BatchResult(
                corporate_name="(名称なし)",
                status="error",
                errors=["企業名が空です"]
            )
        
        try:
            # Build partial plan data
            plan_data = {
                "basic_info": {
                    "corporate_name": corporate_name,
                    "address": row.get("address", ""),
                    "representative_name": row.get("representative", ""),
                    "industry": row.get("industry", ""),
                    "employees": row.get("employees", ""),
                    "phone_number": row.get("phone", ""),
                },
                "goals": {
                    "disaster_scenario": {
                        "disaster_assumption": row.get("disaster_assumption", "")
                    },
                    "business_overview": row.get("business_overview", ""),
                }
            }
            
            # Calculate simple completeness score
            filled_fields = sum(1 for v in plan_data["basic_info"].values() if v)
            score = int((filled_fields / 6) * 100)
            
            return BatchResult(
                corporate_name=corporate_name,
                status="success" if score >= 50 else "partial",
                score=score,
                data=plan_data
            )
            
        except Exception as e:
            return BatchResult(
                corporate_name=corporate_name,
                status="error",
                errors=[str(e)]
            )
    
    def process_batch(self, csv_content: str) -> Dict[str, Any]:
        """
        Process entire CSV batch.
        
        Args:
            csv_content: Raw CSV string
            
        Returns:
            {
                "total": int,
                "success": int,
                "partial": int,
                "error": int,
                "results": List[BatchResult],
                "summary": str
            }
        """
        rows = self.parse_csv(csv_content)
        
        self.results = []
        success_count = 0
        partial_count = 0
        error_count = 0
        
        for row in rows:
            result = self.process_row(row)
            self.results.append(result)
            
            if result.status == "success":
                success_count += 1
            elif result.status == "partial":
                partial_count += 1
            else:
                error_count += 1
        
        self.processed_count = len(rows)
        self.error_count = error_count
        
        return {
            "total": len(rows),
            "success": success_count,
            "partial": partial_count,
            "error": error_count,
            "results": self.results,
            "summary": f"処理完了: {success_count}件成功, {partial_count}件部分完了, {error_count}件エラー"
        }
    
    def export_results_csv(self) -> str:
        """
        Export batch results to CSV format.
        
        Returns:
            CSV string with results
        """
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(["企業名", "ステータス", "スコア", "エラー"])
        
        # Data
        for result in self.results:
            writer.writerow([
                result.corporate_name,
                result.status,
                result.score if result.score else "",
                ", ".join(result.errors) if result.errors else ""
            ])
        
        return output.getvalue()


# Template for CSV import
SAMPLE_CSV_TEMPLATE = """corporate_name,address,representative,industry,employees,phone,disaster_assumption,business_overview
株式会社サンプル,和歌山県白浜町1234,山田太郎,製造業,10,0739-12-3456,地震・津波,当社は製造業を営んでいます
有限会社テスト,和歌山県田辺市5678,鈴木花子,小売業,5,0739-98-7654,台風・水害,小売業として地域に貢献
"""


def get_sample_template() -> str:
    """Get sample CSV template for user reference."""
    return SAMPLE_CSV_TEMPLATE
