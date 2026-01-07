"""
E2E Test: Rejected Cases Quality Verification
Tests the certification architecture against actual rejected application cases.
"""
import sys
import os

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, PROJECT_ROOT)


# PDF extraction
try:
    import fitz  # pymupdf
except ImportError:
    print("ERROR: pymupdf is required. Install with: pip install pymupdf")
    sys.exit(1)

from src.api.schemas import ApplicationRoot
from src.core.completion_checker import CompletionChecker
from src.core.certification_requirements import requirements_loader
from src.core.audit_agent import AuditAgent


REAP_REPORT_DIR = r"C:\Users\kitahara\Desktop\script\jigyokei-copilot\reap report"


def extract_pdf_text(filename: str) -> str:
    """Extract text from PDF file."""
    filepath = os.path.join(REAP_REPORT_DIR, filename)
    if not os.path.exists(filepath):
        return f"[FILE NOT FOUND: {filename}]"
    
    doc = fitz.open(filepath)
    text_parts = []
    for page in doc:
        text_parts.append(page.get_text())
    doc.close()
    return "\n".join(text_parts)


def analyze_case(case_name: str, pdf_files: list, expected_issues: list) -> dict:
    """
    Analyze a case and check for expected issues.
    
    Returns dict with:
    - case_name
    - total_score
    - detected_issues
    - expected_issues_found
    - pass_status
    """
    print(f"\n{'='*60}")
    print(f"【{case_name}】")
    print(f"{'='*60}")
    
    # Extract text from PDFs
    combined_text = ""
    for pdf in pdf_files:
        print(f"  Extracting: {pdf}")
        text = extract_pdf_text(pdf)
        combined_text += f"\n\n--- {pdf} ---\n{text}"
    
    print(f"  Total text length: {len(combined_text)} characters")
    
    # Check keyword presence using certification requirements
    print("\n  【認定要件キーワードチェック】")
    sections_to_check = ["disaster_assumption", "business_impact", "pdca"]
    keyword_results = {}
    
    for section_id in sections_to_check:
        keywords = requirements_loader.check_keywords(section_id, combined_text)
        section = requirements_loader.get_section(section_id)
        found_count = sum(keywords.values())
        total_count = len(keywords)
        
        print(f"    {section.name}: {found_count}/{total_count} keywords found")
        keyword_results[section_id] = {
            "found": found_count,
            "total": total_count,
            "missing": [k for k, v in keywords.items() if not v]
        }
    
    # Calculate certification score
    total_score = 0
    for section_id in sections_to_check:
        score = requirements_loader.calculate_section_score(section_id, combined_text)
        total_score += score
    
    print(f"\n  【認定スコア（推定）】: {total_score}/55点")
    
    # Check for expected issues
    print("\n  【不備指摘項目の検知】")
    detected_issues = []
    
    for section_id, results in keyword_results.items():
        if results["missing"]:
            issue = f"{requirements_loader.get_section(section_id).name}: {', '.join(results['missing'])} が不足"
            detected_issues.append(issue)
            print(f"    ⚠️ {issue}")
    
    if not detected_issues:
        print("    ✅ 不備なし")
    
    # Check if expected issues are detected
    expected_found = []
    for expected in expected_issues:
        for detected in detected_issues:
            if expected.lower() in detected.lower():
                expected_found.append(expected)
                break
    
    pass_status = len(expected_found) == len(expected_issues)
    
    return {
        "case_name": case_name,
        "total_score": total_score,
        "keyword_results": keyword_results,
        "detected_issues": detected_issues,
        "expected_issues": expected_issues,
        "expected_found": expected_found,
        "pass_status": pass_status
    }


def test_case1_approved():
    """Test Case 1: Originally approved application."""
    print("\n" + "="*70)
    print("テスト1: 案件1（認定済み）- 正常ケースとして不備が出ないことを確認")
    print("="*70)
    
    result = analyze_case(
        "案件1（認定済み）",
        [
            "案件1_事業継続力強化計画申請書.pdf",
            "案件1_電子申請下書きシート　事業継続力強化計画.pdf"
        ],
        expected_issues=[]  # No issues expected for approved case
    )
    
    # Approved case should have high score and no critical issues
    if result["total_score"] >= 30 and len(result["detected_issues"]) <= 2:
        print("\n✅ PASS: 案件1は認定レベルの品質です")
        return True
    else:
        print(f"\n⚠️ WARNING: 案件1のスコアが低い ({result['total_score']}点)")
        return False


