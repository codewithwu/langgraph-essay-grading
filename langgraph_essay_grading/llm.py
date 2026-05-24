"""LLM 实例"""

from langchain_agent.agents.base import get_singleton_client

from langgraph_essay_grading.config import LLM_PROVIDER
from langgraph_essay_grading.state import ScoreDetail

llm = get_singleton_client(llm_provider=LLM_PROVIDER)
structured_llm = llm.with_structured_output(ScoreDetail)
