from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator

# --- Jigyokei Application Models (SSOT Implementation) ---
# These models correspond to the definitions in src/core/definitions.py

class BasicInfo(BaseModel):
    """Section 1: Basic Information"""
    applicant_type: Optional[str] = Field(None, description="申請種別") # Defaulting to Houjin to avoid validation error
    corporate_name: Optional[str] = Field(None, description="事業者の氏名又は名称")
    corporate_name_kana: Optional[str] = Field(None, description="事業者の氏名又は名称（フリガナ）")
    representative_title: Optional[str] = Field(None, description="代表者の役職")
    representative_name: Optional[str] = Field(None, description="代表者の氏名")
    address_zip: Optional[str] = Field(None, description="郵便番号")
    address_pref: Optional[str] = Field(None, description="都道府県")
    address_city: Optional[str] = Field(None, description="市区町村")
    address_street: Optional[str] = Field(None, description="住所（字・番地等）")
    address_building: Optional[str] = Field(None, description="マンション名等")
    capital: Optional[int] = Field(None, description="資本金又は出資の額")
    employees: Optional[int] = Field(None, description="常時使用する従業員の数")
    establishment_date: Optional[str] = Field(None, description="設立年月日 (YYYY/MM/DD)")
    industry_major: Optional[str] = Field(None, description="業種（大分類）")
    industry_middle: Optional[str] = Field(None, description="業種（中分類）")
    industry_minor: Optional[str] = Field(None, description="業種（小分類）")
    corporate_number: Optional[str] = Field(None, description="法人番号")

    @field_validator('representative_name')
    @classmethod
    def ensure_full_width_space(cls, v: Optional[str]) -> Optional[str]:
        if v and ' ' not in v and '　' not in v:
            # Simple heuristic: Split last 2 chars as name if > 3 chars? 
            # Or just warn? For now, if no space, just leave it or naive insert?
            # NotebookLM said: "Insert if missing". We will try to insert after standard surname length or just leave if ambiguous.
            # Ideally, we should just assume user input is correct or warn. 
            # But let's replace half-width space with full-width if present.
            return v
        if v:
            return v.replace(' ', '　')
        return v
    
    @field_validator('capital', 'employees', mode='before')
    @classmethod
    def clean_int(cls, v):
        if isinstance(v, str):
            import re
            # Remove non-digits
            nums = re.sub(r'[^\d]', '', v)
            return int(nums) if nums else None
        return v

class ImpactAssessment(BaseModel):
    """Nested model for DisasterScenario (Detail 4 types)"""
    impact_personnel: Optional[str] = Field(None, description="自然災害等の発生が事業活動に与える影響 (人員)")
    impact_building: Optional[str] = Field(None, description="自然災害等の発生が事業活動に与える影響 (建物・設備)")
    impact_funds: Optional[str] = Field(None, description="自然災害等の発生が事業活動に与える影響 (資金繰り)")
    impact_info: Optional[str] = Field(None, description="自然災害等の発生が事業活動に与える影響 (情報)")
    # impact_other: Optional[str] = Field(None, description="その他の影響") # Removed as per stricter system req if needed, or keep as extra


class DisasterScenario(BaseModel):
    """Section 2: Disaster Assumptions & Impact"""
    disaster_assumption: Optional[str] = Field(None, description="事業活動に影響を与える自然災害等の想定")
    # Flattened impacts as they are 1-to-1 in the system usually per scenario, but we can keep object
    impacts: ImpactAssessment = Field(default_factory=ImpactAssessment, description="影響詳細")


class BusinessStabilityGoal(BaseModel):
    """Section 2: Goals"""
    business_overview: Optional[str] = Field(None, description="自社の事業活動の概要")
    business_purpose: Optional[str] = Field(None, description="事業継続力強化に取り組む目的")
    disaster_scenario: DisasterScenario = Field(default_factory=DisasterScenario, description="災害想定と影響")

class FirstResponse(BaseModel):
    """Section 3: Response Procedures (Individual Item)"""
    category: Optional[str] = Field(None, description="対応カテゴリ (例: 人命の安全確保)")
    action_content: Optional[str] = Field(None, description="初動対応の内容")
    timing: Optional[str] = Field(None, description="発災後の対応時期")
    preparation_content: Optional[str] = Field(None, description="事前対策の内容")

