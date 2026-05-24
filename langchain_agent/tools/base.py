from pydantic import BaseModel


def build_json_prompt(schema: type[BaseModel]) -> str:
    """构建 JSON 输出的系统提示词。

    Args:
        schema: Pydantic 模型类，定义输出的 JSON 结构

    Returns:
        系统提示词字符串

    注意:
    Schema 必须包含 is_valid: bool 字段用于标识是否提取到有效信息，
    其他字段建议为 Optional 类型。

    示例:
        from pydantic import BaseModel, Field
        from typing import Optional, Literal

        class ProductReview(BaseModel):
            ""Analysis of a product review.""
            rating: Optional[int]  = Field(description="The rating of the product", ge=1, le=5)
            sentiment: Optional[Literal["positive", "negative"]] = Field(description="The sentiment of the review")
            key_points: Optional[list[str]] = Field(description="The key points of the review. Lowercase, 1-3 words each.")
            is_valid: bool = Field(description="是否提取到了有效的信息")

        prompt = build_json_prompt(ProductReview)
    """
    schema_name = schema.__name__
    schema_json = schema.model_json_schema()

    return f"""你是一个 JSON 输出助手。
                【输出规则】
                1. 只输出纯 JSON 对象，不要包含任何解释、markdown 代码块或其他内容
                2. 根据输入内容判断：从用户的输入中提取有效的 {schema_name} 信息
                3. 确保 JSON 字段与 Schema 定义完全一致

                【Schema 定义】
                ## {schema_name}
                {schema_json}
                """
