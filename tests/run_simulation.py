import os
import sys
import json
import time

# プロジェクトルートをパスに追加して src モジュールをインポート可能にする
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from src.core.jigyokei_core import AIInterviewer
except ImportError as e:
    print(f"Error: Could not import AIInterviewer. Check your python path. {e}")
    sys.exit(1)

# APIキーの設定
if not os.getenv("GOOGLE_API_KEY"):
    print("Warning: GOOGLE_API_KEY is not set. Simulation might fail.")

# Rate Limiting
INTERVAL_SEC = 4

def run_simulation(scenario_path, output_path):
    print(f"--- Starting Simulation: {scenario_path} ---")
    
    # Init Manager
    try:
        manager = AIInterviewer()
    except Exception as e:
        print(f"Failed to initialize AIInterviewer: {e}")
        return

    print(f"--- Simulation Start (Interval: {INTERVAL_SEC}s) ---")
    
    # Load Scenario
    with open(scenario_path, 'r', encoding='utf-8') as f:
        scenario = json.load(f)

    for i, step in enumerate(scenario):
        user_input = step.get("input") or step.get("user_input")
        print(f"\n[Turn {i+1}] User (Persona: 経営者): {user_input}")
        
        # Send Message with Persona
        response = manager.send_message(user_input, persona="経営者")
        print(f"[Turn {i+1}] AI: {response[:100]}...")
        
        time.sleep(INTERVAL_SEC)

    print("\n--- Saving History ---")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"history": manager.history}, f, indent=2, ensure_ascii=False)
    print(f"Saved history to {output_path}")

    # Test Analysis
    print("\n--- Testing Analyze History ---")
    try:
        structure = manager.analyze_history()
        print("Analysis Result (Keys):", list(structure.keys()))
        
        analysis_path = os.path.splitext(output_path)[0] + "_analysis.json"
        with open(analysis_path, "w", encoding="utf-8") as f:
            json.dump(structure, f, indent=2, ensure_ascii=False)
        print(f"Saved analysis to {analysis_path}")
        
    except Exception as e:
        print(f"Analysis Failed: {e}")

    print(f"\n--- Simulation Complete. ---")

if __name__ == "__main__":
    scenario_file = os.path.join(os.path.dirname(__file__), 'scenarios', 'basic_scenario.json')
    output_file = os.path.join(os.path.dirname(__file__), 'output', 'simulation_result.json')
    
    # output dir check
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    run_simulation(scenario_file, output_file)
