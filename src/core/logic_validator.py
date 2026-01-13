"""
Logic Validator for Section-to-Section Consistency Checks

This module provides cross-section validation to ensure logical consistency
across the entire Jigyokei application form.

Part of WS-1: Architecture Alignment 100% Initiative
"""

from typing import List, Dict, Any, Optional
from src.api.schemas import ApplicationRoot


class LogicValidator:
    """
    Validates logical consistency between different sections of the application.
    
    理念対応:
    - 「導く」: 論理的な改善提案を提示
    - 「透明性」: 整合性エラーの根拠を明示
    """
    
    # Disaster type to countermeasure keyword mapping (expanded from completion_checker)
    DISASTER_MEASURE_MAP = {
        "地震": {
            "keywords": ["耐震", "固定", "倒壊", "落下", "避難", "安否", "備蓄", "転倒防止", "免震"],
            "required_in": ["measures", "response_procedures"]
        },
        "水害": {
            "keywords": ["浸水", "止水", "排水", "土嚢", "避難", "高所", "防水", "嵩上げ"],
            "required_in": ["measures", "response_procedures"]
        },
        "台風": {
            "keywords": ["強風", "飛散", "防風", "養生", "避難", "停電", "補強"],
            "required_in": ["measures", "response_procedures"]
        },
        "停電": {
            "keywords": ["発電", "UPS", "バッテリー", "蓄電", "電源", "非常用電源", "自家発電"],
            "required_in": ["measures"]
        },
        "感染症": {
            "keywords": ["感染", "テレワーク", "消毒", "マスク", "リモート", "在宅", "衛生"],
            "required_in": ["measures"]
        }
    }
    
    # Training keywords for PDCA consistency
    TRAINING_KEYWORDS = ["訓練", "演習", "教育", "研修", "講習", "シミュレーション"]
    
    def __init__(self):
        self.warnings = []
        self.suggestions = []
    
    def validate(self, plan: ApplicationRoot) -> Dict[str, Any]:
        """
        Main entry point. Validates all cross-section consistencies.
        
        Returns:
            {
                "is_consistent": bool,
                "warnings": List[dict],  # {"section": str, "msg": str, "severity": str}
                "suggestions": List[str],
                "consistency_score": int  # 0-100
            }
        """
        self.warnings = []
        self.suggestions = []
        
        # Run all consistency checks
        self._check_disaster_to_measures(plan)
        self._check_measures_to_pdca(plan)
        self._check_basic_to_overview(plan)
        self._check_response_to_measures(plan)
        
        # Calculate consistency score
        max_checks = 4
        passed_checks = max_checks - len([w for w in self.warnings if w["severity"] == "critical"])
        consistency_score = int((passed_checks / max_checks) * 100)
        
        return {
            "is_consistent": len(self.warnings) == 0,
            "warnings": self.warnings,
            "suggestions": self.suggestions,
            "consistency_score": consistency_score
        }
    
    def _check_disaster_to_measures(self, plan: ApplicationRoot) -> None:
        """
        災害想定 → 事前対策の対応確認
        
        Checks if the assumed disasters have corresponding countermeasures.
        """
        disaster_text = plan.goals.disaster_scenario.disaster_assumption or ""
        
        # Collect all measure texts
        measure_texts = []
        if plan.measures.personnel:
            measure_texts.append(plan.measures.personnel.current_measure or "")
            measure_texts.append(plan.measures.personnel.future_plan or "")
        if plan.measures.building:
            measure_texts.append(plan.measures.building.current_measure or "")
            measure_texts.append(plan.measures.building.future_plan or "")
        if plan.measures.money:
            measure_texts.append(plan.measures.money.current_measure or "")
            measure_texts.append(plan.measures.money.future_plan or "")
        if plan.measures.data:
            measure_texts.append(plan.measures.data.current_measure or "")
            measure_texts.append(plan.measures.data.future_plan or "")
        
        all_measures_text = " ".join(measure_texts)
        
        # Check each disaster type
        for disaster_type, config in self.DISASTER_MEASURE_MAP.items():
            if disaster_type in disaster_text:
                # Check if any keyword exists in measures
                keyword_found = any(kw in all_measures_text for kw in config["keywords"])
                
                if not keyword_found:
                    self.warnings.append({
                        "section": "LogicConsistency",
                        "msg": f"災害想定「{disaster_type}」に対応する事前対策キーワード（{', '.join(config['keywords'][:3])}等）が見つかりません",
                        "severity": "warning"
                    })
                    self.suggestions.append(
                        f"「{disaster_type}」対策として、{config['keywords'][0]}や{config['keywords'][1]}などの具体的な対策を記載してください"
                    )
    
    def _check_measures_to_pdca(self, plan: ApplicationRoot) -> None:
        """
        事前対策 → PDCA体制の連携確認
        
        If measures include training-related content, PDCA should have training plan.
        """
        # Collect all measure texts
        measure_texts = []
        if plan.measures.personnel:
            measure_texts.append(plan.measures.personnel.current_measure or "")
            measure_texts.append(plan.measures.personnel.future_plan or "")
        
        all_measures_text = " ".join(measure_texts)
        
        # Check if measures mention training
        mentions_training = any(kw in all_measures_text for kw in self.TRAINING_KEYWORDS)
        
        if mentions_training:
            # Check if PDCA has training plan
            training_plan = plan.pdca.training_education or ""
            if not training_plan or training_plan == "未設定":
                self.warnings.append({
                    "section": "LogicConsistency",
                    "msg": "事前対策で訓練について言及していますが、PDCA体制に具体的な訓練計画がありません",
                    "severity": "warning"
                })
                self.suggestions.append(
                    "事前対策で言及した訓練内容をPDCA体制の「教育及び訓練」欄に具体的に記載してください"
                )
    
    def _check_basic_to_overview(self, plan: ApplicationRoot) -> None:
        """
        基本情報 → 事業概要の整合確認
        
        Checks if industry matches business overview content.
        """
        industry = plan.basic_info.industry_middle or plan.basic_info.industry_major or ""
        overview = plan.goals.business_overview or ""
        
        if not industry or not overview:
            return  # Skip if either is missing
        
        # Simple keyword matching for industry-overview consistency
        industry_keywords = {
            "製造": ["製造", "生産", "工場", "加工", "組立"],
            "建設": ["建設", "工事", "施工", "建築", "土木"],
            "卸売": ["卸売", "流通", "販売", "商品", "仕入"],
            "小売": ["小売", "販売", "店舗", "接客", "商品"],
            "飲食": ["飲食", "料理", "食事", "レストラン", "調理"],
            "サービス": ["サービス", "提供", "支援", "サポート"],
            "情報通信": ["IT", "情報", "システム", "ソフトウェア", "通信"],
        }
        
        for industry_type, keywords in industry_keywords.items():
            if industry_type in industry:
                keyword_found = any(kw in overview for kw in keywords)
                if not keyword_found:
                    self.warnings.append({
                        "section": "LogicConsistency",
                        "msg": f"業種「{industry}」と事業概要の内容に関連性が薄い可能性があります",
                        "severity": "info"
                    })
                    self.suggestions.append(
                        f"事業概要に{industry_type}業としての具体的な事業内容（例：{keywords[0]}、{keywords[1]}）を記載してください"
                    )
                break
    
    def _check_response_to_measures(self, plan: ApplicationRoot) -> None:
        """
        初動対応 → 事前対策の関連確認
        
        Checks if response procedures have corresponding preparation measures.
        """
        for procedure in plan.response_procedures:
            action = procedure.action_content or ""
            preparation = procedure.preparation_content or ""
            
            # Check if action mentions equipment but no preparation
            equipment_keywords = ["機器", "設備", "装置", "発電機", "ポンプ", "無線"]
            mentions_equipment = any(kw in action for kw in equipment_keywords)
            
            if mentions_equipment and (not preparation or preparation == "未設定"):
                self.warnings.append({
                    "section": "LogicConsistency",
                    "msg": f"初動対応「{action[:30]}...」で機器・設備を使用しますが、事前対策が記載されていません",
                    "severity": "warning"
                })
                self.suggestions.append(
                    "使用する機器・設備の事前準備（点検、保管場所の確保等）を事前対策に記載してください"
                )


def check_logic_consistency(plan: ApplicationRoot) -> Dict[str, Any]:
    """
    Convenience function for direct usage.
    
    Usage:
        from src.core.logic_validator import check_logic_consistency
        result = check_logic_consistency(plan)
    """
    validator = LogicValidator()
    return validator.validate(plan)
