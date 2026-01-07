import os

os.makedirs(".streamlit", exist_ok=True)

# Write keys at TOP LEVEL (no [secrets] header)
content = """GOOGLE_API_KEY = "AIzaSyD46rENnIujx9ih8QShhpTf693wddewmZ0"
APP_PASSWORD = "30bousai"
"""

with open(".streamlit/secrets.toml", "w", encoding="utf-8") as f:
    f.write(content)

print("Successfully rewrote secrets.toml (FLAT structure).")
