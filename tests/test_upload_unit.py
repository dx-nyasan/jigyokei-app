
import unittest
from unittest.mock import MagicMock, patch
import os
import sys
from io import BytesIO

# プロジェクトルートへのパス追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.jigyokei_core import AIInterviewer

class MockUploadedFile:
    def __init__(self, name, type, content=b"dummy content"):
        self.name = name
        self.type = type
        self.content = content
    
    def getvalue(self):
        return self.content

class TestAIInterviewerUpload(unittest.TestCase):
    
    @patch('src.core.jigyokei_core.genai')
    @patch('src.core.jigyokei_core.st') # Streamlitのモック
    def test_process_files_pdf(self, mock_st, mock_genai):
        # Setup Mocks
        mock_model = MagicMock()
        mock_chat = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_model.start_chat.return_value = mock_chat
        
        # Mock API Key injection (to bypass env check if needed, though constructor handles it gracefully)
        # Actually AIInterviewer constructor reads st.secrets or os.getenv. 
        # We need to mock st.secrets or os.getenv slightly if we want to ensure model init.
        # But if api_key is missing, model is None. We verified code:
        # if api_key: init... else: model=None.
        # So we must ensure api_key is found.
        mock_st.secrets = {"GOOGLE_API_KEY": "dummy_key"}
        
        # Initialize
        interviewer = AIInterviewer()
        
        # Ensure model is initialized
        self.assertIsNotNone(interviewer.model)
        
        # Prepare Mock File
        pdf_file = MockUploadedFile("test_doc.pdf", "application/pdf")
        
        # Mock upload_file return
        mock_g_file = MagicMock()
        mock_g_file.name = "files/12345"
        mock_g_file.display_name = "test_doc.pdf"
        mock_genai.upload_file.return_value = mock_g_file
        
        # Execute
        # interviewer.uploaded_file_refs is now initialized in __init__

        # Wait, looking at the code, `self.uploaded_file_refs` is NOT initialized in __init__!
        # It seems like a bug in the provided code snippet of jigyokei_core.py line 114:
        # self.uploaded_file_refs.append(g_file)
        # If it's not in __init__, this will crash.
        # Let's verify this hypothesis by running the test.
        
        try:
            count = interviewer.process_files([pdf_file])
            print(f"Processed count: {count}")
        except AttributeError as e:
            print(f"Caught expected error if bug exists: {e}")
            self.fail(f"Bug found: {e}")

        # Assertions
        mock_genai.upload_file.assert_called()
        self.assertEqual(count, 1)
        # Check if chat message was sent
        mock_chat.send_message.assert_called()

if __name__ == '__main__':
    unittest.main()
