from pydantic import BaseModel, Field
from typing import List, Optional

class BasicInfo(BaseModel):
    company_name: str = Field(..., description="企業名")
    representative_name: Optional[str] = Field(None, description="代表者名")
    address: Optional[str] = Field(None, description="住所")
    phone_number: Optional[str] = Field(None, description="電話番号")
    business_type: Optional[str] = Field(None, description="業種（例：建設業、製造業）")

class BusinessContent(BaseModel):
    target_customers: Optional[str] = Field(None, description="顧客（誰に）")
    products_services: Optional[str] = Field(None, description="商品・サービス（何を）")
    delivery_methods: Optional[str] = Field(None, description="提供方法（どのように）")
    core_competence: Optional[str] = Field(None, description="自社の強み・重要な経営資源")

class DisasterRisk(BaseModel):
    risk_type: str = Field(..., description="想定する災害（例：大地震、水害）")
    impact_description: Optional[str] = Field(None, description="被害想定（事業への影響）")

class MitigationMeasure(BaseModel):
    item: str = Field(..., description="点検・実施項目")
    content: str = Field(..., description="具体的な対策内容")
    in_charge: Optional[str] = Field(None, description="担当者")
    deadline: Optional[str] = Field(None, description="実施時期")

class JigyokeiPlan(BaseModel):
    basic_info: BasicInfo = Field(default_factory=lambda: BasicInfo(company_name="未設定"))
    business_content: BusinessContent = Field(default_factory=BusinessContent)
    disaster_risks: List[DisasterRisk] = Field(default_factory=list)
    pre_disaster_measures: List[MitigationMeasure] = Field(default_factory=list, description="事前対策（減災）")
    post_disaster_measures: List[MitigationMeasure] = Field(default_factory=list, description="事後対策（初動対応）")

    def progress_score(self) -> int:
        """
        簡易的な進捗スコア計算 (0-100)
        """
        score = 0
        total_points = 5  # 評価項目数

        if self.basic_info.company_name != "未設定": score += 1
        if self.business_content.products_services: score += 1
        if self.disaster_risks: score += 1
        if self.pre_disaster_measures: score += 1
        if self.post_disaster_measures: score += 1

        return int((score / total_points) * 100)
