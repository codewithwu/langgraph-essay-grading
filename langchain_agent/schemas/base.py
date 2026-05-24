from pydantic import BaseModel, Field


class JsonAgentSchema(BaseModel):
    """JSON Agent 的基础 Schema，必须包含 is_valid 字段。"""

    is_valid: bool = Field(
        description="Whether valid information was extracted from input"
    )
