from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

class BasicInfo(BaseModel):
    company_name: str = Field(..., description="企業名")
    representative_name: Optional[str] = Field(None, description="代表者名")
    address: Optional[str] = Field(None, description="住所")
    phone_number: Optional[str] = Field(None, description="電話番号")
    business_type: Optional[str] = Field(None, description="業種（例：建設業、製造業）")

    @field_validator('company_name', 'representative_name', 'address', 'phone_number', 'business_type', mode='before')
    @classmethod
    def set_default_if_none(cls, v):
        return v if v else "未設定"

class BusinessContent(BaseModel):
    target_customers: Optional[str] = Field(None, description="顧客（誰に）")
    products_services: Optional[str] = Field(None, description="商品・サービス（何を）")
    delivery_methods: Optional[str] = Field(None, description="提供方法（どのように）")
    core_competence: Optional[str] = Field(None, description="自社の強み・重要な経営資源")

    @field_validator('*', mode='before')
    @classmethod
    def set_default_if_none(cls, v):
        return v if v else "未設定"

class DisasterRisk(BaseModel):
    risk_type: str = Field(..., description="想定する災害（例：大地震、水害）")
    impact_description: Optional[str] = Field(None, description="被害想定（事業への影響）")

    @field_validator('impact_description', mode='before')
    @classmethod
    def set_default_if_none(cls, v):
        return v if v else "未設定"

class MitigationMeasure(BaseModel):
    item: str = Field(..., description="点検・実施項目")
    content: Optional[str] = Field(None, description="具体的な対策内容")
    in_charge: Optional[str] = Field(None, description="担当者")
    deadline: Optional[str] = Field(None, description="実施時期")

    @field_validator('content', 'in_charge', 'deadline', mode='before')
    @classmethod
    def set_default_if_none(cls, v):
        return v if v else "未設定"

class QualityIssue(BaseModel):
    section: str
    field_name: str
    issue_type: str  # "missing", "insufficient_length", "insufficient_quantity"
    message: str
    severity: str # "critical" (must fix for application), "warning" (better to fix)

class JigyokeiPlan(BaseModel):
    basic_info: BasicInfo = Field(default_factory=lambda: BasicInfo(company_name="未設定"))
    business_content: BusinessContent = Field(default_factory=BusinessContent)
    disaster_risks: List[DisasterRisk] = Field(default_factory=list)
    pre_disaster_measures: List[MitigationMeasure] = Field(default_factory=list, description="事前対策（減災）")
    post_disaster_measures: List[MitigationMeasure] = Field(default_factory=list, description="事後対策（初動対応）")

    def progress_score(self) -> int:
        """
        厳格な進捗スコア計算 (0-100)
    def progress_score(self) -> int:
        """
        厳格な進捗スコア計算 (0-100)
        - Gatekeeper: 廃止 (GbizID連携のため)
        - Quantity & Quality: 文字数や項目数, フィールドの網羅性で加点
        """
        score = 0
        
        # 1. Basic Info (Base points, no gatekeeper)
        if self.basic_info.company_name != "未設定":
            score += 10
            
        # 2. Business Content (Max 30)
        bc = self.business_content
        if bc.products_services != "未設定":
            score += 10 if len(bc.products_services) >= 10 else 5
        if bc.target_customers != "未設定":
            score += 10
        if bc.delivery_methods != "未設定":
            score += 10
            
        # 3. Risks (Max 30)
        if self.disaster_risks:
            score += 10 # Existence
            # Quality Check (Specific Impact)
            detailed_impacts = [r for r in self.disaster_risks if len(r.impact_description) >= 15]
            if detailed_impacts:
                score += 20
            elif [r for r in self.disaster_risks if r.impact_description != "未設定"]:
                score += 10 # Valid but short
        
        # 4. Measures (Max 30)
        pre_count = len(self.pre_disaster_measures)
        if pre_count >= 3:
            score += 20
        else:
            score += pre_count * 5 # 5 pts per item up to 15
            
        post_count = len(self.post_disaster_measures)
        if post_count >= 1:
            score += 10
            
        return min(100, score)

    def check_quality(self) -> List[QualityIssue]:
        """
        データの品質をチェックし, 改善提案リストを返す.
        """
        issues = []
        
        # 1. Basic Info
        if self.basic_info.company_name == "未設定":
            issues.append(QualityIssue(section="基本情報", field_name="企業名", issue_type="missing", message="企業名が入力されていません。", severity="critical"))
        
        # 2. Business Content (Volume Check)
        bc = self.business_content
        if bc.products_services == "未設定":
            issues.append(QualityIssue(section="事業内容", field_name="商品・サービス", issue_type="missing", message="商品・サービスが入力されていません。", severity="warning"))
        elif len(bc.products_services) < 20: # 仮の閾値
             issues.append(QualityIssue(section="事業内容", field_name="商品・サービス", issue_type="insufficient_length", message=f"内容が具体的ではありません（現在{len(bc.products_services)}文字）。商品名や特徴を含めて詳しく記述してください。", severity="warning"))

        if bc.target_customers == "未設定":
             issues.append(QualityIssue(section="事業内容", field_name="顧客", issue_type="missing", message="主な顧客層が入力されていません。", severity="warning"))
        
        if bc.delivery_methods == "未設定":
             issues.append(QualityIssue(section="事業内容", field_name="提供方法", issue_type="missing", message="商品・サービスの提供方法（対面、配送、オンライン等）が入力されていません。", severity="warning"))

        # 3. Risks
        if not self.disaster_risks:
            issues.append(QualityIssue(section="災害リスク", field_name="全体", issue_type="missing", message="想定する災害リスクが1つも登録されていません。", severity="critical"))
        else:
            for r in self.disaster_risks:
                if r.impact_description == "未設定" or len(r.impact_description) < 10:
                    issues.append(QualityIssue(section="災害リスク", field_name=f"影響({r.risk_type})", issue_type="insufficient_length", message=f"「{r.risk_type}」への影響記述が具体的ではありません。停止する設備や期間、金額的損失などを追記してください。", severity="warning"))

        # 4. Measures
        if not self.pre_disaster_measures:
             issues.append(QualityIssue(section="事前対策", field_name="全体", issue_type="missing", message="事前対策が登録されていません。", severity="warning"))
        elif len(self.pre_disaster_measures) < 3:
             issues.append(QualityIssue(section="事前対策", field_name="全体", issue_type="insufficient_quantity", message=f"事前対策が{len(self.pre_disaster_measures)}件しかありません。ヒト・モノ・カネ・情報の観点から追加を検討してください。", severity="warning"))

        return issues
