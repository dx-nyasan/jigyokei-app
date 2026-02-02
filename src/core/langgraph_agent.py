"""
LangGraph-based Jigyokei Agent
Phase 1 POC: Writer-Reviewer Loop for Disaster Assumption Section

This module implements a controllable agent graph that:
1. Writes a draft for a specific section (Writer node)
2. Reviews the draft against certification requirements (Reviewer node)
3. Loops back for revision if criteria are not met
4. Stops for human approval when ready
"""
import os
from typing import TypedDict, List, Optional, Literal, Annotated
from pydantic import BaseModel, Field

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# Gemini imports (using new gennai SDK via ModelCommander)
from src.core.model_commander import get_commander

# Local imports for RAG integration
from src.core.manual_rag import get_rag
from src.core.certification_requirements import requirements_loader


# =============================================================================
# State Definition
# =============================================================================

class CritiqueItem(BaseModel):
    """Single critique item from the Reviewer."""
    section_id: str = Field(description="対象セクションID")
    issue: str = Field(description="指摘内容")
    manual_reference: str = Field(description="マニュアルからの引用例")
    is_resolved: bool = False


class JigyokeiGraphState(TypedDict):
    """
    Shared state for the Jigyokei LangGraph agent.
    All nodes read from and write to this state.
    """
    # Input data
    applicant_name: str
    location: str  # For J-SHIS integration
    raw_interview_text: str  # ヒアリングログ
    
    # Processing state
    current_section: str  # "disaster_assumption", "measures", etc.
    revision_count: int
    max_revisions: int
    
    # Review process
    critique_list: List[dict]  # List of CritiqueItem as dicts
    
    # Generated content
    draft_content: str
    
    # Human interaction
    user_intent: Optional[str]
    human_approved: bool
    
    # Final output
    status: str  # "writing", "reviewing", "approved", "needs_human"


# =============================================================================
# Helper: Gemini Model Wrapper (Integrated with ModelCommander)
# =============================================================================

def get_gemini_response(task_type: str, prompt: str):
    """Get response via ModelCommander with fallback."""
    commander = get_commander()
    return commander.generate_content(task_type, prompt)


# =============================================================================
# Node: Writer
# =============================================================================

# Complete mapping for all 12 certification sections
SECTION_NAME_MAP = {
    "disaster_assumption": "災害等の想定",
    "business_impact": "事業活動への影響",
    "initial_response": "初動対応",
    "measures": "事前対策",
    "pdca": "PDCA体制",
    "business_overview": "事業活動の概要",
    "applicant_info": "申請者情報",
    "implementation_timeline": "実施時期",
    "resource_allocation": "人的・物的リソース",
    "communication_plan": "情報伝達計画",
    "training_plan": "訓練・教育計画",
    "review_process": "見直し・改善",
}

# Section dependencies (section_id: list of required prior sections)
SECTION_DEPENDENCIES = {
    "disaster_assumption": [],
    "business_impact": ["disaster_assumption"],
    "initial_response": ["disaster_assumption"],
    "measures": ["disaster_assumption", "business_impact"],
    "pdca": ["measures"],
    "business_overview": [],
    "applicant_info": [],
    "implementation_timeline": ["measures"],
    "resource_allocation": ["measures"],
    "communication_plan": ["initial_response"],
    "training_plan": ["measures", "communication_plan"],
    "review_process": ["pdca"],
}


def get_section_dependencies(section_id: str) -> List[str]:
    """
    Get list of sections that must be completed before this section.
    
    Args:
        section_id: The section to check
        
    Returns:
        List of dependent section IDs
    """
    return SECTION_DEPENDENCIES.get(section_id, [])


def check_dependencies_satisfied(section_id: str, status: dict) -> bool:
    """
    Check if all dependencies for a section are satisfied.
    
    Args:
        section_id: The section to check
        status: Dictionary mapping section_id to status ("pending", "completed", etc.)
        
    Returns:
        True if all dependencies are completed
    """
    deps = get_section_dependencies(section_id)
    return all(status.get(dep) == "completed" for dep in deps)


def planner_node(state: JigyokeiGraphState) -> dict:
    """
    Planner node that determines which section to process next.
    
    Respects section dependencies and prioritizes sections in order.
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with next current_section
    """
    sections_status = state.get("sections_status", {})
    
    # Priority order for processing
    priority_order = [
        "applicant_info",
        "business_overview", 
        "disaster_assumption",
        "business_impact",
        "initial_response",
        "measures",
        "implementation_timeline",
        "resource_allocation",
        "communication_plan",
        "training_plan",
        "pdca",
        "review_process",
    ]
    
    # Find next section to process
    for section_id in priority_order:
        status = sections_status.get(section_id, "pending")
        
        if status == "pending":
            # Check if dependencies are satisfied
            if check_dependencies_satisfied(section_id, sections_status):
                return {"current_section": section_id}
    
    # All sections completed or blocked
    return {"current_section": None, "status": "all_completed"}