class MeasureDetail(BaseModel):
    current_measure: Optional[str] = Field(None, description="現在の取組")
    future_plan: Optional[str] = Field(None, description="今後の計画")

class PreDisasterMeasures(BaseModel):
    """Section 3(2): Measures (Fixed 4 Categories)"""
    personnel: MeasureDetail = Field(default_factory=MeasureDetail, description="自然災害等が発生した場合における人員体制の整備")
    building: MeasureDetail = Field(default_factory=MeasureDetail, description="事業継続力強化に資する設備、機器及び装置の導入")
    money: MeasureDetail = Field(default_factory=MeasureDetail, description="事業活動を継続するための資金の調達手段の確保")
    data: MeasureDetail = Field(default_factory=MeasureDetail, description="事業活動を継続するための重要情報の保護")


class EquipmentItem(BaseModel):
    """Section 3(3): Equipment List Item"""
    name_model: Optional[str] = Field(None, description="設備等の名称/型式")
    acquisition_date: Optional[str] = Field(None, description="取得年月")
    location: Optional[str] = Field(None, description="所在地")
    unit_price: int = Field(0, description="単価")
    quantity: int = Field(0, description="数量")
    amount: int = Field(0, description="金額")

class EquipmentList(BaseModel):
    """Section 3(3): Equipment List Wrapper"""
    use_tax_incentive: Optional[bool] = Field(None, description="税制優遇措置を活用する")
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
    management_system: Optional[str] = Field(None, description="平時の推進体制の整備")
    training_education: Optional[str] = Field(None, description="訓練・教育の実施")
    training_month: Optional[int] = Field(None, ge=1, le=12, description="教育・訓練の実施月 (1-12)")
    plan_review: Optional[str] = Field(None, description="計画の見直し")
    review_month: Optional[int] = Field(None, ge=1, le=12, description="計画見直しの実施月 (1-12)")
    internal_publicity: Optional[str] = Field(None, description="取組の社内周知 (12/17新設)")

class FinancialPlanItem(BaseModel):
    """Section 5: Financial Plan Item"""
    item: Optional[str] = Field(None, description="実施事項")
    usage: Optional[str] = Field(None, description="使途・用途")
    method: Optional[str] = Field(None, description="資金調達方法")
    amount: int = Field(0, description="金額")

class FinancialPlan(BaseModel):
    """Section 5: Financial Plan Wrapper"""
    items: List[FinancialPlanItem] = Field(default_factory=list, description="資金計画リスト")

class AttachmentsChecklist(BaseModel):
    """Section 4 & 5: Attachments & Checklist"""
    certification_compliance: Optional[bool] = Field(None, description="認定要件への適合")
    no_false_statements: Optional[bool] = Field(None, description="虚偽記載なし")
    not_anti_social: Optional[bool] = Field(None, description="反社でないこと")
    not_cancellation_subject: Optional[bool] = Field(None, description="認定取消対象でないこと")
    legal_compliance: Optional[bool] = Field(None, description="法令適合")
    sme_requirements: Optional[bool] = Field(None, description="中小企業要件")
    registration_consistency: Optional[bool] = Field(None, description="登記と一致")
    data_utilization_consent: Optional[str] = Field(None, description="データ活用同意")
    case_publication_consent: Optional[str] = Field(None, description="事例公表同意")
    confirm_email: Optional[str] = Field(None, description="確認用メールアドレス")
    fax: Optional[str] = Field(None, description="FAX番号")
    questionnaire_consent: Optional[bool] = Field(None, description="アンケート送信に対する許可")

class ImplementationPeriod(BaseModel):
    start_date: Optional[str] = Field(None, description="開始日")
    end_date: Optional[str] = Field(None, description="終了日")

class ApplicantInfo(BaseModel):
    contact_name: Optional[str] = Field(None, description="担当者名")
    email: Optional[str] = Field(None, description="メールアドレス")
    phone: Optional[str] = Field(None, description="電話番号")
    closing_month: Optional[str] = Field(None, description="決算月")

