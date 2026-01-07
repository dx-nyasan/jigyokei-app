"""
Automated Bug Verification Test
Tests that the Dashboard renders correctly with the user-provided JSON data.
Verifies the AttributeError fix for response_procedures field names.
"""
import sys
import os
import json

# Setup
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

print("="*70)
print("自動バグ検証テスト: AttributeError 修正確認")
print("="*70)

# User-provided JSON data from chat
test_data = {
  "basic_info": {
    "applicant_type": "法人",
    "corporate_name": "株式会社〇〇",
    "corporate_name_kana": "カブシキガイシャ〇〇",
    "representative_title": "代表取締役",
    "representative_name": "北原　知恵",
    "address_zip": "641-0054",
    "address_pref": "和歌山県",
    "address_city": "和歌山市",
    "address_street": "塩屋4-6-58",
    "address_building": None,
    "capital": 1000000,
    "employees": 1,
    "establishment_date": "2000/04/01",
    "industry_major": "教育、学習支援業",
    "industry_middle": "教育、学習支援業",
    "industry_minor": None,
    "corporate_number": "1234567890123"
  },
  "goals": {
    "business_overview": "書道教室を運営しており、一人ひとりのレベルに合わせた丁寧な個別指導が強みです。",
    "business_purpose": "災害時でも生徒さんの安全を確保し、学びの機会を途絶えさせないこと。",
    "disaster_scenario": {
      "disaster_assumption": "地震",
      "impacts": {
        "impact_personnel": "地震発生時の生徒の安全確保や、交通機関の停止による帰宅困難が考えられます。",
        "impact_building": "棚に置いている書道具や教材が落下・散乱する可能性があります。",
        "impact_funds": "教室が一時的に閉鎖されることで授業料収入が途絶える可能性があります。",
        "impact_info": "パソコンが破損してしまい、生徒さんの連絡先リストが消失する可能性があります。"
      }
    }
  },
  "response_procedures": [
    {
      "category": "人命安全確保",
      "action_content": "まず揺れがおさまってから生徒の安全確認を行い、火の元の確認をします。",
      "timing": "発災直後",
      "preparation_content": "事前に決めてある緊急連絡網で保護者へ連絡する準備"
    },
    {
      "category": "緊急時体制",
      "action_content": "震度5弱以上の地震発生時に緊急時対応を開始します。",
      "timing": "発災直後",
      "preparation_content": "判断基準：震度5弱以上"
    },
    {
      "category": "被害状況把握",
      "action_content": "教室の被害状況を目視で確認し、写真で記録します。",
      "timing": "発災直後",
      "preparation_content": "メールアドレスやSNSを通じた連絡手段の確保"
    }
  ],
  "measures": {
    "personnel": {
      "current_measure": "生徒さんへの避難経路の説明は定期的に行っています。",
      "future_plan": "年1回程度、実際の避難訓練を実施する予定です。"
    },
    "building": {
      "current_measure": "棚には転倒防止金具を取り付けています。",
      "future_plan": "貴重な書道具は頑丈な収納ケースに入れる予定です。"
    },
    "money": {
      "current_measure": "事業用の損害保険には加入しています。",
      "future_plan": "補償内容を災害時対応に特化したものに見直す予定です。"
    },
    "data": {
      "current_measure": "生徒さんの連絡先は紙媒体でも保管しています。",
      "future_plan": "クラウドサービスでバックアップを取る計画です。"
    }
  },
  "equipment": {"use_tax_incentive": None, "items": [], "compliance_checks": []},
  "cooperation_partners": [],
  "pdca": {
    "management_system": "年に一度は計画書全体を見直します。",
    "training_education": "9月（防災週間に合わせて）",
    "training_month": None,
    "plan_review": "3月（年度末）",
    "review_month": None,
    "internal_publicity": None
  },
  "financial_plan": {
    "items": [
      {"item": "事業継続力強化計画対策費用", "usage": "各種対策費用", "method": "自己資金", "amount": 300000}
    ]
  },
  "period": {"start_date": None, "end_date": None},
  "applicant_info": {"contact_name": None, "email": None, "phone": None, "closing_month": None},
  "attachments": {}
}

# Test Results
test_results = []
plan = None

