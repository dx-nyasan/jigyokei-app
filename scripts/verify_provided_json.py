import sys
import os
import json
from datetime import date

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api.schemas import ApplicationRoot
from src.core.completion_checker import CompletionChecker

def verify_json():
    print("--- Verifying Provided JSON Data ---")
    
    raw_data = {
      "basic_info": {
        "applicant_type": "法人",
        "corporate_name": "株式会社〇〇",
        "corporate_name_kana": "カブシキガイシャマルマル",
        "representative_title": "代表取締役",
        "representative_name": "事業　継続",
        "address_zip": "640-8511",
        "address_pref": "和歌山県",
        "address_city": "和歌山市",
        "address_street": "七番丁23番地",
        "address_building": "未設定",
        "capital": 1000000,
        "employees": 5,
        "establishment_date": "未設定",
        "industry_major": "建設業",
        "industry_middle": "総合工事業",
        "industry_minor": None,
        "corporate_number": "1234567890123"
      },
      "goals": {
        "business_overview": "主にオフィスビルや商業施設の建設工事を請け負っています。地域に根差した創業〇〇年の実績があり、地元の協力会社との強固なネットワークが当社の強みです。",
        "business_purpose": "発災時においても従業員の安全を最優先とし、地域社会への貢献を継続することです。発災後も速やかに事業を再開し、被災地のインフラ復旧に貢献できる体制を構築することです。",
        "disaster_scenario": {
          "disaster_assumption": "地震",
          "impacts": {
            "impact_personnel": "従業員が通勤困難になる、事務所建物内の設備落下により負傷者が出る可能性があると想定しています。",
            "impact_building": "事務所建物の軽微な損壊、倉庫内の資材の倒壊や散乱、重機の転倒・損傷の可能性があります。",
            "impact_funds": "建物や重機の修繕費用、事業中断による売上減少、協力会社への支払い遅延が発生する可能性があります。",
            "impact_info": "サーバーや社内PCの破損による顧客情報や設計データの消失、インターネット回線の不不通による業務システムの利用停止が想定されます。"
          }
        }
      },
      "response_procedures": [
        {
          "category": "人命安全確保",
          "action_content": "まずは身の安全を確保し、揺れがおさまった後に社内の一斉メールで安否確認を行う予定です。その後、指定の避難場所へ集合し、人数を確認します。",
          "timing": "発災直後",
          "preparation_content": None
        },
        {
          "category": "緊急時体制",
          "action_content": "震度5強以上の地震が発生した場合、代表取締役を本部長とし、現場責任者を集めて災害対策本部を設置します。",
          "timing": "発災直後",
          "preparation_content": None
        },
        {
          "category": "被害状況把握",
          "action_content": "まずは現場責任者が社用携帯で各建設現場の被害状況を目視で確認し、写真とともに本部に報告します。その後、必要に応じて主要取引先や発注元、自治体へ被害状況を連絡します。",
          "timing": "発災直後",
          "preparation_content": None
        }
      ],
      "measures": {
        "personnel": {
          "current_measure": "主要な業務について複数名が担当できるように多能工化を進めています。",
          "future_plan": "年に一度、安否確認システムの操作訓練と避難経路の確認訓練を実施したいと考えています。"
        },
        "building": {
          "current_measure": "事務所内の棚やキャビネットの固定は済ませています。",
          "future_plan": "万が一の停電に備えて、非常用発電機の導入を検討しています。"
        },
        "money": {
          "current_measure": "事務所と主要重機については損害保険に加入しています。",
          "future_plan": "〇ヶ月分の運転資金を手元資金として確保することを計画しています。"
        },
        "data": {
          "current_measure": "今は何もできていない。",
          "future_plan": "今後クラウドへ定期的にアップロードすることを業務に組み込んでいきたい。"
        }
      },
      "equipment": {
        "use_tax_incentive": False,
        "items": [],
        "compliance_checks": []
      },
      "cooperation_partners": [],
      "pdca": {
        "management_system": "年に一度、経営会議にて計画の進捗状況と課題を確認し、必要に応じて見直しを行います。",
        "training_education": "訓練は9月に実施する予定です。",
        "plan_review": "計画の見直しは1月に実施する予定です。"
      },
      "financial_plan": {
        "items": [
          {
            "item": "クラウド契約",
            "usage": "データバックアップ",
            "amount": 300000,
            "method": "自己資金" 
          },
          {
            "item": "非常用発電機",
            "usage": "停電対策",
            "amount": 0,
            "method": "事業者間で共同所有を検討"
          },
          {
            "item": "運転資金",
            "usage": "事業継続費用",
            "amount": 0,
            "method": "BCP認定後に金融機関に相談して検討を重ねていきたい"
          }
        ]
      },
      "period": {
        "start_date": None,
        "end_date": None
      },
      "applicant_info": {
        "contact_name": "経済　太郎",
        "email": "example@example.com",
        "phone": "090-1234-5678",
        "closing_month": None
      },
      "attachments": {
        "certification_compliance": True,
        "no_false_statements": True,
        "not_anti_social": True,
        "not_cancellation_subject": False,
        "legal_compliance": True,
        "sme_requirements": False,
        "registration_consistency": False,
        "data_utilization_consent": "未設定",
        "case_publication_consent": "未設定",
        "confirm_email": None,
        "fax": None,
        "questionnaire_consent": None
      }
    }

    print("Step 1: Loading JSON into ApplicationRoot schema...")
    try:
        plan = ApplicationRoot(**raw_data)
        print("✅ Data successfully loaded into Pydantic model.")
    except Exception as e:
        print(f"❌ Failed to load data: {e}")
        return

    print("\nStep 2: Running CompletionChecker...")
    result = CompletionChecker.analyze(plan)

    print(f"\n[Validation Result]")
    print(f"Mandatory Progress: {result['mandatory_progress'] * 100:.1f}%")
    
    print("\n[Missing Mandatory Items]")
    for item in result['missing_mandatory']:
        print(f"- {item['section']}: {item['msg']}")
        
    # Validation Logic
    missing_prep = False
    for item in result['missing_mandatory']:
        if "preparation_content" in item['msg']:
            missing_prep = True
            
    if missing_prep:
        print("\n✅ Verification SUCCESS: System correctly flagged 'preparation_content' as missing.")
    else:
        print("\n❌ Verification FAILURE: System FAILED to flag 'preparation_content'.")

if __name__ == "__main__":
    verify_json()
