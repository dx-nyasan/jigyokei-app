"""
Virtual Companies Scenario Test

10社の仮想事業者データを使用した完全シナリオテスト。
各社について計画作成→監査→下書きシート出力まで実行。
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Virtual Companies Data (10社)
VIRTUAL_COMPANIES = [
    {
        "id": 1,
        "name": "株式会社白浜観光",
        "industry": "観光業",
        "address": "和歌山県西牟婁郡白浜町1234-5",
        "representative": "山田 太郎",
        "employees": 15,
        "capital": 1000,
        "business_overview": "白浜温泉周辺の旅館・民宿運営、観光ガイドサービス、土産物販売を主業務とする。年間宿泊客数約5,000名。",
        "disaster_assumption": "南海トラフ地震により震度6弱以上の揺れが想定される。津波到達まで約15分。今後30年以内の発生確率は70-80%。",
        "measures": {
            "personnel": "従業員緊急連絡網の整備、年1回の避難訓練実施、多能工化の推進",
            "building": "耐震診断済み（Is値0.7）、家具転倒防止器具設置完了",
            "money": "地震保険・火災保険加入、1ヶ月分の運転資金確保",
            "data": "予約システムの日次クラウドバックアップ、顧客データの暗号化"
        },
        "training_month": "9月",
        "review_month": "3月"
    },
    {
        "id": 2,
        "name": "紀州精密工業株式会社",
        "industry": "製造業",
        "address": "和歌山県海南市日方1567",
        "representative": "鈴木 一郎",
        "employees": 45,
        "capital": 5000,
        "business_overview": "精密機械部品の製造・加工。主要取引先は自動車部品メーカー3社。CNC旋盤20台、マシニングセンタ10台を保有。",
        "disaster_assumption": "中央構造線断層帯による直下型地震を想定。震度6強の揺れにより工場設備の損傷リスクが高い。",
        "measures": {
            "personnel": "安否確認システム導入、クロストレーニングによる多能工化、BCP要員の指定",
            "building": "工場建屋の耐震補強完了（2024年）、設備アンカーボルト固定",
            "money": "売掛金保険加入、災害時融資枠3,000万円確保",
            "data": "生産管理システムの遠隔地バックアップ、図面データのクラウド保存"
        },
        "training_month": "6月",
        "review_month": "12月"
    },
    {
        "id": 3,
        "name": "有限会社田辺商店",
        "industry": "小売業",
        "address": "和歌山県田辺市新屋敷町45",
        "representative": "田辺 花子",
        "employees": 8,
        "capital": 300,
        "business_overview": "地域密着型スーパーマーケット。生鮮食品・日用品を販売。地元農家との直接取引により新鮮な野菜を提供。",
        "disaster_assumption": "大雨による河川氾濫を想定。店舗は浸水想定区域内にあり、最大2mの浸水リスク。",
        "measures": {
            "personnel": "災害時の営業継続判断基準を明文化、従業員への連絡手順書作成",
            "building": "冷蔵設備の高床設置、商品棚の補強、浸水対策土嚢の備蓄",
            "money": "水災保険加入、現金決済への一時切替準備",
            "data": "POSデータの日次クラウド同期、仕入先連絡リストの複数保管"
        },
        "training_month": "5月",
        "review_month": "11月"
    },
    {
        "id": 4,
        "name": "串本建設株式会社",
        "industry": "建設業",
        "address": "和歌山県東牟婁郡串本町789",
        "representative": "串本 次郎",
        "employees": 25,
        "capital": 2000,
        "business_overview": "地域の土木工事・建築工事を請け負う総合建設業。公共工事比率60%、民間工事40%。",
        "disaster_assumption": "南海トラフ地震による津波を想定。事務所は高台にあるが、資材置場は浸水区域内。",
        "measures": {
            "personnel": "現場作業員の安全確保手順、協力会社との連携体制構築",
            "building": "重機・車両の高台避難計画、資材の優先搬出リスト作成",
            "money": "工事保険の適用範囲確認、復旧工事受注に向けた資金準備",
            "data": "工事図面のデジタル化完了、積算データのバックアップ"
        },
        "training_month": "9月",
        "review_month": "3月"
    },
    {
        "id": 5,
        "name": "新宮運送株式会社",
        "industry": "運送業",
        "address": "和歌山県新宮市新宮456",
        "representative": "新宮 三郎",
        "employees": 35,
        "capital": 3000,
        "business_overview": "一般貨物運送業。中・長距離輸送が主力。保有車両：大型トラック15台、中型10台。",
        "disaster_assumption": "地震による道路寸断を想定。主要ルート（国道42号）が使用不能になるリスク。",
        "measures": {
            "personnel": "ドライバー安否確認の優先順位設定、緊急時の代替要員確保",
            "building": "車両の高台待避場所確保、燃料の優先確保契約",
            "money": "車両保険の見直し完了、荷主企業との災害時協定締結",
            "data": "配送管理システムのクラウド移行完了、顧客連絡先の二重化"
        },
        "training_month": "10月",
        "review_month": "4月"
    },
    {
        "id": 6,
        "name": "紀の川クリニック",
        "industry": "医療業",
        "address": "和歌山県紀の川市貴志川町123",
        "representative": "川口 医師",
        "employees": 12,
        "capital": 500,
        "business_overview": "内科・小児科を標榜する地域密着型クリニック。1日平均患者数50名。在宅医療も実施。",
        "disaster_assumption": "地震による停電・断水を想定。人工呼吸器使用患者3名の対応が最優先課題。",
        "measures": {
            "personnel": "医師・看護師の緊急出勤体制、患者搬送の優先順位リスト",
            "building": "非常用発電機導入（24時間対応）、医療機器の転倒防止",
            "money": "医療賠償責任保険の適用確認、診療報酬請求データのバックアップ",
            "data": "電子カルテのクラウドバックアップ、処方データの復旧手順確立"
        },
        "training_month": "11月",
        "review_month": "5月"
    },
    {
        "id": 7,
        "name": "和歌山ITソリューションズ株式会社",
        "industry": "IT業",
        "address": "和歌山県和歌山市本町234",
        "representative": "和歌 太一",
        "employees": 18,
        "capital": 1500,
        "business_overview": "中小企業向けシステム開発・保守。クラウドサービスの導入支援も実施。リモートワーク率80%。",
        "disaster_assumption": "地震によるオフィス使用不能を想定。サーバールームへのアクセス不可時の対応が課題。",
        "measures": {
            "personnel": "全社員リモートワーク可能体制、海外拠点（ベトナム）との連携",
            "building": "サーバーラック耐震固定、UPS設備（2時間対応）",
            "money": "サイバー保険加入、SLA違反時の補償準備金",
            "data": "全システムのAWS移行完了、コードリポジトリの地理冗長化"
        },
        "training_month": "8月",
        "review_month": "2月"
    },
    {
        "id": 8,
        "name": "磯野水産株式会社",
        "industry": "水産業",
        "address": "和歌山県有田市宮原町567",
        "representative": "磯野 波平",
        "employees": 20,
        "capital": 800,
        "business_overview": "鮮魚の仲買・加工・販売。地元漁協との連携により毎朝セリに参加。干物製造も手掛ける。",
        "disaster_assumption": "津波警報発令時の漁港からの緊急避難を想定。冷蔵設備への停電影響が課題。",
        "measures": {
            "personnel": "漁港作業員の避難経路確認、従業員家族の安否確認体制",
            "building": "冷凍庫の非常電源確保（48時間）、加工場の高台移転検討中",
            "money": "水産物の損害保険加入、取引先からの前払い制度導入",
            "data": "受発注データの日次バックアップ、取引履歴の紙媒体保管"
        },
        "training_month": "7月",
        "review_month": "1月"
    },
    {
        "id": 9,
        "name": "高野山宿坊 恵光院",
        "industry": "宿泊業",
        "address": "和歌山県伊都郡高野町高野山456",
        "representative": "恵光 住職",
        "employees": 10,
        "capital": 0,
        "business_overview": "高野山の宿坊として外国人観光客を中心に宿泊サービスを提供。精進料理・朝のお勤め体験が人気。",
        "disaster_assumption": "山間部のため土砂災害を想定。孤立時の宿泊客対応が最重要課題。",
        "measures": {
            "personnel": "外国語対応可能スタッフの確保、宿泊客避難誘導マニュアル",
            "building": "建物の耐震診断実施済み、非常食3日分備蓄",
            "money": "国際観光保険への切替、宿泊料前払い制度",
            "data": "予約システムのクラウド化、宿泊者名簿の複数管理"
        },
        "training_month": "4月",
        "review_month": "10月"
    },
    {
        "id": 10,
        "name": "みなべ梅園株式会社",
        "industry": "農業",
        "address": "和歌山県日高郡みなべ町晩稲789",
        "representative": "南部 梅子",
        "employees": 6,
        "capital": 200,
        "business_overview": "南高梅の生産・加工・販売。自社農園10ha、契約農家20軒。梅干し・梅酒の製造販売も実施。",
        "disaster_assumption": "台風・大雨による農園被害を想定。収穫期（6月）の被災が経営に与える影響が大きい。",
        "measures": {
            "personnel": "繁忙期の応援体制確保、高齢作業員の安全確保優先",
            "building": "加工場の排水設備強化、貯蔵庫の高床化",
            "money": "農業共済への加入、収入保険制度の活用",
            "data": "生産履歴のデジタル管理、取引先連絡情報の冗長化"
        },
        "training_month": "5月",
        "review_month": "11月"
    }
]


def create_plan_from_company(company: Dict[str, Any]):
    """会社データからApplicationRootを作成"""
    from src.api.schemas import ApplicationRoot
    
    plan = ApplicationRoot()
    
    # Basic Info
    plan.basic_info.corporate_name = company["name"]
    plan.basic_info.address = company["address"]
    plan.basic_info.representative_name = company["representative"]
    
    # Goals
    plan.goals.business_overview = company["business_overview"]
    plan.goals.disaster_scenario.disaster_assumption = company["disaster_assumption"]
    
    # Measures
    plan.measures.personnel.current_measure = company["measures"]["personnel"]
    plan.measures.building.current_measure = company["measures"]["building"]
    plan.measures.money.current_measure = company["measures"]["money"]
    plan.measures.data.current_measure = company["measures"]["data"]
    
    return plan


def run_audit(plan) -> Dict[str, Any]:
    """監査を実行"""
    from src.core.completion_checker import CompletionChecker
    checker = CompletionChecker(plan)
    return checker.check_completion()


def generate_draft_sheet(plan, audit_result, output_dir: Path, company_id: int, company_name: str) -> str:
    """下書きシートを生成"""
    from src.core.draft_exporter import DraftExporter
    
    exporter = DraftExporter(plan, audit_result)
    
    # Generate filename
    safe_name = company_name.replace(" ", "_").replace("株式会社", "").replace("有限会社", "")
    filename = f"draft_{company_id:02d}_{safe_name}.xlsx"
    filepath = output_dir / filename
    
    try:
        exporter.export_to_excel(str(filepath))
        return str(filepath)
    except Exception as e:
        # Fallback to JSON if Excel export fails
        json_path = output_dir / f"draft_{company_id:02d}_{safe_name}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                "company": company_name,
                "plan": plan.model_dump(),
                "audit": audit_result
            }, f, ensure_ascii=False, indent=2)
        return str(json_path)


def run_all_scenarios(output_dir: str = "test_outputs") -> List[Dict[str, Any]]:
    """全10社のシナリオテストを実行"""
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    results = []
    
    for company in VIRTUAL_COMPANIES:
        print(f"\n{'='*60}")
        print(f"Processing: {company['name']} ({company['industry']})")
        print(f"{'='*60}")
        
        # Step 1: Create plan
        plan = create_plan_from_company(company)
        
        # Step 2: Run audit
        audit_result = run_audit(plan)
        
        # Step 3: Generate draft
        filepath = generate_draft_sheet(
            plan, audit_result, output_path, 
            company["id"], company["name"]
        )
        
        # Record result
        result = {
            "id": company["id"],
            "name": company["name"],
            "industry": company["industry"],
            "address": company["address"],
            "employees": company["employees"],
            "score": audit_result.get("score", 0),
            "severity_counts": audit_result.get("severity_counts", {}),
            "output_file": filepath
        }
        results.append(result)
        
        print(f"  Score: {result['score']}")
        print(f"  Output: {filepath}")
    
    # Save summary
    summary_path = output_path / "scenario_test_summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump({
            "test_date": datetime.now().isoformat(),
            "total_companies": len(results),
            "results": results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*60}")
    print(f"All {len(results)} scenarios completed!")
    print(f"Summary saved to: {summary_path}")
    
    return results


if __name__ == "__main__":
    results = run_all_scenarios()
    
    print("\n" + "="*60)
    print("SCENARIO TEST RESULTS SUMMARY")
    print("="*60)
    
    for r in results:
        print(f"\n{r['id']:02d}. {r['name']}")
        print(f"    Industry: {r['industry']}")
        print(f"    Score: {r['score']}")
        print(f"    Output: {r['output_file']}")
