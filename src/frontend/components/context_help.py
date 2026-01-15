"""
Frontend Components: Context Help System

Task 5: Context Help Tooltips and Helper Icons
Provides user-friendly help messages for IT beginners.
"""

import streamlit as st
from typing import Optional, Dict


# Context help definitions for all major UI elements
CONTEXT_HELP = {
    # Basic Info Section
    "corporate_name": {
        "label": "企業名",
        "help": "正式名称で入力してください（例：株式会社○○商店）。登記上の名称と一致させると認定申請がスムーズです。",
        "example": "株式会社白浜観光"
    },
    "address": {
        "label": "所在地",
        "help": "郵便番号を入力すると自動で住所が補完されます。事業所が複数ある場合は主たる事業所の住所を入力してください。",
        "example": "和歌山県西牟婁郡白浜町1234-5"
    },
    "representative": {
        "label": "代表者名",
        "help": "代表取締役など、事業の最終責任者のお名前を入力してください。",
        "example": "山田太郎"
    },
    "employees": {
        "label": "従業員数",
        "help": "パートやアルバイトを含む総人数を入力してください。認定要件の判断に使用されます。",
        "example": "10名"
    },
    
    # Disaster Section
    "disaster_assumption": {
        "label": "災害想定",
        "help": "J-SHIS地震ハザードカルテの情報を参照して入力してください。「今後30年以内に震度6弱以上の地震が発生する確率は○○%」のような記載が認定審査で重視されます。",
        "example": "今後30年以内に震度6弱以上の地震が発生する確率は26.1%であり、地形区分が沖積低地であることから揺れやすさも全国上位に位置しています。"
    },
    "damage_assumption": {
        "label": "被害想定",
        "help": "「ヒト・モノ・カネ・情報」の4つの経営資源への影響を具体的に記載してください。",
        "example": "【ヒト】従業員の安否確認が必要【モノ】工場設備の損傷リスク【カネ】売上停止による資金繰り悪化【情報】サーバー停止リスク"
    },
    
    # Measures Section
    "personnel_measure": {
        "label": "ヒト（従業員）対策",
        "help": "従業員の安全確保や安否確認、多能工化などの対策を記載してください。",
        "example": "緊急連絡網の整備、安否確認システムの導入、従業員の多能工化推進"
    },
    "building_measure": {
        "label": "モノ（設備・建物）対策",
        "help": "建物の耐震診断、設備の転倒防止など、物理的な対策を記載してください。",
        "example": "耐震診断の実施、棚・設備の固定、消火器の適正配置"
    },
    "money_measure": {
        "label": "カネ（資金）対策",
        "help": "保険加入状況、融資枠の確保など、財務面の対策を記載してください。",
        "example": "地震保険・火災保険への加入維持、災害時融資枠の確保"
    },
    "data_measure": {
        "label": "情報（データ）対策",
        "help": "バックアップ方法、クラウド活用など、情報資産の保護対策を記載してください。",
        "example": "重要データの日次クラウドバックアップ、オフサイトバックアップの週次実施"
    },
    
    # Training Section
    "training_month": {
        "label": "訓練実施月",
        "help": "教育・訓練を実施する月を選択してください。電子申請で必須入力となっています。防災の日（9月）に合わせることをお勧めします。",
        "example": "9月"
    },
    "review_month": {
        "label": "計画見直し月",
        "help": "事業継続力強化計画の見直しを行う月を選択してください。年1回以上の見直しが推奨されています。",
        "example": "3月"
    },
    
    # Response Procedures
    "initial_response": {
        "label": "初動対応",
        "help": "発災直後（おおむね数時間以内）に行う対応を記載してください。人命安全の確保が最優先です。",
        "example": "①従業員の避難指示 ②安否確認の実施 ③設備の緊急停止"
    }
}


def get_field_help(field_key: str) -> str:
    """
    Get help text for a specific field.
    
    Args:
        field_key: Field identifier key
        
    Returns:
        Help text string
    """
    field_info = CONTEXT_HELP.get(field_key, {})
    return field_info.get("help", "")


def get_field_example(field_key: str) -> str:
    """
    Get example text for a specific field.
    
    Args:
        field_key: Field identifier key
        
    Returns:
        Example text string
    """
    field_info = CONTEXT_HELP.get(field_key, {})
    return field_info.get("example", "")


def render_help_icon(field_key: str) -> None:
    """
    Render help icon with tooltip for a field.
    
    Args:
        field_key: Field identifier key
    """
    help_text = get_field_help(field_key)
    if help_text:
        st.markdown(f"ℹ️", help=help_text)


def text_input_with_help(
    label: str,
    field_key: str,
    key: str,
    value: str = "",
    **kwargs
) -> str:
    """
    Render text input with integrated help tooltip.
    
    Args:
        label: Input label
        field_key: Field identifier for help lookup
        key: Streamlit widget key
        value: Default value
        **kwargs: Additional st.text_input arguments
        
    Returns:
        Input value string
    """
    help_text = get_field_help(field_key)
    return st.text_input(
        label,
        value=value,
        key=key,
        help=help_text if help_text else None,
        **kwargs
    )


def text_area_with_help(
    label: str,
    field_key: str,
    key: str,
    value: str = "",
    **kwargs
) -> str:
    """
    Render text area with integrated help tooltip.
    
    Args:
        label: Input label
        field_key: Field identifier for help lookup
        key: Streamlit widget key
        value: Default value
        **kwargs: Additional st.text_area arguments
        
    Returns:
        Input value string
    """
    help_text = get_field_help(field_key)
    return st.text_area(
        label,
        value=value,
        key=key,
        help=help_text if help_text else None,
        **kwargs
    )


def show_example_button(field_key: str, target_key: str) -> None:
    """
    Show button to insert example text into a field.
    
    Args:
        field_key: Field identifier for example lookup
        target_key: Session state key to update with example
    """
    example = get_field_example(field_key)
    if example and st.button("📝 例文を挿入", key=f"example_btn_{field_key}"):
        st.session_state[target_key] = example
        st.rerun()


def render_quick_help_panel() -> None:
    """
    Render expandable quick help panel with common questions.
    """
    with st.expander("❓ よくある質問（ヘルプ）", expanded=False):
        st.markdown("""
        **Q: J-SHISとは何ですか？**  
        A: 防災科学技術研究所が提供する地震ハザード情報サイトです。住所を入力するだけで地震発生確率を確認できます。
        
        **Q: 認定までどのくらいかかりますか？**  
        A: 電子申請から約1ヶ月程度です。不備がある場合は差し戻されることがあります。
        
        **Q: 従業員数に役員は含めますか？**  
        A: はい、役員も含めた全従業員数を入力してください。
        
        **Q: 複数の災害を想定する必要がありますか？**  
        A: 最低1つの自然災害の想定が必要です。地震を推奨しますが、地域特性に応じて水害等を追加できます。
        """)
