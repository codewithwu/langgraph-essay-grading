"""中间件模块，提供模型选择等中间件功能。"""

from typing import Callable

from langchain.agents.middleware import (
    wrap_model_call,
    ModelRequest,
    ModelResponse,
    dynamic_prompt,
)
from langchain.agents.middleware import wrap_tool_call
from langchain.messages import ToolMessage

from langchain_agent.agents.base import get_singleton_client


@wrap_model_call
def dynamic_model_selection(
    request: ModelRequest, handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """根据对话复杂度动态选择模型。

    消息数量超过10条时使用高级模型(bailing)，否则使用轻量模型(longcat)。

    Args:
        request: 模型请求对象，包含对话状态等信息。
        handler: 后续处理函数。

    Returns:
        ModelResponse: 模型响应结果。
    """
    message_count = len(request.state["messages"])

    # 消息数量超过10条时使用高级模型
    if message_count > 10:
        model = get_singleton_client(llm_provider="bailing")
    else:
        model = get_singleton_client(llm_provider="longcat")

    return handler(request.override(model=model))


@wrap_model_call
def comprehensive_tool_filter(
    request: ModelRequest, handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """综合使用 state、store、context 的工具过滤中间件。

    说明：当所有可能的工具在代理创建时都已知时，可以预先注册它们，
    然后根据 state、权限或 context 动态过滤哪些工具暴露给模型。

    过滤策略：
    1. State-based: 未认证用户只能使用公开工具
    2. Store-based: 根据 feature flags 限制工具访问
    3. Context-based: 根据用户角色限制工具权限

    Args:
        request: 模型请求对象，包含 state、runtime 等信息。
        handler: 后续处理函数。

    Returns:
        ModelResponse: 模型响应结果。
    """
    # 1. State-based: 检查认证状态
    is_authenticated = request.state.get("authenticated", False)
    message_count = len(request.state["messages"])

    # 2. Store-based: 获取 feature flags
    store = request.runtime.store if request.runtime else None
    enabled_tools = None
    if store:
        user_id = (
            request.runtime.context.user_id
            if request.runtime and request.runtime.context
            else "anonymous"
        )
        feature_flags = store.get(("features",), user_id)
        if feature_flags:
            enabled_tools = feature_flags.value.get("enabled_tools", [])

    # 3. Context-based: 获取用户角色
    if request.runtime and request.runtime.context:
        user_role = request.runtime.context.user_role
    else:
        user_role = "viewer"

    # 应用过滤规则
    tools = list(request.tools)

    # State-based 过滤: 未认证用户只能使用 public_ 前缀的工具
    if not is_authenticated:
        tools = [t for t in tools if t.name.startswith("public_")]
    elif message_count < 5:
        # 对话早期限制高级工具
        tools = [t for t in tools if t.name != "advanced_search"]

    # Context-based 过滤: 根据角色限制
    if user_role == "editor":
        tools = [t for t in tools if t.name != "delete_data"]
    elif user_role == "viewer":
        tools = [t for t in tools if t.name.startswith("read_")]

    # Store-based 过滤: 只保留启用的工具
    if enabled_tools is not None:
        tools = [t for t in tools if t.name in enabled_tools]

    # 如果过滤后没有可用工具，至少保留一个基础工具
    if not tools and request.tools:
        tools = [request.tools[0]]

    return handler(request.override(tools=tools))


@wrap_tool_call
def handle_tool_errors(request, handler):
    """Handle tool execution errors with custom messages."""
    try:
        return handler(request)
    except Exception as e:
        # Return a custom error message to the model
        return ToolMessage(
            content=f"Tool error: Please check your input and try again. ({str(e)})",
            tool_call_id=request.tool_call["id"],
        )


@dynamic_prompt
def user_role_prompt(request: ModelRequest) -> str:
    """Generate system prompt based on user role."""
    user_role = request.runtime.context.get("user_role", "user")
    base_prompt = "You are a helpful assistant."

    if user_role == "expert":
        return f"{base_prompt} Provide detailed technical responses."
    elif user_role == "beginner":
        return f"{base_prompt} Explain concepts simply and avoid jargon."

    return base_prompt
