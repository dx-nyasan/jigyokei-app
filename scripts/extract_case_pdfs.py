import pdfplumber
import os

report_dir = r'C:\Users\kitahara\Desktop\script\jigyokei-copilot\reap report'

# Key files to analyze
files = [
    '案件2_申請後_不備指摘.pdf',       # Rejection comments
    '案件2_071215申請内容.pdf',         # Initial (rejected) submission
    '案件2_不備指摘後_修正申請.pdf',     # Revised (approved) submission
    '案件1_事業継続力強化計画申請書.pdf', # Case 1 for comparison
]

for fname in files:
    fpath = os.path.join(report_dir, fname)
    if os.path.exists(fpath):
        print(f"\n{'='*80}")
        print(f"FILE: {fname}")
        print('='*80)
        try:
            with pdfplumber.open(fpath) as pdf:
                for i, page in enumerate(pdf.pages[:5]):  # First 5 pages
                    text = page.extract_text()
                    if text:
                        print(f"\n--- Page {i+1} ---")
                        print(text[:3000])
        except Exception as e:
            print(f"Error: {e}")
