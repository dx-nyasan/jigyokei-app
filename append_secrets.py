
# Valid UTF-8 append for secrets
content = '\nAPP_PASSWORD = "30bousai"'
with open(".streamlit/secrets.toml", "a", encoding="utf-8") as f:
    f.write(content)

print(f"Successfully appended APP_PASSWORD.")