WRITER_PROMPT = """あなたは事業継続力強化計画（ジギョケイ）の「{section_name}」セクションを執筆するAIです。

【事業者情報】
- 事業者名: {applicant_name}
- 所在地: {location}

【ヒアリング内容】
{interview_text}

【タスク】
上記のヒアリング内容を元に、「{section_name}」の下書きを作成してください。

{revision_instruction}

【記載要件】
{requirements}

回答は下書き本文のみを出力してください。
"""


def writer_node(state: JigyokeiGraphState) -> dict:
    """
    Writes or revises draft content for the current section.
    If there are critiques, incorporate feedback into revision.
    """
    
    # Get section requirements
    section_id = state["current_section"]
    section_req = requirements_loader.get_section(section_id)
    
    section_name_map = {
        "disaster_assumption": "災害等の想定",
        "business_impact": "事業活動への影響",
        "initial_response": "初動対応",
        "measures": "事前対策",
        "pdca": "PDCA体制",
        "business_overview": "事業活動の概要",
    }
    section_name = section_name_map.get(section_id, section_id)
    
    # Build revision instruction if there are critiques
    revision_instruction = ""
    if state.get("critique_list"):
        critiques = state["critique_list"]
        revision_instruction = "【前回の指摘事項を反映してください】\n"
        for i, c in enumerate(critiques, 1):
            revision_instruction += f"{i}. {c['issue']}\n"
            if c.get("manual_reference"):
                revision_instruction += f"   参考: {c['manual_reference']}\n"
    
    # Build requirements string
    requirements_text = ""
    if section_req:
        requirements_text = f"必須キーワード: {', '.join(section_req.required_keywords)}"
        if section_req.validation_notes:
            requirements_text += f"\n注意: {section_req.validation_notes}"
    
    prompt = WRITER_PROMPT.format(
        section_name=section_name,
        applicant_name=state["applicant_name"],
        location=state["location"],
        interview_text=state["raw_interview_text"],
        revision_instruction=revision_instruction,
        requirements=section_req.text if section_req else "特に指定なし"
    )
    
    response = get_gemini_response("draft", prompt)
    return {"draft_content": response.text, "revision_count": state["revision_count"] + 1, "status": "reviewing"}


# =============================================================================
# Node: Reviewer (RAG-enhanced)
# =============================================================================

REVIEWER_PROMPT = """あなたは中小企業庁の認定審査官として、「{section_name}」セクションの下書きを厳格に審査してください。

【審査対象】
{draft_content}

【審査基準】
{requirements}

【マニュアルの記載例】
{manual_examples}

【タスク】
以下のフォーマットで審査結果を出力してください。

## 判定
PASS または FAIL

## 指摘事項（FAILの場合のみ）
1. [具体的な指摘内容]
   参考: [マニュアルの記載例を引用]

2. [具体的な指摘内容]
   参考: [マニュアルの記載例を引用]
"""


def reviewer_node(state: JigyokeiGraphState) -> dict:
    """
    Reviews the generated draft content against requirements and manual examples.
    """
    rag = get_rag()
    
    section_id = state["current_section"]
    section_req = requirements_loader.get_section(section_id)
    
    section_name_map = {
        "disaster_assumption": "災害等の想定",
        "business_impact": "事業活動への影響",
        "initial_response": "初動対応",
        "measures": "事前対策",
        "pdca": "PDCA体制",
        "business_overview": "事業活動の概要",
    }
    section_name = section_name_map.get(section_id, section_id)
    
    # Get examples from RAG
    manual_examples = ""
    try:
        examples = rag.get_examples_for_section(section_id)
        if examples:
            manual_examples = "\n---\n".join(examples[:3])
        else:
            # Fallback: search for relevant content
            results = rag.search(section_name, top_k=3)
            manual_examples = "\n---\n".join([r.text for r in results])
    except Exception:
        manual_examples = "(マニュアル例の取得に失敗しました)"
    
    # Build requirements string
    requirements_text = ""
    if section_req:
        requirements_text = f"必須キーワード: {', '.join(section_req.required_keywords)}"
        if section_req.validation_notes:
            requirements_text += f"\n注意: {section_req.validation_notes}"
    
    prompt = REVIEWER_PROMPT.format(
        section_name=section_name,
        draft_content=state["draft_content"],
        requirements=requirements_text,
        manual_examples=manual_examples or "(なし)"
    )
    
    response = get_gemini_response("reasoning", prompt)
    review_text = response.text
    
    # Parse response
    if "PASS" in review_text.upper().split("\n")[0:5]:
        return {
            "critique_list": [],
            "status": "approved"
        }
    else:
        # Extract critiques (simple parsing)
        critiques = []
        lines = review_text.split("\n")
        current_critique = None
        
        for line in lines:
            line = line.strip()
            if line.startswith(("1.", "2.", "3.", "4.", "5.")):
                if current_critique:
                    critiques.append(current_critique)
                current_critique = {
                    "section_id": section_id,
                    "issue": line[2:].strip(),
                    "manual_reference": "",
                    "is_resolved": False
                }
            elif line.startswith("参考:") and current_critique:
                current_critique["manual_reference"] = line[3:].strip()
        
        if current_critique:
            critiques.append(current_critique)
        
        # If no critiques parsed but FAIL, create generic one
        if not critiques:
            critiques = [{
                "section_id": section_id,
                "issue": "審査基準を満たしていません。より具体的な記載が必要です。",
                "manual_reference": manual_examples[:200] if manual_examples else "",
                "is_resolved": False
            }]
        
        return {
            "critique_list": critiques,
            "status": "writing"  # Send back to writer
        }