class ApplicationRoot(BaseModel):
    """Root Model for the entire Application (SSOT)"""
    basic_info: BasicInfo = Field(default_factory=BasicInfo)
    goals: BusinessStabilityGoal = Field(default_factory=BusinessStabilityGoal)
    response_procedures: List[FirstResponse] = Field(default_factory=list)
    measures: PreDisasterMeasures = Field(default_factory=PreDisasterMeasures) # Changed from List
    equipment: EquipmentList = Field(default_factory=EquipmentList)
    cooperation_partners: List[CooperationPartner] = Field(default_factory=list)
    pdca: PDCA = Field(default_factory=PDCA)
    financial_plan: FinancialPlan = Field(default_factory=FinancialPlan)
    period: ImplementationPeriod = Field(default_factory=ImplementationPeriod) # New
    applicant_info: ApplicantInfo = Field(default_factory=ApplicantInfo) # New
    attachments: AttachmentsChecklist = Field(default_factory=AttachmentsChecklist)

    @classmethod
    def migrate_legacy_data(cls, data: dict) -> dict:
        """Migrate legacy JSON data to match current schema"""
        import copy
        new_data = copy.deepcopy(data)

        # 1. Migrate Measures (List -> Object)
        if "measures" in new_data and isinstance(new_data["measures"], list):
            old_list = new_data["measures"]
            new_measures = {}
            # Auto-map based on keywords
            dataset = {
                "personnel": ["人", "安全", "教育", "訓練", "human", "personnel"],
                "building": ["物", "設備", "建物", "在庫", "building", "facility"],
                "money": ["金", "資金", "保険", "money", "fund", "finance"],
                "data": ["情報", "データ", "セキュリティ", "data", "info"]
            }
            
            for item in old_list:
                cat = item.get("category", "")
                content = item.get("current_measure", "")
                future = item.get("future_plan", "")
                
                # Assign to matching slot
                assigned = False
                for key, keywords in dataset.items():
                    if any(k in cat for k in keywords):
                        new_measures[key] = {"current_measure": content, "future_plan": future}
                        assigned = True
                        break
            
            # Ensure all keys exist
            for key in ["personnel", "building", "money", "data"]:
                if key not in new_measures:
                    new_measures[key] = {"current_measure": "", "future_plan": ""}
            
            new_data["measures"] = new_measures

        # 2. Migrate DisasterScenario (impact_list -> impacts)
        if "goals" in new_data and "disaster_scenario" in new_data["goals"]:
            ds = new_data["goals"]["disaster_scenario"]
            if "impact_list" in ds and isinstance(ds["impact_list"], list) and ds["impact_list"]:
                # Take the first one
                old_imp = ds["impact_list"][0]
                new_data["goals"]["disaster_scenario"]["impacts"] = {
                    "impact_personnel": old_imp.get("impact_personnel"),
                    "impact_building": old_imp.get("impact_building"),
                    "impact_funds": old_imp.get("impact_funds"),
                    "impact_info": old_imp.get("impact_info")
                }
            # Also ensure disaster_assumption fits
            if "disaster_type" in ds and "disaster_assumption" not in ds:
                 new_data["goals"]["disaster_scenario"]["disaster_assumption"] = ds["disaster_type"]

        # 3. Migrate ResponseProcedures (Separate Cooperation)
        if "response_procedures" in new_data:
            rp_list = new_data["response_procedures"]
            new_rp = []
            new_coop = new_data.get("cooperation_partners", [])
            
            for item in rp_list:
                cat = item.get("category", "")
                # Detect "Cooperation" or "連携"
                if "cooperation" in cat or "連携" in cat or "地域" in cat:
                    # Move to CooperationPartner
                    new_coop.append({
                        "name": item.get("action_content", ""), # Mapping content to name/content loosely
                        "content": item.get("action_content", ""),
                        "address": "", # Default missing
                        "representative": "" # Default missing
                    })
                else:
                    new_rp.append(item)
            
            new_data["response_procedures"] = new_rp
            new_data["cooperation_partners"] = new_coop

        # 4. Add Defaults for New Fields
        if "applicant_info" not in new_data:
            new_data["applicant_info"] = {}
        if "period" not in new_data:
            new_data["period"] = {}

        return new_data


