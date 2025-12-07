from typing import List, Optional, Literal
from pydantic import BaseModel, Field, validator

# --- Jigyokei Application Models (SSOT Implementation) ---
# These models correspond to the definitions in src/core/definitions.py

class BasicInfo(BaseModel):
    """Section 1: Basic Information"""
    applicant_type: str = Field("法人", description="申請種別") # Defaulting to Houjin to avoid validation error
    corporate_name: str = Field("", description="事業者の氏名又は名称")
    corporate_name_kana: str = Field("", description="事業者の氏名又は名称（フリガナ）")
    representative_title: str = Field("", description="代表者の役職")
    representative_name: str = Field("", description="代表者の氏名")
    address_zip: str = Field("", description="郵便番号")
    address_pref: str = Field("", description="都道府県")
    address_city: str = Field("", description="市区町村")
    address_street: str = Field("", description="住所（字・番地等）")
    address_building: Optional[str] = Field(None, description="マンション名等")
    capital: Optional[int] = Field(None, description="資本金又は出資の額 (円)")
    employees: Optional[int] = Field(None, description="常時使用する従業員の数 (人)")
    establishment_date: Optional[str] = Field(None, description="設立年月日 (YYYY/MM/DD)")
    industry_major: str = Field("", description="業種（大分類）")
    industry_middle: str = Field("", description="業種（中分類）")
    industry_minor: Optional[str] = Field(None, description="業種（小分類）")
    corporate_number: Optional[str] = Field(None, description="法人番号")

class ImpactAssessment(BaseModel):
    """Nested model for DisasterScenario"""
    disaster_type: str = Field("未設定", description="想定する自然災害等")
    impact_personnel: str = Field("", description="人員に関する影響")
    impact_building: str = Field("", description="建物・設備に関する影響")
    impact_funds: str = Field("", description="資金繰りに関する影響")
    impact_info: str = Field("", description="情報に関する影響")
    impact_other: Optional[str] = Field(None, description="その他の影響")

class DisasterScenario(BaseModel):
    """Section 2: Disaster Assumptions & Impact"""
    disaster_assumption: str = Field("未設定", description="想定する自然災害等 (全体)")
    impact_list: List[ImpactAssessment] = Field(default_factory=list, description="影響リスト")

class BusinessStabilityGoal(BaseModel):
    """Section 2: Goals"""
    business_overview: str = Field("", description="自社の事業活動の概要")
    business_purpose: str = Field("", description="事業継続力強化に取り組む目的")
    disaster_scenario: DisasterScenario = Field(default_factory=DisasterScenario, description="災害想定と影響")

class FirstResponse(BaseModel):
    """Section 3: Response Procedures (Individual Item)"""
    category: str = Field("未分類", description="対応カテゴリ (例: 人命の安全確保)")
    action_content: str = Field("", description="初動対応の内容")
    timing: str = Field("", description="発災後の対応時期")
    preparation_content: str = Field("", description="事前対策の内容")

class MeasureItem(BaseModel):
    """Section 3(2): Measures"""
    category: str = Field("未分類", description="対策カテゴリ (例: 人員体制の整備)")
    current_measure: str = Field("", description="現在の取組")
    future_plan: str = Field("", description="今後の計画")

class EquipmentItem(BaseModel):
    """Section 3(3): Equipment List Item"""
    name_model: str = Field("", description="設備等の名称/型式")
    acquisition_date: str = Field("", description="取得年月")
    location: str = Field("", description="所在地")
    unit_price: int = Field(0, description="単価")
    quantity: int = Field(0, description="数量")
    amount: int = Field(0, description="金額")

class EquipmentList(BaseModel):
    """Section 3(3): Equipment List Wrapper"""
    use_tax_incentive: bool = Field(False, description="税制優遇措置を活用する")
    items: List[EquipmentItem] = Field(default_factory=list, description="設備リスト")
    compliance_checks: List[str] = Field(default_factory=list, description="確認事項チェックリスト")

class CooperationPartner(BaseModel):
    """Section 4: Cooperation Partner"""
    name: Optional[str] = Field(None, description="名称")
    address: Optional[str] = Field(None, description="住所")
    representative: Optional[str] = Field(None, description="代表者の氏名")
    content: Optional[str] = Field(None, description="協力の内容")

class PDCA(BaseModel):
    """Section 5: PDCA"""
    management_system: str = Field("", description="平時の推進体制の整備")
    training_education: str = Field("", description="訓練・教育の実施")
    plan_review: str = Field("", description="計画の見直し")

class FinancialPlanItem(BaseModel):
    """Section 5: Financial Plan Item"""
    item: str = Field("", description="実施事項")
    usage: str = Field("", description="使途・用途")
    method: str = Field("", description="資金調達方法")
    amount: int = Field(0, description="金額")

class FinancialPlan(BaseModel):
    """Section 5: Financial Plan Wrapper"""
    items: List[FinancialPlanItem] = Field(default_factory=list, description="資金計画リスト")

class AttachmentsChecklist(BaseModel):
    """Section 4 & 5: Attachments & Checklist"""
    certification_compliance: bool = Field(False, description="認定要件への適合")
    no_false_statements: bool = Field(False, description="虚偽記載なし")
    not_anti_social: bool = Field(False, description="反社でないこと")
    not_cancellation_subject: bool = Field(False, description="認定取消対象でないこと")
    legal_compliance: bool = Field(False, description="法令適合")
    sme_requirements: bool = Field(False, description="中小企業要件")
    registration_consistency: bool = Field(False, description="登記と一致")
    data_utilization_consent: str = Field("不可", description="データ活用同意")
    case_publication_consent: str = Field("不可", description="事例公表同意")

class ApplicationRoot(BaseModel):
    """Root Model for the entire Application (SSOT)"""
    basic_info: BasicInfo = Field(default_factory=BasicInfo)
    goals: BusinessStabilityGoal = Field(default_factory=BusinessStabilityGoal)
    response_procedures: List[FirstResponse] = Field(default_factory=list)
    measures: List[MeasureItem] = Field(default_factory=list)
    equipment: EquipmentList = Field(default_factory=EquipmentList)
    cooperation_partners: List[CooperationPartner] = Field(default_factory=list)
    pdca: PDCA = Field(default_factory=PDCA)
    financial_plan: FinancialPlan = Field(default_factory=FinancialPlan)
    attachments: AttachmentsChecklist = Field(default_factory=AttachmentsChecklist)