# =============================================================================
# Conditional Edge: Should Continue Loop?
# =============================================================================

def should_continue(state: JigyokeiGraphState) -> Literal["writer", "human", "end"]:
    """
    Determines the next step based on current state.
    """
    if state["status"] == "approved":
        return "human"  # Go to human approval
    
    if state["revision_count"] >= state["max_revisions"]:
        # Safety valve: too many revisions, ask human
        return "human"
    
    if state["status"] == "writing":
        return "writer"  # Loop back for revision
    
    return "end"


# =============================================================================
# Node: Human Approval (Interrupt point)
# =============================================================================

def human_approval_node(state: JigyokeiGraphState) -> dict:
    """
    Placeholder node for human approval.
    In practice, this is where the graph pauses for human input.
    """
    return {
        "status": "needs_human",
        "human_approved": False
    }


# =============================================================================
# Graph Builder
# =============================================================================

def build_jigyokei_graph():
    """
    Builds and returns the LangGraph StateGraph for Jigyokei.
    """
    # Create the graph
    graph = StateGraph(JigyokeiGraphState)
    
    # Add nodes
    graph.add_node("writer", writer_node)
    graph.add_node("reviewer", reviewer_node)
    graph.add_node("human_approval", human_approval_node)
    
    # Set entry point
    graph.set_entry_point("writer")
    
    # Add edges
    graph.add_edge("writer", "reviewer")
    
    # Conditional edge from reviewer
    graph.add_conditional_edges(
        "reviewer",
        should_continue,
        {
            "writer": "writer",
            "human": "human_approval",
            "end": END
        }
    )
    
    graph.add_edge("human_approval", END)
    
    # Compile with memory for checkpointing
    memory = MemorySaver()
    return graph.compile(checkpointer=memory)


# =============================================================================
# Convenience Function: Run Single Section
# =============================================================================

def run_section_review(
    section_id: str,
    applicant_name: str,
    location: str,
    interview_text: str,
    max_revisions: int = 3
) -> dict:
    """
    Run the Writer-Reviewer loop for a single section.
    
    Args:
        section_id: Section to process (e.g., "disaster_assumption")
        applicant_name: Name of the applicant company
        location: Location for J-SHIS integration
        interview_text: Raw interview/hearing text
        max_revisions: Maximum number of revision loops
        
    Returns:
        Final state dictionary with draft_content and status
    """
    graph = build_jigyokei_graph()
    
    initial_state: JigyokeiGraphState = {
        "applicant_name": applicant_name,
        "location": location,
        "raw_interview_text": interview_text,
        "current_section": section_id,
        "revision_count": 0,
        "max_revisions": max_revisions,
        "critique_list": [],
        "draft_content": "",
        "user_intent": None,
        "human_approved": False,
        "status": "writing"
    }
    
    # Run the graph
    config = {"configurable": {"thread_id": f"{applicant_name}_{section_id}"}}
    final_state = graph.invoke(initial_state, config)
    
    return final_state


# =============================================================================
# Test Entry Point
# =============================================================================

if __name__ == "__main__":
    # Simple test
    result = run_section_review(
        section_id="disaster_assumption",
        applicant_name="テスト株式会社",
        location="和歌山県和歌山市",
        interview_text="""
        当社は従業員10名の製造業者です。
        主に自動車部品の金属加工を行っています。
        過去に大きな災害の経験はありませんが、
        南海トラフ地震のリスクを心配しています。
        """,
        max_revisions=2
    )
    
    print("=" * 60)
    print(f"Status: {result['status']}")
    print(f"Revisions: {result['revision_count']}")
    print("=" * 60)
    print("Draft Content:")
    print(result["draft_content"])
    if result.get("critique_list"):
        print("=" * 60)
        print("Remaining Critiques:")
        for c in result["critique_list"]:
            print(f"  - {c['issue']}")
