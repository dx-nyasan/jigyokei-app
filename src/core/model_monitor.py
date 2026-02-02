
import os
import pandas as pd
import re
from datetime import datetime, timedelta

def get_model_stats(log_path: str = "docs/MODEL_FLIGHT_LOG.md"):
    """
    Parses the flight log and returns statistics.
    """
    if not os.path.exists(log_path):
        return None

    try:
        # Read the markdown table
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # Extract data rows (skip header and separator)
        data_rows = []
        for line in lines:
            if "|" in line and ":---" not in line and "#" not in line and "Timestamp" not in line:
                # Clean up and split
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) == 5:
                    data_rows.append(parts)
        
        if not data_rows:
            return None

        df = pd.DataFrame(data_rows, columns=["Timestamp", "Task", "Model", "Tier", "Status"])
        df["Timestamp"] = pd.to_datetime(df["Timestamp"])
        df["Tier"] = pd.to_numeric(df["Tier"], errors='coerce')
        
        # Calculate stats
        last_24h = datetime.now() - timedelta(days=1)
        df_recent = df[df["Timestamp"] > last_24h]
        
        total_recent = len(df_recent)
        success_recent = len(df_recent[df_recent["Status"] == "SUCCESS"])
        success_rate = (success_recent / total_recent * 100) if total_recent > 0 else 100.0
        
        tier_counts = df_recent["Tier"].value_counts().to_dict()
        
        # Get EOL warnings (simulated check here or could be passed from commander)
        # For now, we reuse the MODEL_EOL mapping from commander logic if possible, 
        # but as a monitor, we just show what's in the log + any 'ERROR' statuses
        recent_errors = df_recent[df_recent["Status"].str.contains("ERROR", na=False)].to_dict('records')

        return {
            "total_recent": total_recent,
            "success_rate": success_rate,
            "tier_counts": tier_counts,
            "recent_errors": recent_errors,
            "latest_model": df.iloc[-1]["Model"] if not df.empty else "N/A"
        }
    except Exception as e:
        print(f"Monitor analysis failed: {e}")
        return None
