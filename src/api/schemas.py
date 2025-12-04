from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from src.context_engine.schema import ContextData
from src.suggestion_engine.schema import SuggestionItem
from src.report_engine.schema import OmamoriReport
from src.transcription_engine.schema import MinutesData

# --- Existing Models ---

class TranscribeResponse(BaseModel):
    text: str

class AnalyzeRequest(BaseModel):
    text: str

class AnalyzeResponse(BaseModel):
    context: ContextData
    suggestions: List[SuggestionItem]

class ReportRequest(BaseModel):
    context: ContextData
    company_name: str
    staff_name: str

class ReportResponse(BaseModel):
    report: OmamoriReport
    html: str

class RAGSearchRequest(BaseModel):
    query: str
    collection_name: str = "knowledge_db"
    filter: Optional[dict] = None

class RAGSearchResponse(BaseModel):
    results: List[dict] # page_content, metadata

class MinutesRequest(BaseModel):
    transcript: str

class MinutesResponse(BaseModel):
    minutes: MinutesData

class FeedbackRequest(BaseModel):
    user_query: str
    ai_response: str
    retrieved_chunks: Optional[str] = None
    correction: Optional[str] = None
    quality_score: Optional[int] = None

class GenerateDocumentsRequest(BaseModel):
    context: ContextData
    questionnaire_data: dict
    company_name: str
    staff_name: str

class GenerateDocumentsResponse(BaseModel):
    report: OmamoriReport
    html: str
    form_data: dict # ApplicationForm as dict
    docx_url: str
    excel_url: str

# --- Jigyokei Application Models (SSOT Implementation) ---
# These models correspond to the definitions in src/core/definitions.py

class BasicInfo(BaseModel):
    """Section 1: Basic Information"""
    applicant_type: Literal["法人", "個人事業主"] = Field(..., description="申請種別")
    corporate_name: str = Field(..., description="事業者の氏名又は名称")
    corporate_name_kana: str = Field(..., description="事業者の氏名又は名称（フリガナ）")
    representative_title: str = Field(..., description="代表者の役職")
    representative_name: str = Field(..., description="代表者の氏名")
    address_zip: str = Field(..., description="郵便番号")
    address_pref: str = Field(..., description="都道府県")
    address_city: str = Field(..., description="市区町村")
    address_street: str = Field(..., description="住所（字・番地等）")
    address_building: Optional[str] = Field(None, description="マンション名等")
    capital: int = Field(..., description="資本金又は出資の額 (円)")
    employees: int = Field(..., description="常時使用する従業員の数 (人)")
    establishment_date: str = Field(..., description="設立年月日 (YYYY/MM/DD)")
    industry_major: str = Field(..., description="業種（大分類）")
    industry_middle: str = Field(..., description="業種（中分類）")
    industry_minor: Optional[str] = Field(None, description="業種（小分類）")
    corporate_number: Optional[str] = Field(None, description="法人番号")

class ImpactAssessment(BaseModel):
    """Nested model for DisasterScenario"""
    disaster_type: str = Field(..., description="想定する自然災害等")
    impact_personnel: str = Field(..., description="人員に関する影響")
    impact_building: str = Field(..., description="建物・設備に関する影響")
    impact_funds: str = Field(..., description="資金繰りに関する影響")
    impact_info: str = Field(..., description="情報に関する影響")
    impact_other: Optional[str] = Field(None, description="その他の影響")

class DisasterScenario(BaseModel):
    """Section 2: Disaster Assumptions & Impact"""
    disaster_assumption: str = Field(..., description="想定する自然災害等 (全体)")
    impact_list: List[ImpactAssessment] = Field(..., description="影響リスト")

class BusinessStabilityGoal(BaseModel):
    """Section 2: Goals"""
    business_overview: str = Field(..., description="自社の事業活動の概要")
    business_purpose: str = Field(..., description="事業継続力強化に取り組む目的")
    disaster_scenario: DisasterScenario = Field(..., description="災害想定と影響")

class FirstResponse(BaseModel):
    """Section 3: Response Procedures (Individual Item)"""
    category: str = Field(..., description="対応カテゴリ (例: 人命の安全確保)")
    action_content: str = Field(..., description="初動対応の内容")
    timing: str = Field(..., description="発災後の対応時期")
    preparation_content: str = Field(..., description="事前対策の内容")

class MeasureItem(BaseModel):
    """Section 3(2): Measures"""
    category: str = Field(..., description="対策カテゴリ (例: 人員体制の整備)")
    current_measure: str = Field(..., description="現在の取組")
    future_plan: str = Field(..., description="今後の計画")

class EquipmentItem(BaseModel):
    """Section 3(3): Equipment List Item"""
    name_model: str = Field(..., description="設備等の名称/型式")
    acquisition_date: str = Field(..., description="取得年月")
    location: str = Field(..., description="所在地")
    unit_price: int = Field(..., description="単価")
    quantity: int = Field(..., description="数量")
    amount: int = Field(..., description="金額")

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
    management_system: str = Field(..., description="平時の推進体制の整備")
    training_education: str = Field(..., description="訓練・教育の実施")
    plan_review: str = Field(..., description="計画の見直し")

class FinancialPlanItem(BaseModel):
    """Section 5: Financial Plan Item"""
    item: str = Field(..., description="実施事項")
    usage: str = Field(..., description="使途・用途")
    method: str = Field(..., description="資金調達方法")
    amount: int = Field(..., description="金額")

class FinancialPlan(BaseModel):
    """Section 5: Financial Plan Wrapper"""
    items: List[FinancialPlanItem] = Field(..., description="資金計画リスト")

class AttachmentsChecklist(BaseModel):
    """Section 4 & 5: Attachments & Checklist"""
    # Attachments are usually handled as file uploads, but we track metadata here
    check_sheet_uploaded: bool = Field(False, description="チェックシート添付済み")
    financial_risk_uploaded: bool = Field(False, description="財務リスク評価シート添付済み")
    existing_bcp_uploaded: bool = Field(False, description="既存BCP添付済み")
    
    # Checklist
    certification_compliance: bool = Field(..., description="認定要件への適合")
    no_false_statements: bool = Field(..., description="虚偽記載の不存在")
    not_anti_social: bool = Field(..., description="反社会的勢力非該当")
    not_cancellation_subject: bool = Field(..., description="取消事由非該当")
    legal_compliance: bool = Field(..., description="関係法令の遵守")
    sme_requirements: bool = Field(..., description="中小事業者の要件")
    registration_consistency: bool = Field(..., description="登記情報との一致確認")
    data_utilization_consent: Literal["可", "不可"] = Field(..., description="データ利活用への同意")
    case_publication_consent: Literal["可", "不可"] = Field(..., description="事例公表への同意")

class ApplicationRoot(BaseModel):
    """Root Model for the entire Jigyokei Application"""
    basic_info: BasicInfo
    goals: BusinessStabilityGoal
    response_procedures: List[FirstResponse]
    measures: List[MeasureItem]
    equipment: EquipmentList
    cooperation: List[CooperationPartner]
    pdca: PDCA
    financial_plan: FinancialPlan
    attachments: AttachmentsChecklist