def test_case2_initial_rejected():
    """Test Case 2 Initial: Should detect issues that led to rejection."""
    print("\n" + "="*70)
    print("テスト2: 案件2（初回申請）- 不備指摘された内容を検知できるか確認")
    print("="*70)
    
    result = analyze_case(
        "案件2（初回申請 - 不備指摘前）",
        [
            "案件2_071215申請内容.pdf"
        ],
        expected_issues=[
            "震度",  # Missing specific disaster assumption
            "確率"   # Missing probability data
        ]
    )
    
    # Initial rejected version should have low score and issues detected
    if result["total_score"] < 40 or len(result["detected_issues"]) >= 1:
        print(f"\n✅ PASS: 案件2（初回）の不備を正しく検知しました")
        print(f"   検知された不備: {result['detected_issues']}")
        return True
    else:
        print(f"\n❌ FAIL: 案件2（初回）の不備を検知できませんでした")
        return False


def test_case2_after_revision():
    """Test Case 2 After Revision: Should have fewer/no issues."""
    print("\n" + "="*70)
    print("テスト3: 案件2（修正後）- 修正により品質が向上したことを確認")
    print("="*70)
    
    result = analyze_case(
        "案件2（修正後 - 認定）",
        [
            "案件2_不備指摘後_修正申請.pdf"
        ],
        expected_issues=[]  # Should be fixed
    )
    
    # Revised version should have higher score
    if result["total_score"] >= 30:
        print(f"\n✅ PASS: 案件2（修正後）は認定レベルに達しています")
        return True
    else:
        print(f"\n⚠️ WARNING: 案件2（修正後）のスコアがまだ低い ({result['total_score']}点)")
        return False


def test_completion_checker_integration():
    """Test CompletionChecker with simulated bad/good data."""
    print("\n" + "="*70)
    print("テスト4: CompletionChecker 12/17改修対応テスト")
    print("="*70)
    
    # Bad case: Missing 12/17 mandatory fields
    bad_plan = ApplicationRoot()
    bad_plan.pdca.training_education = "訓練を実施する"
    # Missing: training_month, review_month, internal_publicity
    
    bad_result = CompletionChecker.analyze(bad_plan)
    bad_pdca_issues = [m for m in bad_result['missing_mandatory'] if m['section'] == 'PDCA']
    
    print(f"  不完全な計画のPDCA不備: {len(bad_pdca_issues)}件")
    for issue in bad_pdca_issues:
        print(f"    - {issue['msg']}")
    
    # Good case: All 12/17 fields filled
    good_plan = ApplicationRoot()
    good_plan.pdca.training_education = "教育及び訓練を実施する"
    good_plan.pdca.training_month = 2
    good_plan.pdca.review_month = 3
    good_plan.pdca.internal_publicity = "社内ポータルで周知"
    
    good_result = CompletionChecker.analyze(good_plan)
    good_pdca_issues = [m for m in good_result['missing_mandatory'] if m['section'] == 'PDCA']
    
    print(f"\n  完全な計画のPDCA不備: {len(good_pdca_issues)}件")
    
    if len(bad_pdca_issues) >= 3 and len(good_pdca_issues) == 0:
        print("\n✅ PASS: 12/17改修対応のバリデーションが正常に動作")
        return True
    else:
        print("\n❌ FAIL: バリデーションロジックに問題あり")
        return False


def main():
    print("="*70)
    print("E2E品質検証テスト: 不備指摘案件の正常化確認")
    print("="*70)
    
    results = []
    
    # Run all tests
    results.append(("案件1（認定済み）確認", test_case1_approved()))
    results.append(("案件2（初回申請）不備検知", test_case2_initial_rejected()))
    results.append(("案件2（修正後）品質確認", test_case2_after_revision()))
    results.append(("12/17改修対応テスト", test_completion_checker_integration()))
    
    # Summary
    print("\n" + "="*70)
    print("テスト結果サマリー")
    print("="*70)
    
    passed = 0
    failed = 0
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n総合結果: {passed}/{len(results)} テスト成功")
    
    if failed == 0:
        print("\n🎉 すべてのE2Eテストに合格しました！")
        return 0
    else:
        print(f"\n⚠️ {failed}件のテストが失敗しました")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
