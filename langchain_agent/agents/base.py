from functools import lru_cache
from typing import Annotated, Any

from langchain_agent.utils.llm_factory import LLMFactory


@lru_cache()
def get_singleton_client(
    llm_provider: Annotated[
        str, "LLM 提供者: 'ollama'、'openai' 或 'bailing'"
    ] = "bailing",
) -> Any:
    """获取 LLM 实例（单例）.

    Args:
        llm_provider: LLM 提供者

    Returns:
        LLM 实例
    """
    return LLMFactory(provider=llm_provider).get_client()
