"""agents 模块 - Agent 相关功能。"""

from langchain_agent.agents.base import get_singleton_client
from langchain_agent.agents.json_agent import JsonAgent, create_json_agent

__all__ = ["get_singleton_client", "create_json_agent", "JsonAgent"]
