"""
API Key Validation Script
Tests if the GEMINI_API_KEY in .streamlit/secrets.toml is valid
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_api_key():
    # Load API key from secrets.toml
    try:
        import tomllib
        secrets_path = os.path.join(os.path.dirname(__file__), ".streamlit", "secrets.toml")
        with open(secrets_path, "rb") as f:
            secrets = tomllib.load(f)
        api_key = secrets.get("GEMINI_API_KEY") or secrets.get("GOOGLE_API_KEY")
        
        if not api_key:
            print("[FAIL] API key not found")
            return False
            
        print(f"[OK] API key loaded: {api_key[:10]}...{api_key[-4:]}")
        
    except Exception as e:
        print(f"[FAIL] secrets.toml error: {e}")
        return False
    
    # Test with google-generativeai (old library)
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content("Say 'Hello' in Japanese")
        
        print(f"[OK] API call successful!")
        print(f"     Response: {response.text[:100]}")
        return True
        
    except Exception as e:
        print(f"[FAIL] API call error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Gemini API Key Validation Test")
    print("=" * 50)
    result = test_api_key()
    print("=" * 50)
    print(f"Result: {'SUCCESS' if result else 'FAILED'}")
