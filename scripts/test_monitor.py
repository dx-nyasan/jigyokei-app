
import os
import sys
# Add project root to sys.path
sys.path.append(os.path.abspath(os.curdir))

from src.core.model_monitor import get_model_stats
import time

def simulate_logs():
    log_path = "docs/MODEL_FLIGHT_LOG.md"
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    
    # Append some simulated entries
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"| {timestamp} | test_task | gemini-2.5-flash | 1 | SUCCESS |\n")
        f.write(f"| {timestamp} | test_task | gemini-1.5-flash | 2 | SUCCESS |\n")
        f.write(f"| {timestamp} | test_task | gemini-1.5-flash-8b | 3 | ERROR: Quota Exceeded |\n")

def test_monitor():
    simulate_logs()
    stats = get_model_stats()
    print("--- Model Stats ---")
    if stats:
        print(f"Success Rate: {stats['success_rate']:.1f}%")
        print(f"Total Recent: {stats['total_recent']}")
        print(f"Tier Counts: {stats['tier_counts']}")
        print(f"Recent Errors: {len(stats['recent_errors'])}")
        assert stats['total_recent'] >= 3
        assert stats['success_rate'] > 0
        print("✅ Monitor Test Passed!")
    else:
        print("❌ Monitor Test Failed: No stats returned.")

if __name__ == "__main__":
    test_monitor()
