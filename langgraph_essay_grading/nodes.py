"""图节点定义"""

from langchain.messages import HumanMessage, SystemMessage

from langgraph_essay_grading.config import (
    WEIGHT_EVIDENCE,
    WEIGHT_EXPRESSION,
    WEIGHT_RELEVANCE,
    WEIGHT_STRUCTURE,
)
from langgraph_essay_grading.llm import structured_llm
from langgraph_essay_grading.prompts import SYSTEM_PROMPT, build_json_prompt
from langgraph_essay_grading.state import EssayState, ScoreDetail


def check_relevance(state: EssayState) -> dict:
    """审题立意：检查是否切题、立意是否深刻。"""
    messages = [
        SystemMessage(content=build_json_prompt(ScoreDetail) + SYSTEM_PROMPT),
        HumanMessage(
            content=f"请评估以下高考作文的审题立意。"
            f"考察是否切题、立意是否深刻。"
            f"给出 0 到 1 之间的分数，并说明理由。"
            f"\n\n题目：{state['topic']}\n\n作文：{state['essay']}"
        ),
    ]
    result = structured_llm.invoke(messages)
    return {"relevance": result}


def check_evidence(state: EssayState) -> dict:
    """论据分析：检查材料是否充实、论据是否有力。"""
    messages = [
        SystemMessage(content=build_json_prompt(ScoreDetail) + SYSTEM_PROMPT),
        HumanMessage(
            content=f"请评估以下高考作文的论据分析。"
            f"考察材料是否充实、论据是否有力。"
            f"给出 0 到 1 之间的分数，并说明理由。"
            f"\n\n题目：{state['topic']}\n\n作文：{state['essay']}"
        ),
    ]
    result = structured_llm.invoke(messages)
    return {"evidence": result}


def check_structure(state: EssayState) -> dict:
    """结构评估：检查行文逻辑、段落衔接。"""
    messages = [
        SystemMessage(content=build_json_prompt(ScoreDetail) + SYSTEM_PROMPT),
        HumanMessage(
            content=f"请评估以下高考作文的结构。"
            f"考察行文逻辑、段落衔接是否合理。"
            f"给出 0 到 1 之间的分数，并说明理由。"
            f"\n\n题目：{state['topic']}\n\n作文：{state['essay']}"
        ),
    ]
    result = structured_llm.invoke(messages)
    return {"structure": result}


def check_expression(state: EssayState) -> dict:
    """语言文采：检查用词、修辞、句式。"""
    messages = [
        SystemMessage(content=build_json_prompt(ScoreDetail) + SYSTEM_PROMPT),
        HumanMessage(
            content=f"请评估以下高考作文的语言文采。"
            f"考察用词是否贴切、修辞是否恰当、句式是否灵活。"
            f"给出 0 到 1 之间的分数，并说明理由。"
            f"\n\n题目：{state['topic']}\n\n作文：{state['essay']}"
        ),
    ]
    result = structured_llm.invoke(messages)
    return {"expression": result}


def calculate_final_score(state: EssayState) -> dict:
    """根据各维度分数计算加权最终分数。"""
    final = (
        state["relevance"].score * WEIGHT_RELEVANCE
        + state["evidence"].score * WEIGHT_EVIDENCE
        + state["structure"].score * WEIGHT_STRUCTURE
        + state["expression"].score * WEIGHT_EXPRESSION
    )
    return {"final_score": round(final, 2)}
