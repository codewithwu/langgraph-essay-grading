"""请求体模型"""

from pydantic import BaseModel, Field


class GradeRequest(BaseModel):
    """作文评分请求"""

    topic: str = Field(..., description="作文题目", min_length=1)
    sample_essay: str = Field(..., description="待评作文内容", min_length=1)
