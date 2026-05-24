"""图状态定义"""

from typing import TypedDict

from pydantic import BaseModel, Field


class ScoreDetail(BaseModel):
    """单维度评分详情"""

    score: float = Field(default=0.0, ge=0, le=1, description="分数 0~1")
    reason: str = Field(default="", description="评分理由")


class EssayState(TypedDict):
    """高考作文评分状态"""

    topic: str  # 作文题目
    essay: str  # 待评作文
    relevance: ScoreDetail  # 审题立意
    evidence: ScoreDetail  # 论据分析
    structure: ScoreDetail  # 结构评估
    expression: ScoreDetail  # 语言文采
    final_score: float  # 最终加权分数
