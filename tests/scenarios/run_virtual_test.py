"""
Virtual Companies Scenario Test Runner
10社の仮想事業者シナリオテスト（監査レポート・申請適合度判定付き）
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import json
from pathlib import Path
from datetime import datetime

# Virtual Companies Data
VIRTUAL_COMPANIES = [
    {"id": 1, "name": "白浜観光", "industry": "観光業", "address": "和歌山県白浜町", "representative": "山田 太郎", "employees": 15,
     "business_overview": "白浜温泉周辺の旅館運営、観光ガイドサービス",
     "disaster_assumption": "南海トラフ地震により震度6弱以上想定。津波到達約15分。",
     "measures": {"personnel": "緊急連絡網整備、年1回避難訓練", "building": "耐震診断済みIs値0.7", "money": "地震保険加入、1ヶ月運転資金確保", "data": "予約システム日次バックアップ"}},
    {"id": 2, "name": "紀州精密工業", "industry": "製造業", "address": "和歌山県海南市", "representative": "鈴木 一郎", "employees": 45,
     "business_overview": "精密機械部品製造、CNC旋盤20台保有",
     "disaster_assumption": "中央構造線断層帯直下型地震、震度6強想定",
     "measures": {"personnel": "安否確認システム導入、多能工化", "building": "工場耐震補強完了2024年", "money": "売掛金保険、融資枠3000万確保", "data": "生産管理システム遠隔バックアップ"}},
    {"id": 3, "name": "田辺商店", "industry": "小売業", "address": "和歌山県田辺市", "representative": "田辺 花子", "employees": 8,
     "business_overview": "地域密着型スーパー、生鮮食品・日用品販売",
     "disaster_assumption": "大雨による河川氾濫、最大2m浸水リスク",
     "measures": {"personnel": "営業継続判断基準明文化", "building": "冷蔵設備高床設置、土嚢備蓄", "money": "水災保険加入", "data": "POSデータ日次クラウド同期"}},
    {"id": 4, "name": "串本建設", "industry": "建設業", "address": "和歌山県串本町", "representative": "串本 次郎", "employees": 25,
     "business_overview": "土木・建築工事請負、公共工事60%",
     "disaster_assumption": "南海トラフ津波、資材置場浸水区域内",
     "measures": {"personnel": "現場作業員安全確保手順", "building": "重機高台避難計画", "money": "工事保険確認、復旧工事資金準備", "data": "工事図面デジタル化完了"}},
    {"id": 5, "name": "新宮運送", "industry": "運送業", "address": "和歌山県新宮市", "representative": "新宮 三郎", "employees": 35,
     "business_overview": "一般貨物運送、大型トラック15台保有",
     "disaster_assumption": "地震による国道42号寸断リスク",
     "measures": {"personnel": "ドライバー安否確認優先順位", "building": "車両高台待避場所確保", "money": "車両保険見直し完了", "data": "配送管理システムクラウド移行完了"}},
    {"id": 6, "name": "紀の川クリニック", "industry": "医療業", "address": "和歌山県紀の川市", "representative": "川口 医師", "employees": 12,
     "business_overview": "内科・小児科クリニック、在宅医療実施",
     "disaster_assumption": "地震停電・断水、人工呼吸器患者3名対応",
     "measures": {"personnel": "医師・看護師緊急出勤体制", "building": "非常用発電機24時間", "money": "医療賠償責任保険確認", "data": "電子カルテクラウドバックアップ"}},
    {"id": 7, "name": "和歌山ITソリューションズ", "industry": "IT業", "address": "和歌山県和歌山市", "representative": "和歌 太一", "employees": 18,
     "business_overview": "中小企業向けシステム開発、リモートワーク率80%",
     "disaster_assumption": "地震によるオフィス使用不能想定",
     "measures": {"personnel": "全社員リモートワーク可能", "building": "サーバーラック耐震固定、UPS2時間", "money": "サイバー保険加入", "data": "全システムAWS移行完了"}},
    {"id": 8, "name": "磯野水産", "industry": "水産業", "address": "和歌山県有田市", "representative": "磯野 波平", "employees": 20,
     "business_overview": "鮮魚仲買・加工・販売、干物製造",
     "disaster_assumption": "津波警報時漁港緊急避難、冷蔵設備停電影響",
     "measures": {"personnel": "漁港作業員避難経路確認", "building": "冷凍庫非常電源48時間", "money": "水産物損害保険加入", "data": "受発注データ日次バックアップ"}},
    {"id": 9, "name": "高野山宿坊恵光院", "industry": "宿泊業", "address": "和歌山県高野町", "representative": "恵光 住職", "employees": 10,
     "business_overview": "高野山宿坊、外国人観光客中心、精進料理提供",
     "disaster_assumption": "山間部土砂災害、孤立時宿泊客対応",
     "measures": {"personnel": "外国語対応スタッフ確保", "building": "耐震診断済み、非常食3日分", "money": "国際観光保険", "data": "予約システムクラウド化"}},
    {"id": 10, "name": "みなべ梅園", "industry": "農業", "address": "和歌山県みなべ町", "representative": "南部 梅子", "employees": 6,
     "business_overview": "南高梅生産・加工・販売、自社農園10ha",
     "disaster_assumption": "台風・大雨農園被害、6月収穫期被災リスク",
     "measures": {"personnel": "繁忙期応援体制確保", "building": "加工場排水強化、貯蔵庫高床化", "money": "農業共済・収入保険加入", "data": "生産履歴デジタル管理"}}
]

def assess_application_readiness(score, severity_counts):
    """申請適合度を判定"""
    critical = severity_counts.get("critical", 0)
    warning = severity_counts.get("warning", 0)
    
    if score >= 80 and critical == 0:
        return "A", "申請可能", "認定取得の見込みが高い"
    elif score >= 60 and critical <= 2:
        return "B", "軽微修正で申請可", "数項目の追記で認定可能"
    elif score >= 40:
        return "C", "要修正", "重要項目の追記が必要"
    else:
        return "D", "大幅修正要", "計画の見直しが必要"

def run_scenario_test():
    """10社シナリオテスト実行"""
    from src.api.schemas import ApplicationRoot
    from src.core.completion_checker import CompletionChecker
    
    results = []
    
    for company in VIRTUAL_COMPANIES:
        # Create plan
        plan = ApplicationRoot()
        plan.basic_info.corporate_name = company["name"]
        plan.basic_info.address_pref = company["address"].split("県")[0] + "県" if "県" in company["address"] else company["address"]
        plan.basic_info.address_city = company["address"].split("県")[1] if "県" in company["address"] else ""
        plan.basic_info.representative_name = company["representative"]
        plan.basic_info.employees = company["employees"]
        plan.basic_info.industry_major = company["industry"]
        plan.goals.business_overview = company["business_overview"]
        plan.goals.disaster_scenario.disaster_assumption = company["disaster_assumption"]
        plan.measures.personnel.current_measure = company["measures"]["personnel"]
        plan.measures.building.current_measure = company["measures"]["building"]
        plan.measures.money.current_measure = company["measures"]["money"]
        plan.measures.data.current_measure = company["measures"]["data"]
        
        # Run audit (CompletionChecker.analyze is a static/class method)
        audit = CompletionChecker.analyze(plan)
        
        # Get score - audit returns dict with total_score
        score = audit.get("total_score", audit.get("score", 0))
        severity = audit.get("severity_counts", {"critical": 0, "warning": 0})
        
        # Assess readiness
        grade, status, comment = assess_application_readiness(score, severity)
        
        results.append({
            "id": company["id"],
            "name": company["name"],
            "industry": company["industry"],
            "employees": company["employees"],
            "score": score,
            "severity_counts": severity,
            "grade": grade,
            "status": status,
            "comment": comment,
            "plan_summary": {
                "business": company["business_overview"][:50] + "...",
                "disaster": company["disaster_assumption"][:50] + "..."
            }
        })
    
    return results

if __name__ == "__main__":
    print("=" * 70)
    print("VIRTUAL COMPANIES SCENARIO TEST - 10社仮想事業者テスト")
    print("=" * 70)
    
    results = run_scenario_test()
    
    # Output results
    output_dir = Path("test_outputs")
    output_dir.mkdir(exist_ok=True)
    
    # Save JSON
    with open(output_dir / "scenario_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # Print summary
    for r in results:
        print(f"\n{r['id']:02d}. {r['name']} ({r['industry']})")
        print(f"    従業員: {r['employees']}名 | スコア: {r['score']} | 判定: {r['grade']}")
        print(f"    申請状況: {r['status']} - {r['comment']}")
    
    print("\n" + "=" * 70)
    print(f"Results saved to: {output_dir / 'scenario_results.json'}")
