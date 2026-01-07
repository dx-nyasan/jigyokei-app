"""
Case 1 Complete Improvement Verification
Uses Gemini API for accurate PDF text extraction and comparison.
"""
import os
import sys
import google.generativeai as genai

# Setup
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

REAP_REPORT_DIR = r"C:\Users\kitahara\Desktop\script\jigyokei-copilot\reap report"

# Configure Gemini API key from secrets.toml
def load_api_key():
    import tomllib
    secrets_path = os.path.join(PROJECT_ROOT, ".streamlit", "secrets.toml")
    with open(secrets_path, "rb") as f:
        secrets = tomllib.load(f)
    return secrets.get("GEMINI_API_KEY") or secrets.get("GOOGLE_API_KEY")

api_key = load_api_key()
if api_key:
    genai.configure(api_key=api_key)
else:
    print("ERROR: No API key found in secrets.toml")
    sys.exit(1)



def extract_pdf_with_gemini(pdf_path: str, extraction_prompt: str) -> str:
    """
    Extract structured text from PDF using Gemini's vision capabilities.
    """
    import base64
    
    # Read PDF as binary
    with open(pdf_path, "rb") as f:
        pdf_data = f.read()
    
    # Upload to Gemini
    print(f"Uploading: {os.path.basename(pdf_path)}")
    
    # Use file upload API
    uploaded_file = genai.upload_file(pdf_path, mime_type="application/pdf")
    
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    response = model.generate_content([
        uploaded_file,
        extraction_prompt
    ])
    
    # Clean up uploaded file
    genai.delete_file(uploaded_file.name)
    
    return response.text


def extract_case1_draft():
    """Extract Case 1 draft sheet content."""
    pdf_path = os.path.join(REAP_REPORT_DIR, "案件1_電子申請下書きシート　事業継続力強化計画.pdf")
    
    prompt = """
    この電子申請下書きシートから、以下のセクションの内容を正確に抽出してください：
    
    1. 事業者情報（企業名、代表者名、住所等）
    2. 事業活動の概要
    3. 自然災害等の想定（災害の種類、想定内容）
    4. 事業活動に与える影響（ヒト・モノ・カネ・情報への影響）
    5. 初動対応の取組内容
    6. 平時の推進体制（PDCA）
    
    各セクションについて、記載されている内容をそのまま抽出してください。
    記載がないセクションは「未記載」と明記してください。
    
    日本語で出力してください。
    """
    
    return extract_pdf_with_gemini(pdf_path, prompt)


def extract_case1_final():
    """Extract Case 1 approved application content."""
    pdf_path = os.path.join(REAP_REPORT_DIR, "案件1_事業継続力強化計画申請書.pdf")
    
    prompt = """
    この認定済み事業継続力強化計画申請書から、以下のセクションの内容を正確に抽出してください：
    
    1. 事業者情報（企業名、代表者名、住所等）
    2. 事業活動の概要
    3. 自然災害等の想定（災害の種類、想定内容）
    4. 事業活動に与える影響（ヒト・モノ・カネ・情報への影響）
    5. 初動対応の取組内容
    6. 平時の推進体制（PDCA）
    
    各セクションについて、記載されている内容をそのまま抽出してください。
    
    特に以下の点に注目してください：
    - 災害想定の具体的な数値（震度、確率、津波到達時間等）
    - 事業影響の因果関係（物理的被害→事業停止の繋がり）
    - PDCA体制の「教育及び訓練」の記載
    
    日本語で出力してください。
    """
    
    return extract_pdf_with_gemini(pdf_path, prompt)


def compare_and_identify_gaps(draft_content: str, final_content: str) -> dict:
    """
    Compare draft and final to identify what improvements were needed.
    """
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    prompt = f"""
    以下は同じ案件の「下書きシート（改善前）」と「認定済み申請書（最終版）」の内容です。
    
    【下書きシート（改善前）】
    {draft_content}
    
    【認定済み申請書（最終版）】
    {final_content}
    
    下書きから最終版への改善点を分析し、以下のJSON形式で出力してください：
    
    {{
        "gaps": [
            {{
                "section": "セクション名",
                "draft_issue": "下書きの問題点",
                "final_improvement": "最終版での改善内容",
                "improvement_type": "追加/修正/具体化のいずれか",
                "certification_requirement": "この改善が満たす認定要件"
            }}
        ],
        "key_additions": [
            "最終版で追加された重要な情報1",
            "最終版で追加された重要な情報2"
        ],
        "improvement_summary": "改善の要約（日本語100文字以内）"
    }}
    
    必ずJSON形式のみで出力してください。
    """
    
    response = model.generate_content(prompt)
    
    import json
    import re
    
    # Extract JSON from response
    text = response.text
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except:
            return {"error": "JSON parse failed", "raw": text}
    
    return {"error": "No JSON found", "raw": text}


def main():
    print("="*70)
    print("案件1 完全改善検証: Gemini API による精密PDF解析")
    print("="*70)
    
    print("\n[Step 1] 下書きシート（改善前）を抽出中...")
    draft_content = extract_case1_draft()
    print(f"抽出完了: {len(draft_content)} 文字")
    
    print("\n[Step 2] 認定済み申請書（最終版）を抽出中...")
    final_content = extract_case1_final()
    print(f"抽出完了: {len(final_content)} 文字")
    
    print("\n[Step 3] 差分分析中...")
    gaps = compare_and_identify_gaps(draft_content, final_content)
    
    print("\n" + "="*70)
    print("分析結果")
    print("="*70)
    
    import json
    print(json.dumps(gaps, ensure_ascii=False, indent=2))
    
    # Save results
    output_path = os.path.join(PROJECT_ROOT, "case1_improvement_analysis.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "draft_content": draft_content,
            "final_content": final_content,
            "gap_analysis": gaps
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n結果を保存: {output_path}")
    
    return gaps


if __name__ == "__main__":
    main()
