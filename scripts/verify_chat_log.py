import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api.schemas import ApplicationRoot, FirstResponse, BasicInfo, BusinessStabilityGoal, DisasterScenario, PreDisasterMeasures, PDCA, FinancialPlan, AttachmentsChecklist
from src.core.completion_checker import CompletionChecker

def create_test_plan():
    """
    Constructs an ApplicationRoot object based on the User's provided Chat Log (Step 1135).
    Note: The chat log shows 'preparation_content' was NOT asked, so it strictly remains None/Empty.
    """
    plan = ApplicationRoot()
    
    # 1. Basic Info (Filled based on chat)
    plan.basic_info = BasicInfo(
        corporate_name="株式会社〇〇",
        corporate_name_kana="カブシキガイシャマルマル",
        corporate_number="1234567890123",
        address_zip="640-8511",
        address_pref="和歌山県",
        address_city="和歌山市",
        address_street="七番丁23番地",
        representative_title="代表取締役",
        representative_name="事業　継続",
        capital=1000000,
        employees=5,
        industry_major="建設業",
        industry_middle="総合工事業"
    )

    # 2. Goals (Filled)
    plan.goals = BusinessStabilityGoal()
    plan.goals.business_overview = "主にオフィスビルや商業施設の建設工事を請け負っています。..."
    plan.goals.business_purpose = "発災時においても従業員の安全を最優先とし..."
    plan.goals.disaster_scenario = DisasterScenario(disaster_assumption="地震")

    # 3. Response Procedures (The Critical Part)
    # Extracted from Chat:
    # Item 1: Safety
    # Item 2: HQ Setup
    # Item 3: Damage Assess
    # Note: preparation_content is implied to be MISSING in the chat log.
    plan.response_procedures = [
        FirstResponse(
            category="人命安全確保",
            action_content="まずは身の安全を確保し...",
            timing="発災直後",
            preparation_content=None # MISSING
        ),
        FirstResponse(
            category="緊急時体制",
            action_content="震度5強以上の地震が発生した場合...",
            timing="発災直後",
            preparation_content="" # MISSING (Empty string)
        ),
        FirstResponse(
            category="被害状況把握",
            action_content="まずは現場責任者が社用携帯で...",
            timing="発災直後",
            preparation_content="未設定" # MISSING (Placeholder)
        )
    ]

    # 4. Measures (Filled)
    plan.measures = PreDisasterMeasures() # (Simplified for this test, assuming populated to avoid noise)
    
    return plan

def verify_chat_log():
    print("--- Verifying Chat Log Data against CompletionChecker ---")
    plan = create_test_plan()
    
    # Run Analysis
    result = CompletionChecker.analyze(plan)
    
    # Check for ResponseProcedures Critical Error
    missing = result.get("missing_mandatory", [])
    
    print(f"Total Missing Items: {len(missing)}")
    
    found_prep_error = False
    for m in missing:
        print(f"[{m.get('severity')}] {m.get('section')}: {m.get('msg')}")
        if m.get('section') == "ResponseProcedures" and "preparation_content" in m.get('msg'):
            found_prep_error = True

    print("-" * 30)
    if found_prep_error:
        print("✅ SUCCESS: Missing 'preparation_content' was correctly flagged as a CRITICAL error.")
        print("   This confirms that the system will now require the user to answer this item.")
    else:
        print("❌ FAILURE: 'preparation_content' error was NOT found.")
        print("   The system might overlook the missing field.")

if __name__ == "__main__":
    verify_chat_log()
