"""
Chunk Quality Analyzer for WS-2

Analyzes manual chunks for quality issues and tests RAG search accuracy.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any

# Target keywords for RAG search testing
TARGET_KEYWORDS = [
    "災害想定",
    "事業概要",
    "初動対応",
    "事前対策",
    "教育及び訓練",
    "計画の見直し",
    "J-SHIS",
    "ハザードマップ",
    "PDCA",
    "人員体制",
    "設備導入",
    "資金確保",
    "情報保護",
    "震度",
    "浸水",
    "避難"
]


def analyze_chunk(filepath: Path) -> Dict[str, Any]:
    """Analyze a single chunk file for quality issues."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    issues = []
    
    # Check file size
    if len(content) < 100:
        issues.append({"type": "too_short", "detail": f"Content too short ({len(content)} chars)"})
    
    if len(content) > 5000:
        issues.append({"type": "too_long", "detail": f"Content too long ({len(content)} chars)"})
    
    # Check for excessive whitespace
    whitespace_ratio = len(re.findall(r'\s', content)) / max(len(content), 1)
    if whitespace_ratio > 0.5:
        issues.append({"type": "excessive_whitespace", "detail": f"Whitespace ratio: {whitespace_ratio:.2%}"})
    
    # Check for fragmented lines (many short lines)
    lines = content.split('\n')
    short_lines = [l for l in lines if 0 < len(l.strip()) < 10]
    if len(short_lines) > len(lines) * 0.3:
        issues.append({"type": "fragmented", "detail": f"{len(short_lines)}/{len(lines)} short lines"})
    
    # Check for broken sentences (ending without punctuation)
    sentences = re.split(r'[。！？\n]', content)
    incomplete = [s for s in sentences if len(s.strip()) > 20 and not re.search(r'[。！？、]$', s.strip())]
    if len(incomplete) > 3:
        issues.append({"type": "incomplete_sentences", "detail": f"{len(incomplete)} incomplete sentences"})
    
    # Detect section keywords
    detected_sections = []
    section_map = {
        "災害": "disaster",
        "事業概要": "overview",
        "初動": "response",
        "対策": "measures",
        "PDCA": "pdca",
        "訓練": "training",
        "見直し": "review",
        "人員": "personnel",
        "設備": "equipment",
        "資金": "finance",
        "情報": "data"
    }
    for keyword, section in section_map.items():
        if keyword in content:
            detected_sections.append(section)
    
    return {
        "file": filepath.name,
        "size": len(content),
        "lines": len(lines),
        "issues": issues,
        "issue_count": len(issues),
        "detected_sections": list(set(detected_sections)),
        "quality_score": max(0, 100 - len(issues) * 20)
    }


def test_rag_search(chunks_dir: Path) -> Dict[str, Any]:
    """Test RAG search for target keywords."""
    # Load all chunk contents
    all_content = ""
    chunk_contents = {}
    
    for chunk_file in sorted(chunks_dir.glob("*.md")):
        with open(chunk_file, 'r', encoding='utf-8') as f:
            content = f.read()
            chunk_contents[chunk_file.name] = content
            all_content += content + "\n"
    
    # Test each keyword
    results = {}
    for keyword in TARGET_KEYWORDS:
        matches = []
        for filename, content in chunk_contents.items():
            if keyword in content:
                matches.append(filename)
        
        results[keyword] = {
            "found": len(matches) > 0,
            "match_count": len(matches),
            "files": matches[:3]  # First 3 matches
        }
    
    found_count = sum(1 for r in results.values() if r["found"])
    
    return {
        "total_keywords": len(TARGET_KEYWORDS),
        "found_keywords": found_count,
        "coverage": found_count / len(TARGET_KEYWORDS),
        "details": results
    }


def generate_report(chunks_dir: Path) -> Dict[str, Any]:
    """Generate complete quality report."""
    print(f"Analyzing chunks in: {chunks_dir}")
    
    # Analyze each chunk
    chunk_analyses = []
    for chunk_file in sorted(chunks_dir.glob("*.md")):
        analysis = analyze_chunk(chunk_file)
        chunk_analyses.append(analysis)
        print(f"  {analysis['file']}: {analysis['quality_score']}% quality, {analysis['issue_count']} issues")
    
    # Test RAG search
    print("\nTesting RAG keyword search...")
    rag_results = test_rag_search(chunks_dir)
    print(f"  Keyword coverage: {rag_results['coverage']:.1%}")
    
    # Summary
    total_issues = sum(a['issue_count'] for a in chunk_analyses)
    avg_quality = sum(a['quality_score'] for a in chunk_analyses) / max(len(chunk_analyses), 1)
    
    report = {
        "summary": {
            "total_chunks": len(chunk_analyses),
            "total_issues": total_issues,
            "average_quality": round(avg_quality, 1),
            "rag_keyword_coverage": round(rag_results['coverage'] * 100, 1),
            "overall_grade": "A" if avg_quality >= 90 and rag_results['coverage'] >= 0.9 else
                            "B" if avg_quality >= 70 and rag_results['coverage'] >= 0.7 else
                            "C" if avg_quality >= 50 else "D"
        },
        "chunk_analyses": chunk_analyses,
        "rag_search_results": rag_results,
        "missing_keywords": [k for k, v in rag_results['details'].items() if not v['found']],
        "problematic_chunks": [a['file'] for a in chunk_analyses if a['issue_count'] > 0]
    }
    
    return report


if __name__ == "__main__":
    chunks_dir = Path(__file__).parent.parent / "data" / "manual_chunks"
    
    if not chunks_dir.exists():
        print(f"Error: Chunks directory not found: {chunks_dir}")
        exit(1)
    
    report = generate_report(chunks_dir)
    
    print("\n" + "="*60)
    print("CHUNK QUALITY REPORT")
    print("="*60)
    print(f"Total Chunks: {report['summary']['total_chunks']}")
    print(f"Average Quality: {report['summary']['average_quality']}%")
    print(f"RAG Coverage: {report['summary']['rag_keyword_coverage']}%")
    print(f"Overall Grade: {report['summary']['overall_grade']}")
    print(f"\nMissing Keywords: {report['missing_keywords']}")
    print(f"Problematic Chunks: {len(report['problematic_chunks'])}")
    
    # Save report
    report_path = Path(__file__).parent / "chunk_quality_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\nReport saved to: {report_path}")
