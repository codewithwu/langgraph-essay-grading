"""响应体模型"""

from pydantic import BaseModel


class ScoreDetailResponse(BaseModel):
    """单维度评分详情"""

    score: float
    reason: str


class GradeResponse(BaseModel):
    """完整评分结果"""

    topic: str
    essay: str
    relevance: ScoreDetailResponse
    evidence: ScoreDetailResponse
    structure: ScoreDetailResponse
    expression: ScoreDetailResponse
    final_score: float
