import fitz
import os

files_to_analyze = [
    r"C:\Users\kitahara\Desktop\script\jigyokei-copilot\reap report\案件1_電子申請下書きシート　事業継続力強化計画.pdf",
    r"C:\Users\kitahara\Desktop\script\jigyokei-copilot\reap report\案件1_事業継続力強化計画申請書.pdf",
    r"C:\Users\kitahara\Desktop\script\jigyokei-copilot\reap report\案件1_添付_地震　KARTE-5035421931.pdf",
    r"C:\Users\kitahara\Desktop\script\jigyokei-copilot\reap report\案件2_071215申請内容.pdf",
    r"C:\Users\kitahara\Desktop\script\jigyokei-copilot\reap report\案件2_申請後_不備指摘.pdf",
    r"C:\Users\kitahara\Desktop\script\jigyokei-copilot\reap report\案件2_添付_地震ハザードカルテ.pdf",
    r"C:\Users\kitahara\Desktop\script\jigyokei-copilot\reap report\案件2_不備指摘後_修正申請.pdf"
]

def extract_text(path):
    if not os.path.exists(path):
        return f"File not found: {path}"
    try:
        doc = fitz.open(path)
        text = ""
        for page in doc:
            text += f"\n--- Page {page.number+1} ---\n"
            text += page.get_text()
        return text
    except Exception as e:
        return f"Error reading {path}: {str(e)}"

# Focus on specific keywords
keywords = ["震度", "津波", "液状化", "初動対応", "連携", "不備", "指摘", "入力内容を修正", "想定"]

for f in files_to_analyze:
    print(f"\nEXTRACTING: {os.path.basename(f)}")
    content = extract_text(f)
    # Print the first 10000 chars to avoid hitting output limits but get the meat
    # Actually, for the rejection comments and hazard reports, I need page content.
    print(content[:15000])
    print("\n" + "-"*40 + " END OF EXTRACT " + "-"*40 + "\n")
