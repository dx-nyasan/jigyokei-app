import pytest
import sys
import json
import datetime
from pathlib import Path

# Config
TEST_DIR = "tests/e2e"
REPORT_DIR = "output/reports"

def run_e2e_tests():
    """Run Playwright tests and return result dict."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"{REPORT_DIR}/report_{timestamp}.json"
    
    # Ensure dir exists
    Path(REPORT_DIR).mkdir(parents=True, exist_ok=True)

    print(f"🚀 Starting Non-Stop Verification: {timestamp}")
    
    # Run pytest
    # -x: Fast fail
    # --json-report: (Requires pytest-json-report plugin if available, else parse output)
    # Here we use basic exit code for simplicity in this mock
    
    retcode = pytest.main(["-x", TEST_DIR])
    
    success = (retcode == 0)
    result = {
        "timestamp": timestamp,
        "success": success,
        "exit_code": retcode,
        "type": "E2E_BROWSER_TEST"
    }
    
    # Save Report
    with open(report_file, "w") as f:
        json.dump(result, f, indent=4)
        
    if success:
        print("✅ SUCCESS: All checks passed.")
        print(f"📄 Report saved to: {report_file}")
    else:
        print("❌ FAILURE: Issues detected.")
        print(f"📄 Report saved to: {report_file}")
        
    return success

if __name__ == "__main__":
    success = run_e2e_tests()
    sys.exit(0 if success else 1)
