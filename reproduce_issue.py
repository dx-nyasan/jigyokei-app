from unittest.mock import MagicMock
import json

def reproduction():
    mock_file = MagicMock()
    mock_file.type = "application/pdf"
    mock_file.read.return_value = b"fake_content"
    
    file_refs = [mock_file]
    contents = []
    
    for file_obj in file_refs:
        mime_type = file_obj.type
        file_obj.seek(0)
        blob = file_obj.read()
        print(f"Blob: {blob}")
        
        contents.append({
            "mime_type": mime_type,
            "data": blob
        })
        
    print(f"Contents: {contents}")

if __name__ == "__main__":
    reproduction()
