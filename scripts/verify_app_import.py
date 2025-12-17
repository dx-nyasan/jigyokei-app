
import sys
import os
from unittest.mock import MagicMock

# Mock streamlit before importing the app
sys.modules["streamlit"] = MagicMock()
sys.modules["streamlit.components.v1"] = MagicMock()

# Configure st.columns to return a list of mocks when unpacked
def mock_columns(spec):
    count = spec if isinstance(spec, int) else len(spec)
    return [MagicMock() for _ in range(count)]

sys.modules["streamlit"].columns.side_effect = mock_columns

# Configure st.button to return False (avoid entering interactive blocks during import)
sys.modules["streamlit"].button.return_value = False
sys.modules["streamlit"].chat_input.return_value = None

class MockSessionState(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)
    def __setattr__(self, key, value):
        self[key] = value

sys.modules["streamlit"].session_state = MockSessionState()
# Pre-populate required keys to avoid startup checks failing before assignment
sys.modules["streamlit"].session_state.session_manager = MagicMock()
sys.modules["streamlit"].secrets = {"APP_PASSWORD": "password"}
sys.modules["streamlit"].query_params = {}

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    print("Attempting to import src.frontend.app_hybrid...")
    import src.frontend.app_hybrid
    print("SUCCESS: app_hybrid imported successfully.")
except Exception as e:
    import traceback
    print(f"FAILURE: Import failed with error: {e}")
    traceback.print_exc()
    sys.exit(1)
