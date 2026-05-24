"""条件路由"""

from langgraph_essay_grading.config import RELEVANCE_THRESHOLD
from langgraph_essay_grading.state import EssayState


def route_relevance(state: EssayState) -> str:
    """审题立意评分后路由：分数过低则跳过后续评估。"""
    if state["relevance"].score > RELEVANCE_THRESHOLD:
        return "fan_out"
    return "calculate_final_score"
