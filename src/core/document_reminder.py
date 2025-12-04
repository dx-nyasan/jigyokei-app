from typing import List, Dict, Optional

class DocumentReminder:
    """
    Manages the mapping between application fields and required physical documents.
    Used when a user skips a question in the chat.
    """
    
    # Mapping: Field Key (or Section) -> Required Document Name
    REMINDER_MAP = {
        # Basic Info
        "establishment_date": "履歴事項全部証明書（登記簿）",
        "capital": "履歴事項全部証明書（登記簿）",
        "representative_name": "履歴事項全部証明書（登記簿）",
        "address_street": "履歴事項全部証明書（登記簿）",
        
        # Financial / Goals
        "sales_amount": "直近の決算書", # Assuming this field exists or mapped to business_overview
        "profit": "直近の決算書",
        
        # Equipment
        "equipment_list": "設備のカタログ・見積書",
        
        # General fallback for sections
        "basic_info": "履歴事項全部証明書（登記簿）",
        "financial_plan": "直近の決算書",
    }

    def __init__(self):
        self.pending_documents: set = set()

    def check_reminder(self, field_key: str) -> Optional[str]:
        """
        Checks if skipping a field triggers a document reminder.
        Returns the document name if a reminder is needed, else None.
        """
        doc_name = self.REMINDER_MAP.get(field_key)
        if doc_name:
            self.pending_documents.add(doc_name)
            return doc_name
        return None

    def get_reminder_message(self, doc_name: str) -> str:
        """Returns a formatted message for the user."""
        return f"承知しました。当日は**『{doc_name}』**をご用意ください。支援担当者が確認して入力します。"

    def get_summary_list(self) -> List[str]:
        """Returns the list of all documents to bring."""
        return list(self.pending_documents)
