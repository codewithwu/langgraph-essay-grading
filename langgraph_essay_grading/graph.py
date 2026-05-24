"""工作流图定义"""

from langgraph.graph import END, START, StateGraph

from langgraph_essay_grading.nodes import (
    calculate_final_score,
    check_evidence,
    check_expression,
    check_relevance,
    check_structure,
)
from langgraph_essay_grading.routes import route_relevance
from langgraph_essay_grading.state import EssayState


def fan_out(state: EssayState) -> dict:
    """扇出节点：触发三个并行评分。"""
    return {}


# 构建状态图
workflow = StateGraph(EssayState)

# 注册节点
workflow.add_node("check_relevance", check_relevance)
workflow.add_node("fan_out", fan_out)
workflow.add_node("check_evidence", check_evidence)
workflow.add_node("check_structure", check_structure)
workflow.add_node("check_expression", check_expression)
workflow.add_node("calculate_final_score", calculate_final_score)

# 定义边
workflow.add_edge(START, "check_relevance")
workflow.add_conditional_edges(
    "check_relevance",
    route_relevance,
    {
        "fan_out": "fan_out",
        "calculate_final_score": "calculate_final_score",
    },
)
# 扇出：三个评分节点并行执行
workflow.add_edge("fan_out", "check_evidence")
workflow.add_edge("fan_out", "check_structure")
workflow.add_edge("fan_out", "check_expression")
# 汇聚：全部完成后计算总分
workflow.add_edge("check_evidence", "calculate_final_score")
workflow.add_edge("check_structure", "calculate_final_score")
workflow.add_edge("check_expression", "calculate_final_score")
workflow.add_edge("calculate_final_score", END)

# 编译图
graph = workflow.compile()
