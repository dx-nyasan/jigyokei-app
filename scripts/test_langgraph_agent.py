"""
Test script for LangGraph Jigyokei Agent (Phase 1 POC)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.langgraph_agent import run_section_review

# Sample interview text (simulating hearing from an SME)
SAMPLE_INTERVIEW = """
当社は和歌山県和歌山市に所在する従業員8名の金属加工業者です。
主に自動車部品の精密加工を行っており、トヨタ系のTier2サプライヤーとして
地域のサプライチェーンで重要な役割を担っています。

災害については、南海トラフ地震が心配です。
ハザードマップを見たところ、当社周辺は津波の浸水域には入っていませんが、
揺れによる被害は想定されます。

過去に大きな災害経験はありませんが、
2018年の台風21号では停電が2日間続き、生産が止まったことがあります。
"""

print("=" * 70)
print("LangGraph Jigyokei Agent - Phase 1 POC Test")
print("=" * 70)
print(f"対象セクション: 災害等の想定 (disaster_assumption)")
print("=" * 70)

result = run_section_review(
    section_id="disaster_assumption",
    applicant_name="テスト金属加工株式会社",
    location="和歌山県和歌山市",
    interview_text=SAMPLE_INTERVIEW,
    max_revisions=2
)

print(f"\n【実行結果】")
print(f"ステータス: {result['status']}")
print(f"添削ループ回数: {result['revision_count']}")

print("\n" + "=" * 70)
print("【生成された下書き】")
print("=" * 70)
print(result["draft_content"])

if result.get("critique_list"):
    print("\n" + "=" * 70)
    print("【未解消の指摘事項】")
    print("=" * 70)
    for i, c in enumerate(result["critique_list"], 1):
        print(f"{i}. {c['issue']}")
        if c.get('manual_reference'):
            print(f"   参考: {c['manual_reference'][:100]}...")
