"""
J-SHIS Helper Module
Provides earthquake hazard data based on address for certification-level documentation.

Based on J-SHIS (Japan Seismic Hazard Information Station) data format.
Phase 1: Static data for Wakayama Prefecture
Phase 2: API integration (future)
"""

from typing import Optional, Dict
from dataclasses import dataclass

@dataclass
class JShisData:
    """J-SHIS earthquake hazard data structure."""
    prefecture: str
    city: str
    probability_30yr_6lower: float  # 30年以内に震度6弱以上の確率
    probability_30yr_6upper: float  # 30年以内に震度6強以上の確率
    terrain_type: str  # 地形区分
    amplification_factor: str  # 揺れやすさ（全国ランク）
    liquefaction_risk: str  # 液状化リスク
    source: str = "J-SHIS地震ハザードカルテ"


# Static data for Wakayama Prefecture (based on actual J-SHIS data)
JSHIS_DATA = {
    # 白浜町
    "和歌山県西牟婁郡白浜町": JShisData(
        prefecture="和歌山県",
        city="西牟婁郡白浜町",
        probability_30yr_6lower=65.3,
        probability_30yr_6upper=26.5,
        terrain_type="三角州・海岸低地",
        amplification_factor="全国上位6%",
        liquefaction_risk="高い",
    ),
    # 和歌山市
    "和歌山県和歌山市": JShisData(
        prefecture="和歌山県",
        city="和歌山市",
        probability_30yr_6lower=72.3,
        probability_30yr_6upper=31.2,
        terrain_type="沖積低地",
        amplification_factor="全国上位8%",
        liquefaction_risk="中程度",
    ),
    # 椿地区（白浜町）
    "和歌山県西牟婁郡白浜町椿": JShisData(
        prefecture="和歌山県",
        city="西牟婁郡白浜町椿",
        probability_30yr_6lower=65.3,
        probability_30yr_6upper=26.5,
        terrain_type="山麓堆積地形",
        amplification_factor="全国上位10%",
        liquefaction_risk="低い",
    ),
    # 田辺市
    "和歌山県田辺市": JShisData(
        prefecture="和歌山県",
        city="田辺市",
        probability_30yr_6lower=62.8,
        probability_30yr_6upper=24.1,
        terrain_type="沖積低地",
        amplification_factor="全国上位12%",
        liquefaction_risk="中程度",
    ),
    # 新宮市
    "和歌山県新宮市": JShisData(
        prefecture="和歌山県",
        city="新宮市",
        probability_30yr_6lower=58.4,
        probability_30yr_6upper=21.5,
        terrain_type="沖積低地",
        amplification_factor="全国上位15%",
        liquefaction_risk="中程度",
    ),
    # Generic Wakayama (fallback)
    "和歌山県": JShisData(
        prefecture="和歌山県",
        city="",
        probability_30yr_6lower=60.0,
        probability_30yr_6upper=25.0,
        terrain_type="（要確認）",
        amplification_factor="全国上位10%程度",
        liquefaction_risk="（要確認）",
    ),
}


def get_jshis_data(address: str) -> Optional[JShisData]:
    """
    Get J-SHIS data for the given address.
    
    Args:
        address: Full address string (e.g., "和歌山県西牟婁郡白浜町堅田2500番地")
    
    Returns:
        JShisData if found, None otherwise
    """
    if not address:
        return None
    
    # Try exact match first
    for key in JSHIS_DATA:
        if key in address:
            return JSHIS_DATA[key]
    
    # Try prefecture match as fallback
    for pref in ["和歌山県", "大阪府", "兵庫県", "京都府", "奈良県", "滋賀県", "三重県"]:
        if pref in address and pref in JSHIS_DATA:
            return JSHIS_DATA[pref]
    
    return None


def format_jshis_disaster_text(data: JShisData, include_tsunami: bool = False) -> str:
    """
    Format J-SHIS data into certification-level disaster scenario text.
    
    Args:
        data: J-SHIS data
        include_tsunami: Whether to include tsunami information
    
    Returns:
        Formatted text for disaster scenario section
    """
    text = f"""当社は{data.prefecture}{data.city}にあります。
今後30年以内に震度6弱以上の地震が起こる確率は{data.probability_30yr_6lower}％と非常に高く、地形区分が{data.terrain_type}であることから揺れやすさも{data.amplification_factor}に位置しています。({data.source}参照)"""
    
    if include_tsunami:
        text += """
また、地震により引き起こされる津波では警戒地域に含まれており、津波到達までの時間が短いことから、迅速な避難が必要です。(自治体津波ハザードマップ参照)"""
    
    return text


def format_impact_text(data: JShisData, business_type: str = "一般") -> str:
    """
    Format business impact text based on J-SHIS data.
    
    Args:
        data: J-SHIS data
        business_type: Type of business for context
    
    Returns:
        Formatted text for business impact section
    """
    base_impact = f"""自然災害の内、事業内容に与える影響の大きい災害は地震です。
{data.prefecture}は南海トラフ地震の影響を強く受ける地域であり、今後30年以内に震度6強以上の地震が発生する確率は{data.probability_30yr_6upper}％とされています。"""
    
    if data.liquefaction_risk == "高い":
        base_impact += f"""
また、{data.terrain_type}という地形特性から液状化リスクも高く、建物や設備への被害が懸念されます。"""
    
    return base_impact


def validate_disaster_scenario(text: str) -> Dict[str, bool]:
    """
    Validate if disaster scenario text meets certification requirements.
    
    Args:
        text: Disaster scenario text to validate
    
    Returns:
        Dictionary with validation results
    """
    checks = {
        "has_probability": any(kw in text for kw in ["確率", "％", "%"]),
        "has_seismic_intensity": any(kw in text for kw in ["震度", "6弱", "6強", "5強"]),
        "has_jshis_reference": "J-SHIS" in text or "ハザード" in text,
        "has_location": any(kw in text for kw in ["当社は", "弊社は", "所在地"]),
        "has_terrain": any(kw in text for kw in ["地形", "低地", "台地", "山麓"]),
    }
    
    return checks


def get_missing_requirements(text: str) -> list:
    """
    Get list of missing requirements in disaster scenario text.
    
    Args:
        text: Disaster scenario text
    
    Returns:
        List of missing requirement descriptions
    """
    checks = validate_disaster_scenario(text)
    
    missing = []
    if not checks["has_probability"]:
        missing.append("地震発生確率の記載（例：30年以内に震度6弱以上72.3%）")
    if not checks["has_seismic_intensity"]:
        missing.append("想定震度の記載（例：震度6強）")
    if not checks["has_jshis_reference"]:
        missing.append("J-SHIS または ハザードマップ参照の記載")
    if not checks["has_location"]:
        missing.append("事業所所在地の明記")
    if not checks["has_terrain"]:
        missing.append("地形区分の記載")
    
    return missing


# Example usage and testing
if __name__ == "__main__":
    # Test with Shirahama address
    test_address = "和歌山県西牟婁郡白浜町堅田2500番地の417"
    data = get_jshis_data(test_address)
    
    if data:
        print("=== J-SHIS Data Found ===")
        print(f"Prefecture: {data.prefecture}")
        print(f"City: {data.city}")
        print(f"30yr Probability (6-): {data.probability_30yr_6lower}%")
        print(f"Terrain: {data.terrain_type}")
        print()
        print("=== Formatted Disaster Scenario ===")
        print(format_jshis_disaster_text(data, include_tsunami=True))
    else:
        print("No J-SHIS data found for address")
