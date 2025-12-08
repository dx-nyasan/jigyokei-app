import json
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from src.api.schemas import ApplicationRoot
except ImportError:
    # Handle case where script is run from project root
    sys.path.append(os.path.abspath(os.path.join(os.getcwd(), 'src')))
    from src.api.schemas import ApplicationRoot

def validate_json_file(file_path):
    print(f"Testing {file_path}...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validation
        plan = ApplicationRoot.model_validate(data)
        print(f"[OK] Success: {file_path}")
        return True, None
    except Exception as e:
        print(f"[FAIL] Failed: {file_path}")
        print(f"   Error: {e}")
        return False, str(e)

def main():
    # Target directory
    base_dir = Path(r"C:\Users\kitahara\Desktop\script\jigyokei-app\scenarios NotebookLM\scenarios NotebookLM")
    files = [
        "basic_scenario.json",
        "level_1.json",
        "level_2.json",
        "level_3.json",
        "level_4.json",
        "level_5.json"
    ]
    
    results = {}
    
    for fname in files:
        fpath = base_dir / fname
        if fpath.exists():
            success, error = validate_json_file(fpath)
            results[fname] = {"success": success, "error": error}
        else:
            print(f"⚠️ File not found: {fpath}")
            results[fname] = {"success": False, "error": "File not found"}

    # Summary
    print("\n--- Summary ---")
    failure_count = sum(1 for r in results.values() if not r["success"])
    if failure_count == 0:
        print("All files passed validation.")
        sys.exit(0)
    else:
        print(f"{failure_count} files failed validation.")
        sys.exit(1)

if __name__ == "__main__":
    main()
