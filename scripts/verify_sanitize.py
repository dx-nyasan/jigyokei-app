import re

def sanitize_content(text: str) -> str:
    if not text: return ""
    # 1. Remove <suggestions> tags (Robust regex)
    text = re.sub(r'<\s*suggestions\s*>.*?<\s*/\s*suggestions\s*>', '', text, flags=re.DOTALL)
    # 2. Remove HTML comments (Schema definitions)
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    # 3. Remove raw JSON blocks that look like extraction data
    text = re.sub(r'\{[^{}]*("parameter"|"company_name"|"business_overview")[^{}]*\}', '', text, flags=re.DOTALL)
    return text.strip()

def test_sanitization():
    print("--- Testing Sanitize Logic ---")
    
    # Case 1: Standard
    raw_1 = """
    Here is the response.
    <suggestions>
    {
        "options": ["A", "B"]
    }
    </suggestions>
    """
    cleaned_1 = sanitize_content(raw_1)
    print(f"Case 1 Result: '{cleaned_1}'")
    assert "<suggestions>" not in cleaned_1
    assert "options" not in cleaned_1
    assert "Here is the response." in cleaned_1

    # Case 2: Inline
    raw_2 = "Hello <suggestions>{...}</suggestions>"
    cleaned_2 = sanitize_content(raw_2)
    print(f"Case 2 Result: '{cleaned_2}'")
    assert cleaned_2 == "Hello"

    # Case 3: Messy spaces
    raw_3 = "End. < suggestions > { ... } < / suggestions >"
    cleaned_3 = sanitize_content(raw_3)
    print(f"Case 3 Result: '{cleaned_3}'")
    assert cleaned_3 == "End."

    print("✅ All Regex Tests Passed")

if __name__ == "__main__":
    test_sanitization()
