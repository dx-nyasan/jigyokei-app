import openpyxl
import os

EXCEL_PATH = r"C:\Users\kitahara\.gemini\antigravity\brain\b932dbb7-0ad2-4b11-b5b9-740aecb2a7ae\strict_evidence\core_verified_draft.xlsx"

KEYWORDS = [
    "昭和47年",
    "特殊旋盤加工",
    "三次元測定機",
    "葛飾区",
    "佐藤健二"
]

def verify_integrity():
    if not os.path.exists(EXCEL_PATH):
        print(f"❌ Excel file not found at {EXCEL_PATH}")
        return

    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
    found_keywords = {k: False for k in KEYWORDS}

    print("\n" + "="*40)
    print("Excel Integrity Verification")
    print("="*40)

    for sheet in wb.worksheets:
        for row in sheet.iter_rows(values_only=True):
            for cell in row:
                if cell and isinstance(cell, str):
                    for k in KEYWORDS:
                        if k in cell:
                            found_keywords[k] = True

    all_passed = True
    for k, found in found_keywords.items():
        status = "✅ Found" if found else "❌ Not Found"
        if not found: all_passed = False
        print(f"- {k}: {status}")

    print("="*40)
    if all_passed:
        print("🎯 FINAL JUDGMENT: PASS (Context Inheritance Verified)")
    else:
        print("⚠️ FINAL JUDGMENT: FAIL (Some data loss detected)")
    print("="*40 + "\n")

if __name__ == "__main__":
    verify_integrity()
