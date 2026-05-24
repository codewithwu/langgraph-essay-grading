"""json_agent 模块 - 专门用于稳定输出 JSON 的 Agent。"""

import json
from typing import Annotated, Any

from pydantic import BaseModel

from langchain_agent.prompts.base import build_json_prompt


class JsonAgent:
    """能够稳定输出 JSON 的 Agent。

    统一处理 agent 的创建、调用和结果解析。

    Attributes:
        model: LLM 模型实例
        output_schema: 输出 JSON 的 Pydantic Schema

    Example:
        >>> from langchain_agent.agents import JsonAgent
        >>> from pydantic import BaseModel
        >>> from langchain_agent.utils.llm_factory import LLMFactory
        >>>
        >>> class ReviewSchema(BaseModel):
        ...     rating: int | None
        ...     sentiment: Literal["positive", "negative"] | None
        ...     is_valid: bool
        >>>
        >>> model = LLMFactory(provider="bailing").get_client()
        >>> agent = JsonAgent(model=model, output_schema=ReviewSchema)
        >>> result = agent.invoke_with_validation("这个产品很好用")
        >>> print(result)
    """

    def __init__(
        self,
        model: Annotated[
            Any,
            "支持 with_structured_output 的 LLM 模型实例",
        ],
        output_schema: type[BaseModel],
    ) -> None:
        """初始化 JsonAgent。

        Args:
            model: LLM 模型实例
            output_schema: 输出 JSON 的 Pydantic Schema，
                必须包含 is_valid: bool 字段用于标识是否提取到有效信息，
                其他字段建议为 Optional 类型
        """
        self._model = model
        self._output_schema = output_schema
        self._system_prompt = build_json_prompt(output_schema)
        self._agent = self._create_agent()

    def _create_agent(self) -> Any:
        """创建底层的 Agent。"""
        from langchain.agents import create_agent

        return create_agent(
            model=self._model,
            system_prompt=self._system_prompt,
        )

    @staticmethod
    def parse_json_response(data: dict[str, Any]) -> tuple[bool | None, dict | None]:
        """解析 Agent 响应数据，提取 is_valid 字段。

        Args:
            data: Agent 返回的数据，格式为 {'messages': [...]}

        Returns:
            元组 (is_valid, parsed_data)：
            - is_valid: is_valid 的布尔值，解析失败返回 None
            - parsed_data: 解析后的 JSON 字典，解析失败返回 None
        """
        messages = data.get("messages", [])
        if not messages:
            return None
        msg = messages[-1]
        content = getattr(msg, "content", None)
        if not isinstance(content, str):
            return None
        try:
            parsed = json.loads(content)
            if isinstance(parsed, dict) and "is_valid" in parsed:
                is_valid = parsed["is_valid"]
                if isinstance(is_valid, bool):
                    return is_valid, parsed
        except json.JSONDecodeError:
            pass
        return None, None

    @property
    def model(self) -> Any:
        """获取 LLM 模型实例。"""
        return self._model

    @property
    def output_schema(self) -> type[BaseModel]:
        """获取输出 Schema。"""
        return self._output_schema

    def invoke_with_validation(
        self, input: str | dict, max_retries: int = 3
    ) -> dict[str, Any]:
        """调用 Agent 并验证 is_valid，为假时重试。

        Args:
            input: 用户输入，支持简单字符串或 {"messages": [...]} 格式
            max_retries: 最大重试次数，默认 3

        Returns:
            解析后的 JSON 字典（当 is_valid 为 True 时）

        Raises:
            ValueError: 如果所有重试都失败
        """
        from langchain.messages import HumanMessage

        if isinstance(input, str):
            input = {"messages": [HumanMessage(input)]}

        for _ in range(max_retries):
            result = self._agent.invoke(input)
            is_valid, parsed = self.parse_json_response(result)
            if is_valid is True:
                return parsed
        raise ValueError(f"重试 {max_retries} 次后 is_valid 仍为假")


def create_json_agent(
    model: Annotated[
        Any,
        "支持 with_structured_output 的 LLM 模型实例",
    ],
    output_schema: type[BaseModel],
) -> JsonAgent:
    """创建能够稳定输出 JSON 的 Agent。

    Args:
        model: LLM 模型实例
        output_schema: 输出 JSON 的 Pydantic Schema，
            必须包含 is_valid: bool 字段用于标识是否提取到有效信息，
            其他字段建议为 Optional 类型

    Returns:
        JsonAgent 实例，可直接调用 .invoke() 或 .stream()
    """
    return JsonAgent(model=model, output_schema=output_schema)