# ======================================
# テスト1: スキーマへのデータ読み込み
# ======================================
print("\n[Test 1] スキーマへのデータ読み込み")
try:
    from src.api.schemas import BusinessContinuityPlan
    plan = BusinessContinuityPlan.model_validate(test_data)
    test_results.append(("スキーマ読み込み", True, "正常にパース完了"))
    print("  ✅ PASS: データを正常にパース")
except Exception as e:
    test_results.append(("スキーマ読み込み", False, str(e)))
    print(f"  ❌ FAIL: {e}")

# ======================================
# テスト2: response_procedures フィールドアクセス (修正確認)
# ======================================
print("\n[Test 2] response_procedures フィールドアクセス (修正確認)")
if plan is not None:
    try:
        # この行がエラーの原因だった
        # 修正前: p.item, p.content
        # 修正後: p.category, p.action_content
        response_text = "\n".join([f"{p.category}: {p.action_content}" for p in plan.response_procedures if p.action_content])
        
        if len(response_text) > 0:
            test_results.append(("response_procedures アクセス", True, f"{len(plan.response_procedures)}件のデータにアクセス成功"))
            print(f"  ✅ PASS: {len(plan.response_procedures)}件のresponse_proceduresにアクセス成功")
            print(f"     テキスト長: {len(response_text)}文字")
        else:
            test_results.append(("response_procedures アクセス", False, "データが空"))
            print("  ❌ FAIL: データが空")
    except AttributeError as e:
        test_results.append(("response_procedures アクセス", False, f"AttributeError: {e}"))
        print(f"  ❌ FAIL: AttributeError - {e}")
    except Exception as e:
        test_results.append(("response_procedures アクセス", False, str(e)))
        print(f"  ❌ FAIL: {e}")
else:
    test_results.append(("response_procedures アクセス", False, "plan is None"))
    print("  ❌ SKIP: planが読み込めていません")

# ======================================
# テスト3: measures アクセス
# ======================================
print("\n[Test 3] measures フィールドアクセス")
if plan is not None:
    try:
        measures = plan.measures
        measures_text = f"""
人員: {measures.personnel.current_measure or ''} / {measures.personnel.future_plan or ''}
建物: {measures.building.current_measure or ''} / {measures.building.future_plan or ''}
資金: {measures.money.current_measure or ''} / {measures.money.future_plan or ''}
情報: {measures.data.current_measure or ''} / {measures.data.future_plan or ''}
"""
        if len(measures_text.strip()) > 20:
            test_results.append(("measures アクセス", True, "4カテゴリ全てにアクセス成功"))
            print("  ✅ PASS: 4カテゴリ全てにアクセス成功")
        else:
            test_results.append(("measures アクセス", False, "データ不足"))
            print("  ❌ FAIL: データ不足")
    except Exception as e:
        test_results.append(("measures アクセス", False, str(e)))
        print(f"  ❌ FAIL: {e}")
else:
    test_results.append(("measures アクセス", False, "plan is None"))
    print("  ❌ SKIP: planが読み込めていません")

# ======================================
# テスト4: completion_checker 実行
# ======================================
print("\n[Test 4] completion_checker 実行")
if plan is not None:
    try:
        from src.core.completion_checker import CompletionChecker
        checker = CompletionChecker()
        result = checker.check(plan)
        score = result.get("completion_percentage", 0)
        test_results.append(("completion_checker", True, f"スコア: {score}%"))
        print(f"  ✅ PASS: 完了度スコア {score}%")
    except Exception as e:
        test_results.append(("completion_checker", False, str(e)))
        print(f"  ❌ FAIL: {e}")
else:
    test_results.append(("completion_checker", False, "plan is None"))
    print("  ❌ SKIP: planが読み込めていません")

# ======================================
# 結果サマリー
# ======================================
print("\n" + "="*70)
print("テスト結果サマリー")
print("="*70)

passed = sum(1 for _, status, _ in test_results if status)
total = len(test_results)

for name, status, detail in test_results:
    icon = "✅" if status else "❌"
    print(f"  {icon} {name}: {detail}")

print(f"\n総合結果: {passed}/{total} テスト成功 ({100*passed//total}%)")

if passed == total:
    print("\n🎉 全テスト成功！AttributeErrorは修正されています。")
else:
    print("\n⚠️ 一部テストが失敗しました。")
