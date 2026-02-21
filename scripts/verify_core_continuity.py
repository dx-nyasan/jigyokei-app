import asyncio
import os
import sys
from io import BytesIO

# Add project root to path
sys.path.append(os.getcwd())

from src.api.schemas import ApplicationRoot, BasicInfo, BusinessStabilityGoal, DisasterScenario
from src.core.draft_exporter import DraftExporter

STRICT_DIR = r"C:\Users\kitahara\.gemini\antigravity\brain\b932dbb7-0ad2-4b11-b5b9-740aecb2a7ae\strict_evidence"
os.makedirs(STRICT_DIR, exist_ok=True)

async def verify_continuity_core():
    print("--- Core Continuity Verification (Mock Hybrid) Start ---")
    
    # Plan object initialization
    plan = ApplicationRoot()
    
    # 1. Basic Info Injection (Directly from Sato Asset)
    plan.basic_info = BasicInfo(
        corporate_name="佐藤精密工業株式会社",
        representative_name="佐藤 健二",
        address_zip="124-0012",
        address_city="東京都葛飾区立石",
        establishment_date="1972-05-15",
        capital=10000000,
        employees=15
    )
    
    # 2. Goals Injection (Directly from Sato Asset)
    plan.goals.business_overview = "当社は葛飾区で50年以上続く町工場で、特殊旋盤加工を得意としています。主要取引先の工作機械メーカーへの安定供給が使命です。"
    plan.goals.disaster_scenario.disaster_assumption = "荒川の氾濫による大規模水害"
    
    # 3. Simulate AI Refinement (Sato's sandbags)
    print("Scene 4: Adding refined measure for water risk...")
    plan.measures.building.current_measure = "荒川の氾濫（浸水想定3m）に備え、全ての加工機を嵩上げ台に設置し、工場入口に止水板と土嚢を配備している。"
    
    # 4. Export to Excel using actual DraftExporter logic
    print("Scene 6: Exporting to Excel (application format)...")
    exporter = DraftExporter()
    excel_path = os.path.join(STRICT_DIR, "core_verified_draft.xlsx")
    
    try:
        # Use export_for_application method (Proves the SSOT mapping)
        excel_bytes_io = exporter.export_for_application(plan)
        with open(excel_path, "wb") as f:
            f.write(excel_bytes_io.getbuffer())
        print(f"  Export Success: {excel_path}")
    except Exception as e:
        print(f"  Export Failed: {e}")
        import traceback
        traceback.print_exc()

    print("--- Core Continuity Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(verify_continuity_core())
