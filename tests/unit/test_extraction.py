import pytest
from unittest.mock import MagicMock, patch
import json
import os
from src.core.jigyokei_core import AIInterviewer

# Mock Streamlit secrets
@pytest.fixture
def mock_streamlit():
    with patch("streamlit.secrets", {"GOOGLE_API_KEY": "fake_key"}):
        yield

# Mock GenAI
@pytest.fixture
def mock_genai():
    with patch("google.generativeai.GenerativeModel") as MockModel:
        # Configuration mock
        with patch("google.generativeai.configure"):
            yield MockModel

def test_extract_structured_data_text_only(mock_streamlit, mock_genai):
    """Test extraction with text input"""
    
    # Setup Mock Response
    mock_instance = mock_genai.return_value
    mock_response = MagicMock()
    
    expected_data = {
        "basic_info": {
            "corporate_name": "Test Company",
            "address_city": "Tokyo"
        }
    }
    mock_response.text = json.dumps(expected_data)
    mock_instance.generate_content.return_value = mock_response

    # Execute
    interviewer = AIInterviewer()
    result = interviewer.extract_structured_data(text="Our company is Test Company in Tokyo.")

    # Verify
    assert result == expected_data
    
    # Check if prompt contained the text
    args, kwargs = mock_instance.generate_content.call_args
    # contents list check
    contents = args[0]
    assert any("Test Company" in str(c) for c in contents)

def test_extract_structured_data_with_file(mock_streamlit, mock_genai):
    """Test extraction with file input"""
    
    # Setup Mock File
    mock_file = MagicMock()
    mock_file.type = "application/pdf"
    mock_file.read.return_value = b"fake_pdf_content"
    
    # Setup Mock Response
    mock_instance = mock_genai.return_value
    mock_response = MagicMock()
    mock_response.text = json.dumps({"goals": {"business_overview": "PDF Content"}})
    mock_instance.generate_content.return_value = mock_response

    # Execute
    interviewer = AIInterviewer()
    result = interviewer.extract_structured_data(file_refs=[mock_file])

    # Verify
    assert result["goals"]["business_overview"] == "PDF Content"
    
    # Check if blob was passed
    args, _ = mock_instance.generate_content.call_args
    contents = args[0]
    # Look for dict with 'data' key
    print(f"DEBUG CONTENTS: {contents}")
    blob_entry = next((item for item in contents if isinstance(item, dict) and "data" in item), None)
    assert blob_entry is not None
    assert blob_entry["data"] == b"fake_pdf_content"
    assert blob_entry["mime_type"] == "application/pdf"
