"""LangChain 官方中间件模块。

提供 LangChain 官方文档中介绍的中间件封装。
https://python.langchain.com/docs/how_to/middleware/
"""

from langchain.agents.middleware import (
    FilesystemFileSearchMiddleware,
    HumanInTheLoopMiddleware,
    LLMToolEmulator,
    LLMToolSelectorMiddleware,
    ModelCallLimitMiddleware,
    ModelFallbackMiddleware,
    ModelRetryMiddleware,
    PIIMiddleware,
    SummarizationMiddleware,
    TodoListMiddleware,
    ToolCallLimitMiddleware,
    ToolRetryMiddleware,
)
from langchain.agents.middleware.context_editing import (
    ClearToolUsesEdit,
    ContextEditingMiddleware,
)
from langchain.agents.middleware.shell_tool import (
    CodexSandboxExecutionPolicy,
    DockerExecutionPolicy,
    HostExecutionPolicy,
    RedactionRule,
    ShellToolMiddleware,
)

__all__ = [
    "SummarizationMiddleware",
    "HumanInTheLoopMiddleware",
    "ModelCallLimitMiddleware",
    "ToolCallLimitMiddleware",
    "ModelFallbackMiddleware",
    "PIIMiddleware",
    "TodoListMiddleware",
    "LLMToolSelectorMiddleware",
    "ToolRetryMiddleware",
    "ModelRetryMiddleware",
    "LLMToolEmulator",
    "ContextEditingMiddleware",
    "ClearToolUsesEdit",
    "ShellToolMiddleware",
    "HostExecutionPolicy",
    "DockerExecutionPolicy",
    "CodexSandboxExecutionPolicy",
    "RedactionRule",
    "FilesystemFileSearchMiddleware",
]


# ============================================================================
# SummarizationMiddleware 使用指南
# ============================================================================
"""
SummarizationMiddleware 用于在对话token数量接近限制时，自动对历史消息进行摘要，
从而在保持上下文连贯性的同时避免超出模型的输入token限制。

使用示例：
----------

1. 基本用法（按 token 数触发）：

    from langchain.agents import create_agent
    from langchain.agents.middleware import SummarizationMiddleware

    agent = create_agent(
        model="gpt-4.1",
        tools=[your_weather_tool],
        middleware=[
            SummarizationMiddleware(
                model="gpt-4.1-mini",      # 用于生成摘要的模型
                trigger=("tokens", 4000),   # 当 token 数达到 4000 时触发摘要
                keep=("messages", 20),      # 摘要后保留最近 20 条消息
            ),
        ],
    )

2. 按消息数触发：

    SummarizationMiddleware(
        model="gpt-4.1-mini",
        trigger=("messages", 50),       # 消息数达到 50 条时触发
        keep=("messages", 10),           # 保留最近 10 条
    )

3. 按模型输入比例触发（需模型支持 profile）：

    SummarizationMiddleware(
        model="gpt-4.1-mini",
        trigger=("fraction", 0.8),      # 模型输入达到 80% 时触发
        keep=("fraction", 0.3),         # 保留 30% 的上下文
    )

4. 组合触发条件（满足任一即触发）：

    SummarizationMiddleware(
        model="gpt-4.1-mini",
        trigger=[("fraction", 0.8), ("messages", 100)],
        keep=("messages", 20),
    )

参数说明：
----------

model: str | BaseChatModel
    用于生成摘要的模型。可以是模型名称字符串（如 "gpt-4.1-mini"）
    或已初始化的 ChatModel 实例。

trigger: ContextSize | list[ContextSize] | None
    触发摘要的条件，可以是：
    - ("tokens", 数量): token 数达到指定值时触发
    - ("messages", 数量): 消息数达到指定值时触发
    - ("fraction", 比例): 达到模型最大输入的指定比例时触发（需模型有 profile）
    - [条件1, 条件2, ...]: 多个条件，满足任一即触发

    默认: None（不自动触发，需要外部调用）

keep: ContextSize
    摘要后保留的上下文量，支持与 trigger 相同的格式。
    默认: ("messages", 20)

token_counter: TokenCounter
    用于计算 token 数的函数。默认使用内置的近似计数函数，
    会根据模型类型（如 Anthropic）自动调整。

summary_prompt: str
    生成摘要时使用的提示词模板。默认模板会提取：
    - 会话意图 (SESSION INTENT)
    - 摘要 (SUMMARY)
    - 产物/资源 (ARTIFACTS)
    - 下一步 (NEXT STEPS)

trim_tokens_to_summarize: int | None
    准备摘要时保留的最大 token 数，用于控制输入给摘要模型的数据量。
    默认: 4000。设为 None 则跳过修剪。

上下文大小类型 ContextSize：
--------------------------
    ContextSize 是一个联合类型，表示上下文大小的规格：

    1. ("tokens", 数量) - 绝对 token 数
       例: ("tokens", 3000) 表示 3000 个 token

    2. ("messages", 数量) - 绝对消息数
       例: ("messages", 50) 表示 50 条消息

    3. ("fraction", 比例) - 模型最大输入的比例（0 < 比例 <= 1）
       例: ("fraction", 0.5) 表示模型最大输入的 50%

注意事项：
----------
1. 摘要会保持 AI/Tool 消息对在一起，不会拆分它们
2. 摘要后的消息会被替换为一条 HumanMessage，包含摘要内容
3. 使用 ("fraction", ...) 需要模型配置 profile {"max_input_tokens": ...}
4. 摘要操作是同步的，在 before_model hook 中执行
"""


# ============================================================================
# HumanInTheLoopMiddleware 使用指南
# ============================================================================
"""
HumanInTheLoopMiddleware 用于在 Agent 执行特定工具前暂停，等待人工审核批准。
这在需要人工确认敏感操作（如发送邮件、删除数据、转账等）的场景中非常有用。

使用示例：
----------

1. 基本用法（所有决策类型）：

    from langchain.agents import create_agent
    from langchain.agents.middleware import HumanInTheLoopMiddleware
    from langgraph.checkpoint.memory import InMemorySaver

    def send_email_tool(recipient: str, subject: str, body: str) -> str:
        '''发送邮件'''
        return f"Email sent to {recipient}"

    agent = create_agent(
        model="gpt-4.1",
        tools=[send_email_tool],
        checkpointer=InMemorySaver(),      # 必须配置 checkpointer 以保存状态
        middleware=[
            HumanInTheLoopMiddleware(
                interrupt_on={
                    "send_email_tool": True,  # 所有决策类型（approve, edit, reject, respond）
                }
            ),
        ],
    )

2. 指定允许的决策类型：

    HumanInTheLoopMiddleware(
        interrupt_on={
            "send_email_tool": {
                "allowed_decisions": ["approve", "edit", "reject"],
            },
            "read_email_tool": False,  # 自动批准，无需人工介入
        }
    )

3. 自定义描述信息：

    import json

    def format_tool_description(tool_call, state, runtime):
        return (
            f"工具: {tool_call['name']}\n"
            f"参数:\n{json.dumps(tool_call['args'], indent=2, ensure_ascii=False)}"
        )

    HumanInTheLoopMiddleware(
        interrupt_on={
            "send_email_tool": {
                "allowed_decisions": ["approve", "edit", "reject"],
                "description": "请审核以下邮件发送请求",  # 静态描述
                # description: format_tool_description,  # 动态描述
            },
        },
        description_prefix="工具执行需要批准",  # 默认前缀
    )

参数说明：
----------

interrupt_on: dict[str, bool | InterruptOnConfig]
    工具名称到审核配置的映射。

    - True: 所有决策类型（approve, edit, reject, respond）
    - False: 自动批准，无需人工介入
    - InterruptOnConfig: 自定义审核配置

    InterruptOnConfig 支持以下字段：

    allowed_decisions: list[DecisionType]
        允许的决策类型列表，可选值：
        - "approve": 批准执行
        - "edit": 编辑参数后执行
        - "reject": 拒绝执行
        - "respond": 直接回复（跳过工具执行）

    description: str | Callable | None
        显示给用户的描述信息。
        可以是静态字符串，或动态生成描述的函数。

        动态描述函数签名：
        def description_factory(
            tool_call: ToolCall,
            state: AgentState,
            runtime: Runtime
        ) -> str

    args_schema: dict[str, Any] | None
        编辑参数时使用的 JSON schema，用于验证和指导用户编辑。

description_prefix: str
    当工具没有自定义 description 时使用的默认前缀。
    默认: "Tool execution requires approval"

决策类型说明：
-------------

1. ApproveDecision: 批准执行
    {"type": "approve"}

2. EditDecision: 编辑后执行
    {
        "type": "edit",
        "edited_action": {
            "name": "tool_name",
            "args": {"param": "new_value"}
        }
    }

3. RejectDecision: 拒绝执行
    {"type": "reject", "message": "拒绝原因（可选）"}

4. RespondDecision: 直接回复（跳过工具执行）
    {"type": "respond", "message": "人工回复内容"}

注意事项：
----------
1. 必须配置 checkpointer（推荐使用 InMemorySaver 或持久化存储）
   否则 Agent 无法在中断后恢复状态
2. 工具审核在 after_model hook 中执行
3. 审核结果是同步等待的，通过 langgraph.types.interrupt 实现
4. 可以同时审核多个工具调用，按配置顺序处理
5. 审核配置中工具名称必须与实际工具名称完全匹配
"""


# ============================================================================
# ModelCallLimitMiddleware 使用指南
# ============================================================================
"""
ModelCallLimitMiddleware 用于跟踪和限制 Agent 的模型调用次数，
防止过度消耗 token 或陷入无限循环。

支持两种粒度的限制：
- Thread 级别：跨多次运行（invocation）累积计数
- Run 级别：单次运行内的计数

使用示例：
----------

1. 基本用法：

    from langchain.agents import create_agent
    from langchain.agents.middleware import ModelCallLimitMiddleware
    from langgraph.checkpoint.memory import InMemorySaver

    agent = create_agent(
        model="gpt-4.1",
        checkpointer=InMemorySaver(),    # 必须配置 checkpointer 以保存状态
        tools=[],
        middleware=[
            ModelCallLimitMiddleware(
                thread_limit=10,    # 每个线程最多 10 次模型调用
                run_limit=5,       # 每次运行最多 5 次模型调用
                exit_behavior="end",  # 超出限制时跳转到末尾
            ),
        ],
    )

2. 仅限制 thread 级别：

    ModelCallLimitMiddleware(
        thread_limit=100,  # 线程级别限制
        # run_limit 未设置
    )

3. 仅限制 run 级别：

    ModelCallLimitMiddleware(
        run_limit=10,  # 单次运行限制
    )

4. 超出限制时抛出异常：

    ModelCallLimitMiddleware(
        thread_limit=5,
        exit_behavior="error",  # 超出限制时抛出 ModelCallLimitExceededError
    )

参数说明：
----------

thread_limit: int | None
    每个线程允许的最大模型调用次数。
    - None 表示不限制
    - 跨多次 agent.invoke() 调用累积计数

run_limit: int | None
    单次运行允许的最大模型调用次数。
    - None 表示不限制
    - 每次 agent.invoke() 调用独立计数

exit_behavior: Literal["end", "error"]
    超出限制时的行为：
    - "end": 跳转到 agent 末尾，注入一条 AI 消息说明限制已超出
    - "error": 抛出 ModelCallLimitExceededError 异常

异常说明：
----------

ModelCallLimitExceededError
    当 exit_behavior="error" 时，超出限制会抛出此异常。

    属性：
    - thread_count: 当前线程的模型调用次数
    - run_count: 当前运行的模型调用次数
    - thread_limit: 线程限制（可能为 None）
    - run_limit: 运行限制（可能为 None）

状态说明：
----------

该中间件会向 AgentState 添加两个私有字段：
- thread_model_call_count: 线程级别的累积调用计数
- run_model_call_count: 单次运行的调用计数

这些字段通过 checkpointer 持久化，因此 thread_limit 会跨会话累积。

注意事项：
----------
1. 必须配置 checkpointer 来持久化状态
2. thread_limit 是跨线程累积的，使用不同 thread_id 会重置计数
3. 在 before_model hook 中检查限制，在 after_model hook 中更新计数
4. 限制检查在模型调用之前，因此实际调用次数可能等于（但不超过）限制
5. 至少需要设置 thread_limit 或 run_limit 之一
"""


# ============================================================================
# ToolCallLimitMiddleware 使用指南
# ============================================================================
"""
ToolCallLimitMiddleware 用于限制 Agent 执行过程中对工具的调用次数。
与 ModelCallLimitMiddleware 类似，但限制的是工具调用而非模型调用。

支持两种粒度的限制：
- Thread 级别：跨多次运行（invocation）累积计数
- Run 级别：单次运行内的计数

支持两种作用范围：
- 全局限制：限制所有工具的总调用次数（tool_name=None）
- 工具特定限制：限制特定工具的调用次数

使用示例：
----------

1. 全局限制（限制所有工具）：

    from langchain.agents import create_agent
    from langchain.agents.middleware import ToolCallLimitMiddleware

    agent = create_agent(
        model="gpt-4.1",
        tools=[search_tool, database_tool],
        middleware=[
            ToolCallLimitMiddleware(
                thread_limit=20,    # 每个线程最多 20 次工具调用
                run_limit=10,       # 每次运行最多 10 次工具调用
            ),
        ],
    )

2. 特定工具限制：

    agent = create_agent(
        model="gpt-4.1",
        tools=[search_tool, database_tool],
        middleware=[
            # 限制 search 工具的调用次数
            ToolCallLimitMiddleware(
                tool_name="search",
                thread_limit=5,
                run_limit=3,
            ),
        ],
    )

3. 组合全局限制和工具特定限制：

    agent = create_agent(
        model="gpt-4.1",
        tools=[search_tool, database_tool],
        middleware=[
            ToolCallLimitMiddleware(
                thread_limit=20,
                run_limit=10,
            ),
            ToolCallLimitMiddleware(
                tool_name="search",
                thread_limit=5,
                run_limit=3,
            ),
        ],
    )

4. 超出限制时的行为：

    # 继续执行，阻止超限工具调用（默认行为）
    ToolCallLimitMiddleware(
        thread_limit=5,
        exit_behavior="continue",
    )

    # 抛出异常
    ToolCallLimitMiddleware(
        thread_limit=5,
        exit_behavior="error",
    )

    # 立即停止（仅限单个工具调用）
    ToolCallLimitMiddleware(
        thread_limit=5,
        exit_behavior="end",
    )

参数说明：
----------

tool_name: str | None
    要限制的工具名称。如果为 None，则限制适用于所有工具。
    默认: None（全局限制）

thread_limit: int | None
    每个线程允许的最大工具调用次数。
    - None 表示不限制
    - 跨多次 agent.invoke() 调用累积计数

run_limit: int | None
    单次运行允许的最大工具调用次数。
    - None 表示不限制
    - 每次 agent.invoke() 调用独立计数

exit_behavior: Literal["continue", "error", "end"]
    超出限制时的行为：

    - "continue": 阻止超限的工具调用，但允许其他工具继续执行（默认）
    - "error": 抛出 ToolCallLimitExceededError 异常
    - "end": 立即停止执行，如果存在多个并行工具调用会抛出 NotImplementedError

异常说明：
----------

ToolCallLimitExceededError
    当 exit_behavior="error" 时，超出限制会抛出此异常。

    属性：
    - thread_count: 当前线程的工具调用次数
    - run_count: 当前运行的工具调用次数
    - thread_limit: 线程限制（可能为 None）
    - run_limit: 运行限制（可能为 None）
    - tool_name: 被限制的工具名称（None 表示全局限制）

状态说明：
----------

该中间件会向 AgentState 添加两个私有字段：
- thread_tool_call_count: 线程级别的累积调用计数（字典，按工具名索引）
- run_tool_call_count: 单次运行的调用计数（字典，按工具名索引）

特殊键 "__all__" 用于全局跟踪所有工具的调用次数。

注意事项：
----------
1. run_limit 不能超过 thread_limit（如果两者都设置了）
2. exit_behavior="end" 在有多个并行工具调用时会抛出 NotImplementedError
3. exit_behavior="continue" 会向模型返回错误消息，告知该工具已被阻止
4. 多个 ToolCallLimitMiddleware 实例可以同时使用，每个跟踪不同的工具
5. 在 after_model hook 中执行限制检查和计数更新
"""


# ============================================================================
# ModelFallbackMiddleware 使用指南
# ============================================================================
"""
ModelFallbackMiddleware 用于在主模型调用失败时，自动切换到备用模型。
这可以提高 Agent 的可靠性和容错能力。

工作原理：
- 首先尝试主模型（create_agent 时指定的模型）
- 如果失败，按顺序尝试配置的备用模型
- 成功则返回结果，全部失败则抛出最后一个异常

使用示例：
----------

1. 基本用法：

    from langchain.agents import create_agent
    from langchain.agents.middleware import ModelFallbackMiddleware

    agent = create_agent(
        model="gpt-4.1",  # 主模型
        tools=[],
        middleware=[
            ModelFallbackMiddleware(
                "gpt-4.1-mini",  # 第一个备用模型
                "claude-3-5-sonnet-20241022",  # 第二个备用模型
            ),
        ],
    )

2. 使用已初始化的模型实例：

    from langchain.chat_models import init_chat_model

    fallback = ModelFallbackMiddleware(
        init_chat_model("gpt-4.1-mini"),
        init_chat_model("claude-3-5-sonnet-20241022"),
    )

    agent = create_agent(
        model="gpt-4.1",
        middleware=[fallback],
    )

3. 单个备用模型：

    ModelFallbackMiddleware("gpt-4.1-mini")

参数说明：
----------

first_model: str | BaseChatModel
    第一个备用模型。可以是模型名称字符串（如 "gpt-4.1-mini"）
    或已初始化的 ChatModel 实例。

*additional_models: str | BaseChatModel
    额外的备用模型，按顺序尝试。可以是模型名称或实例。

工作流程：
----------

1. 调用主模型
2. 如果成功，返回结果
3. 如果失败，尝试第一个备用模型
4. 如果成功，返回结果
5. 如果失败，继续尝试下一个备用模型
6. 所有模型都失败，抛出最后一个异常

注意事项：
----------
1. 备用模型会按配置顺序依次尝试，直到成功或全部失败
2. 如果主模型成功，不会使用任何备用模型
3. 只有在模型调用抛出异常时才会触发备用切换
4. 最后一个异常会被重新抛出
5. 备用模型的模型调用参数（temperature、system_message 等）继承自主模型的请求
6. 使用字符串模型名时，会使用 init_chat_model 初始化
"""


# ============================================================================
# PIIMiddleware 使用指南
# ============================================================================
"""
PIIMiddleware 用于检测和处理对话中的个人身份信息（PII）。
可以检测电子邮件、信用卡号、IP 地址、MAC 地址和 URL，并提供多种处理策略。

内置 PII 类型：
--------------
- email: 电子邮件地址
- credit_card: 信用卡号（使用 Luhn 算法验证）
- ip: IP 地址
- mac_address: MAC 地址
- url: URL 地址

处理策略：
----------
- block: 检测到 PII 时抛出异常
- redact: 替换为 [REDACTED_TYPE] 占位符
- mask: 部分遮盖 PII（如信用卡显示为 ****-****-****-1234）
- hash: 替换为确定性哈希（如 <email_hash:a1b2c3d4>）

策略选择指南：
--------------
| 策略   | 保留身份？      | 适用场景                    |
|--------|-----------------|---------------------------|
| block  | N/A            | 完全避免 PII              |
| redact | 否             | 一般合规、日志脱敏         |
| mask   | 否             | 人类可读、客服界面         |
| hash   | 是（假名化）    | 分析、调试                 |

使用示例：
----------

1. 基本用法（输入脱敏）：

    from langchain.agents import create_agent
    from langchain.agents.middleware import PIIMiddleware

    agent = create_agent(
        model="gpt-4.1",
        tools=[],
        middleware=[
            PIIMiddleware("email", strategy="redact", apply_to_input=True),
        ],
    )

2. 信用卡号遮盖：

    PIIMiddleware("credit_card", strategy="mask", apply_to_input=True)

3. 对输出内容进行 PII 检测：

    PIIMiddleware(
        "email",
        strategy="redact",
        apply_to_input=True,
        apply_to_output=True,
    )

4. 多个 PII 类型组合：

    agent = create_agent(
        model="gpt-4.1",
        tools=[],
        middleware=[
            PIIMiddleware("email", strategy="redact", apply_to_input=True),
            PIIMiddleware("credit_card", strategy="mask", apply_to_input=True),
            PIIMiddleware("url", strategy="redact", apply_to_output=True),
        ],
    )

5. 自定义 PII 检测器（正则表达式）：

    PIIMiddleware(
        "api_key",
        detector=r"sk-[a-zA-Z0-9]{32}",
        strategy="block",
    )

6. 自定义 PII 检测器（函数）：

    def detect_phone(content):
        import re
        matches = re.finditer(r'\\b\\d{3}-\\d{4}-\\d{4}\\b', content)
        return [PIIMatch(start=m.start(), end=m.end(), match=m.group()) for m in matches]

    PIIMiddleware(
        "phone",
        detector=detect_phone,
        strategy="mask",
    )

参数说明：
----------

pii_type: Literal["email", "credit_card", "ip", "mac_address", "url"] | str
    要检测的 PII 类型。可以是内置类型或自定义类型名称。

strategy: Literal["block", "redact", "mask", "hash"]
    检测到 PII 后的处理策略：
    - "block": 抛出 PIIDetectionError 异常
    - "redact": 替换为 [REDACTED_TYPE] 占位符
    - "mask": 部分遮盖（保留最后几个字符）
    - "hash": 替换为确定性哈希

detector: Callable[[str], list[PIIMatch]] | str | None
    自定义检测器：
    - Callable: 接收内容字符串，返回 PIIMatch 列表
    - str: 正则表达式模式
    - None: 使用内置检测器

apply_to_input: bool
    是否在模型调用前检查用户消息。
    默认: True

apply_to_output: bool
    是否在模型调用后检查 AI 消息。
    默认: False

apply_to_tool_results: bool
    是否在工具执行后检查工具结果消息。
    默认: False

策略效果示例：
--------------

原始内容: "请联系我 john@example.com 或 4532-1234-5678-9012"
strategy="redact": "请联系我 [REDACTED_EMAIL] [REDACTED_CREDIT_CARD]"
strategy="mask": "请联系我 j***@e**.com ****-****-****-9012"
strategy="hash": "请联系我 <email_hash:abc123> <credit_card_hash:def456>"

注意事项：
----------
1. 可以在同一个 Agent 中使用多个 PIIMiddleware 实例检测不同类型的 PII
2. 内置检测器使用 Luhn 算法验证信用卡号，减少误报
3. hash 策略生成确定性哈希，相同输入产生相同输出，便于调试
4. 检测在 before_model 和 after_model hook 中进行
5. 只会检查最后一条用户消息和最后一条 AI 消息
6. 可以通过自定义 detector 支持任何正则表达式匹配模式
"""


# ============================================================================
# TodoListMiddleware 使用指南
# ============================================================================
"""
TodoListMiddleware 为 Agent 提供任务列表管理能力。
通过添加 write_todos 工具，允许 Agent 创建和管理结构化的任务列表，
以跟踪复杂多步骤操作的进度。

该中间件的主要功能：
- 添加 write_todos 工具供 Agent 调用
- 自动注入系统提示，指导 Agent 何时以及如何使用任务列表
- 防止并行调用 write_todos（因为每次调用会替换整个列表）

使用示例：
----------

1. 基本用法：

    from langchain.agents import create_agent
    from langchain.agents.middleware import TodoListMiddleware

    agent = create_agent(
        model="gpt-4.1",
        tools=[read_file, write_file, run_tests],
        middleware=[TodoListMiddleware()],
    )

2. 自定义提示词：

    TodoListMiddleware(
        system_prompt="使用任务列表来跟踪你的工作进度...",
        tool_description="自定义的工具描述...",
    )

参数说明：
----------

system_prompt: str
    系统提示词，指导 Agent 何时以及如何使用 write_todos 工具。
    包含何时使用、任务状态说明、管理规则等。

tool_description: str
    write_todos 工具的描述，影响 Agent 如何理解该工具的用途。

Todo 数据结构：
---------------

Todo 任务项包含以下字段：

content: str
    任务内容/描述

status: Literal["pending", "in_progress", "completed"]
    任务状态：
    - pending: 任务尚未开始
    - in_progress: 正在处理
    - completed: 已完成

write_todos 工具使用规则：
---------------------------

1. 何时使用：
   - 复杂多步骤任务（3 步或更多）
   - 需要仔细规划的任务
   - 用户明确要求使用任务列表
   - 用户提供多个任务需要完成

2. 何时不使用：
   - 简单单一任务
   - 可以少于 3 步完成的简单任务
   - 纯对话或信息查询

3. 使用规范：
   - 开始工作时立即将任务标记为 in_progress
   - 完成后立即标记为 completed
   - 不要批量标记完成
   - 遇到错误或阻塞时保持 in_progress 状态

状态字段：
----------

该中间件会向 AgentState 添加一个私有字段：
- todos: list[Todo] - 任务列表，从输入中省略

注意事项：
----------
1. write_todos 工具每轮模型调用最多调用一次
2. 多次并行调用会被拒绝并返回错误
3. 任务列表通过 checkpointer 持久化
4. 可以与 checkpointer（如 InMemorySaver）配合使用以保存状态
5. 任务状态会在 result["todos"] 中返回
"""


# ============================================================================
# LLMToolSelectorMiddleware 使用指南
# ============================================================================
"""
LLMToolSelectorMiddleware 使用 LLM 在调用主模型之前选择相关工具。
当 Agent 有很多工具可用时，此中间件会将工具筛选到与用户查询最相关的工具，
从而减少 token 使用量并帮助主模型专注于正确的工具。

工作原理：
- 在模型调用之前，使用一个 LLM（可以是主模型或更小的模型）来评估哪些工具与当前查询相关
- 根据相关性排序，选择最相关的工具
- 将筛选后的工具列表传递给主模型

使用示例：
----------

1. 基本用法（限制最多 3 个工具）：

    from langchain.agents import create_agent
    from langchain.agents.middleware import LLMToolSelectorMiddleware

    agent = create_agent(
        model="gpt-4.1",
        tools=[tool1, tool2, tool3, tool4, tool5],
        middleware=[
            LLMToolSelectorMiddleware(
                max_tools=3,
            ),
        ],
    )

2. 使用更小的模型进行选择：

    LLMToolSelectorMiddleware(
        model="gpt-4.1-mini",  # 使用更小更快的模型
        max_tools=3,
    )

3. 始终包含某些工具：

    LLMToolSelectorMiddleware(
        model="gpt-4.1-mini",
        max_tools=3,
        always_include=["search", "calculator"],  # 这些工具始终被包含
    )

4. 自定义系统提示：

    LLMToolSelectorMiddleware(
        model="gpt-4.1-mini",
        system_prompt="从工具列表中选择最适合回答用户问题的工具。",
        max_tools=5,
    )

参数说明：
----------

model: str | BaseChatModel | None
    用于工具选择的模型。
    - 如果不提供，使用 Agent 的主模型
    - 可以是模型标识符字符串（如 "gpt-4.1-mini"）
    - 或 BaseChatModel 实例

system_prompt: str
    选择模型的指令。
    默认: "Your goal is to select the most relevant tools for answering the user's query."

max_tools: int | None
    最多选择的工具数量。
    - 如果模型选择更多，则只使用前 max_tools 个
    - 如果不指定，则没有限制

always_include: list[str] | None
    始终包含的工具名称，无论选择结果如何。
    这些工具不计入 max_tools 限制。

工作流程：
----------

1. 从请求中获取可用的工具列表
2. 过滤出非 always_include 的工具作为候选
3. 构建包含系统提示和用户消息的选择请求
4. 调用 LLM 获取工具选择结果
5. 根据 max_tools 限制和 always_include 规则处理选择结果
6. 返回筛选后的工具列表

注意事项：
----------
1. 工具选择发生在 wrap_model_call hook 中，在主模型调用之前
2. 如果没有可用工具或所有工具都在 always_include 中，则跳过选择
3. always_include 中的工具必须存在于请求的工具列表中
4. 选择模型使用结构化输出，确保返回的工具名称有效
5. 如果模型选择了无效工具，会抛出 ValueError
6. 保留原始请求中的 provider-specific 工具字典（如 Anthropic 的特定工具格式）
"""


# ============================================================================
# ToolRetryMiddleware 使用指南
# ============================================================================
"""
ToolRetryMiddleware 自动重试失败的工具调用，支持可配置的退避策略。
当工具调用因临时性错误失败时，中间件会自动进行重试，提高 Agent 的鲁棒性。

主要功能：
- 自动重试失败的工具调用
- 支持指数退避策略
- 可配置重试的异常类型
- 可针对特定工具应用重试逻辑

使用示例：
----------

1. 基本用法（默认设置：2 次重试，指数退避）：

    from langchain.agents import create_agent
    from langchain.agents.middleware import ToolRetryMiddleware

    agent = create_agent(
        model="gpt-4.1",
        tools=[search_tool, database_tool],
        middleware=[
            ToolRetryMiddleware(),
        ],
    )

2. 自定义重试次数和退避策略：

    ToolRetryMiddleware(
        max_retries=3,
        backoff_factor=2.0,
        initial_delay=1.0,
    )

3. 仅重试特定异常：

    from requests.exceptions import RequestException, Timeout

    retry = ToolRetryMiddleware(
        max_retries=4,
        retry_on=(RequestException, Timeout),
        backoff_factor=1.5,
    )

4. 自定义异常过滤逻辑：

    from requests.exceptions import HTTPError

    def should_retry(exc: Exception) -> bool:
        # 仅重试 5xx 错误
        if isinstance(exc, HTTPError):
            return 500 <= exc.status_code < 600
        return False

    retry = ToolRetryMiddleware(
        max_retries=3,
        retry_on=should_retry,
    )

5. 特定工具应用重试：

    retry = ToolRetryMiddleware(
        max_retries=4,
        tools=["search_database"],
        on_failure="continue",
    )

6. 自定义错误格式化：

    def format_error(exc: Exception) -> str:
        return f"数据库暂时不可用: {str(exc)}"

    retry = ToolRetryMiddleware(
        max_retries=4,
        tools=["search_database"],
        on_failure=format_error,
    )

7. 恒定退避（无指数增长）：

    retry = ToolRetryMiddleware(
        max_retries=5,
        backoff_factor=0.0,  # 无指数增长
        initial_delay=2.0,   # 始终等待 2 秒
    )

8. 重试失败时抛出异常：

    retry = ToolRetryMiddleware(
        max_retries=2,
        on_failure="error",  # 重新抛出异常，停止 Agent 执行
    )

参数说明：
----------

max_retries: int
    初始调用后的最大重试次数。
    默认: 2
    必须 >= 0

tools: list[BaseTool | str] | None
    应用重试逻辑的工具列表。
    - 可以是 BaseTool 实例或工具名称字符串
    - 如果为 None，则应用于所有工具

retry_on: RetryOn
    要重试的异常类型，可以是：
    - 异常类型元组：retry_on=(ValueError, Timeout)
    - 可调用函数：接收异常并返回 True/False

on_failure: OnFailure
    所有重试都用尽后的行为：
    - "continue": 返回包含错误详情的 ToolMessage，允许 LLM 处理
    - "error": 重新抛出异常，停止 Agent 执行
    - 可调用函数：接收异常并返回 ToolMessage 内容字符串

backoff_factor: float
    指数退避的乘数。
    每次重试等待 initial_delay * (backoff_factor ** retry_number) 秒。
    设置为 0.0 表示恒定延迟。
    默认: 2.0

initial_delay: float
    首次重试前的初始延迟（秒）。
    默认: 1.0

max_delay: float
    重试之间的最大延迟（秒），限制指数退避增长。
    默认: 60.0

jitter: bool
    是否添加随机抖动（±25%）以避免雷鸣般的群体效应。
    默认: True

重试延迟计算：
--------------

延迟 = min(initial_delay * (backoff_factor ** attempt) + random_jitter, max_delay)

例如，initial_delay=1.0, backoff_factor=2.0, max_delay=60.0：
- 第 1 次重试: 约 1-2.5 秒
- 第 2 次重试: 约 2-5 秒
- 第 3 次重试: 约 4-10 秒
- 后续重试会被 max_delay 限制在约 60 秒

注意事项：
----------
1. 重试发生在 wrap_tool_call hook 中，拦截工具执行
2. retry_on 可以是异常类型元组或自定义过滤函数
3. 第一次调用不计入重试次数，max_retries=2 表示最多 3 次尝试
4. on_failure="continue" 返回 ToolMessage 而非抛出异常
5. 同步版本使用 time.sleep，异步版本使用 asyncio.sleep
6. 可以同时对多个工具应用不同的重试配置
"""


# ============================================================================
# ModelRetryMiddleware 使用指南
# ============================================================================
"""
ModelRetryMiddleware 自动重试失败的模型调用，支持可配置的退避策略。
当模型调用因临时性错误（如速率限制、超时等）失败时，中间件会自动进行重试，提高 Agent 的可靠性。

ModelRetryMiddleware 与 ToolRetryMiddleware 的区别：
- ModelRetryMiddleware 作用于模型调用（wrap_model_call hook）
- ToolRetryMiddleware 作用于工具调用（wrap_tool_call hook）

主要功能：
- 自动重试失败的模型调用
- 支持指数退避策略
- 可配置重试的异常类型
- 可自定义错误处理行为

使用示例：
----------

1. 基本用法（默认设置：2 次重试，指数退避）：

    from langchain.agents import create_agent
    from langchain.agents.middleware import ModelRetryMiddleware

    agent = create_agent(
        model="gpt-4.1",
        tools=[search_tool, database_tool],
        middleware=[
            ModelRetryMiddleware(),
        ],
    )

2. 自定义重试次数和退避策略：

    ModelRetryMiddleware(
        max_retries=3,
        backoff_factor=2.0,
        initial_delay=1.0,
    )

3. 仅重试特定异常（如速率限制和超时）：

    from anthropic import RateLimitError
    from openai import APITimeoutError

    retry = ModelRetryMiddleware(
        max_retries=4,
        retry_on=(APITimeoutError, RateLimitError),
        backoff_factor=1.5,
    )

4. 自定义异常过滤逻辑：

    from anthropic import APIStatusError

    def should_retry(exc: Exception) -> bool:
        # 仅重试 5xx 错误
        if isinstance(exc, APIStatusError):
            return 500 <= exc.status_code < 600
        return False

    retry = ModelRetryMiddleware(
        max_retries=3,
        retry_on=should_retry,
    )

5. 自定义错误处理：

    def format_error(exc: Exception) -> str:
        return "模型暂时不可用，请稍后再试。"

    retry = ModelRetryMiddleware(
        max_retries=4,
        on_failure=format_error,
    )

6. 恒定退避（无指数增长）：

    retry = ModelRetryMiddleware(
        max_retries=5,
        backoff_factor=0.0,  # 无指数增长
        initial_delay=2.0,   # 始终等待 2 秒
    )

7. 重试失败时抛出异常：

    retry = ModelRetryMiddleware(
        max_retries=2,
        on_failure="error",  # 重新抛出异常，停止 Agent 执行
    )

参数说明：
----------

max_retries: int
    初始调用后的最大重试次数。
    默认: 2
    必须 >= 0

retry_on: RetryOn
    要重试的异常类型，可以是：
    - 异常类型元组：retry_on=(ValueError, Timeout)
    - 可调用函数：接收异常并返回 True/False
    默认: (Exception,) - 重试所有异常

on_failure: OnFailure
    所有重试都用尽后的行为：
    - "continue": 返回包含错误详情的 AIMessage，允许 Agent 继续执行
    - "error": 重新抛出异常，停止 Agent 执行
    - 可调用函数：接收异常并返回 AIMessage 内容字符串
    默认: "continue"

backoff_factor: float
    指数退避的乘数。
    每次重试等待 initial_delay * (backoff_factor ** retry_number) 秒。
    设置为 0.0 表示恒定延迟。
    默认: 2.0

initial_delay: float
    首次重试前的初始延迟（秒）。
    默认: 1.0

max_delay: float
    重试之间的最大延迟（秒），限制指数退避增长。
    默认: 60.0

jitter: bool
    是否添加随机抖动（±25%）以避免雷鸣般的群体效应。
    默认: True

与 ToolRetryMiddleware 的区别：
-------------------------------

| 特性         | ModelRetryMiddleware      | ToolRetryMiddleware       |
|-------------|-------------------------|-------------------------|
| 作用对象     | 模型调用                  | 工具调用                  |
| Hook        | wrap_model_call          | wrap_tool_call           |
| 失败时返回   | AIMessage                | ToolMessage              |
| 适用场景     | API 超时、速率限制        | 网络错误、服务不可用      |

注意事项：
----------
1. 重试发生在 wrap_model_call hook 中，拦截模型调用
2. retry_on 可以是异常类型元组或自定义过滤函数
3. 第一次调用不计入重试次数，max_retries=2 表示最多 3 次尝试
4. on_failure="continue" 返回 AIMessage 而非抛出异常
5. 同步版本使用 time.sleep，异步版本使用 asyncio.sleep
6. 与 ToolRetryMiddleware 可同时使用，分别处理模型和工具的失败情况
"""


# ============================================================================
# LLMToolEmulator 使用指南
# ============================================================================
"""
LLMToolEmulator 使用 LLM 模拟工具执行，用于测试目的。
当工具需要真实执行但又想快速测试 Agent 时，可以使用此中间件模拟工具响应。

主要用途：
- 单元测试：模拟工具响应而不需要真实的外部服务
- 集成测试：在 CI/CD 环境中快速测试 Agent 行为
- 开发调试：不需要搭建真实的后端服务即可测试

工作原理：
- 拦截指定的工具调用
- 使用 LLM 生成符合工具描述和参数的模拟响应
- 返回模拟的 ToolMessage，而不是真正执行工具

使用示例：
----------

1. 模拟所有工具（默认行为）：

    from langchain.agents import create_agent
    from langchain.agents.middleware import LLMToolEmulator

    agent = create_agent(
        model="gpt-4.1",
        tools=[get_weather, search_database, send_email],
        middleware=[
            LLMToolEmulator(),  # 模拟所有工具
        ],
    )

2. 仅模拟特定工具：

    LLMToolEmulator(tools=["get_weather", "search_database"])

3. 使用自定义模型进行模拟：

    LLMToolEmulator(
        tools=["get_weather"],
        model="anthropic:claude-sonnet-4-5-20250929",
    )

4. 通过工具实例指定：

    LLMToolEmulator(tools=[get_weather, get_user_location])

参数说明：
----------

tools: list[str | BaseTool] | None
    要模拟的工具列表。
    - None: 模拟所有工具（默认）
    - 空列表 []: 不模拟任何工具
    - [tool1, tool2]: 模拟指定的工具（可以是名称字符串或 BaseTool 实例）

model: str | BaseChatModel | None
    用于模拟的模型。
    - 默认为 "anthropic:claude-sonnet-4-5-20250929"，temperature=1
    - 可以是模型标识符字符串
    - 或 BaseChatModel 实例

模拟器提示词：
-------------

模拟器使用以下提示词生成工具响应：

    You are emulating a tool call for testing purposes.

    Tool: {tool_name}
    Description: {tool_description}
    Arguments: {tool_args}

    Generate a realistic response that this tool would return
    given these arguments.
    Return ONLY the tool's output, no explanation or preamble.
    Introduce variation into your responses.

注意事项：
----------
1. 模拟发生在 wrap_tool_call hook 中，拦截工具调用
2. 模拟的工具不执行真实操作，直接返回 LLM 生成的响应
3. 模拟结果具有随机性（temperature=1），相同调用可能产生不同结果
4. 模拟适用于测试 Agent 的工具调用逻辑，不适用于测试工具本身的正确性
5. 模拟响应可能与真实工具响应有差异，测试时需注意
"""


# ============================================================================
# ContextEditingMiddleware 使用指南
# ============================================================================
"""
ContextEditingMiddleware 自动裁剪工具结果以管理上下文大小。
当对话长度超过配置的 token 阈值时，中间件会清除较旧的工具结果。
此实现参考了 Anthropic 的 context editing 功能。

工作原理：
- 在模型调用之前计算消息的 token 总数
- 如果 token 数超过触发阈值，应用编辑策略清除部分工具结果
- 将清除后的消息传递给主模型

ClearToolUsesEdit 策略：
- 保留最近 N 条工具结果（默认保留 3 条）
- 将被清除的工具结果替换为占位符 "[cleared]"
- 可选择清除工具调用参数

使用示例：
----------

1. 基本用法（默认设置）：

    from langchain.agents import create_agent
    from langchain.agents.middleware import ContextEditingMiddleware

    agent = create_agent(
        model="gpt-4.1",
        tools=[],
        middleware=[
            ContextEditingMiddleware(),
        ],
    )

2. 自定义触发阈值和保留数量：

    ContextEditingMiddleware(
        edits=[
            ClearToolUsesEdit(
                trigger=100000,  # token 数超过 100000 时触发
                keep=3,          # 保留最近 3 条工具结果
            ),
        ],
    )

3. 指定最小清除 token 数：

    ClearToolUsesEdit(
        trigger=50000,
        keep=5,
        clear_at_least=10000,  # 至少清除 10000 token
    )

4. 排除特定工具：

    ClearToolUsesEdit(
        trigger=80000,
        keep=3,
        exclude_tools=["critical_operation", "get_user_data"],
    )

5. 同时清除工具输入参数：

    ClearToolUsesEdit(
        trigger=100000,
        keep=3,
        clear_tool_inputs=True,  # 同时清除 AI 消息中的工具调用参数
    )

6. 自定义占位符：

    ClearToolUsesEdit(
        trigger=100000,
        keep=3,
        placeholder="[已清除工具结果]",
    )

7. 使用精确 token 计数：

    ContextEditingMiddleware(
        token_count_method="model",  # 使用模型的精确计数
    )

8. 组合多个编辑策略：

    from langchain.agents.middleware.context_editing import ClearToolUsesEdit

    ContextEditingMiddleware(
        edits=[
            ClearToolUsesEdit(trigger=100000, keep=5),
            ClearToolUsesEdit(trigger=200000, keep=10, clear_tool_inputs=True),
        ],
    )

ContextEditingMiddleware 参数说明：
----------------------------------

edits: Iterable[ContextEdit] | None
    要应用的编辑策略序列。
    默认为 [ClearToolUsesEdit()]

token_count_method: Literal["approximate", "model"]
    Token 计数方法：
    - "approximate": 使用近似计数（更快，精度较低）
    - "model": 使用模型的精确计数（可能较慢，更精确）

ClearToolUsesEdit 参数说明：
---------------------------

trigger: int
    触发编辑的 token 数量阈值。
    当消息 token 总数超过此值时触发清除。
    默认: 100000

keep: int
    保留的最近工具结果数量。
    默认: 3

clear_at_least: int
    最小要清除的 token 数。
    当触发后，至少清除这么多 token 才停止。
    默认: 0（不清除最低要求）

clear_tool_inputs: bool
    是否清除 AI 消息中的工具调用参数。
    如果为 True，AI 消息中的 tool_calls 参数会被清空。
    默认: False

exclude_tools: Sequence[str]
    排除在清除范围外的工具名称列表。
    这些工具的结果不会被清除。

placeholder: str
    清除工具结果后插入的占位符文本。
    默认: "[cleared]"

使用场景：
----------

1. 长对话管理：当对话历史很长时，自动清除旧工具结果
2. Token 成本控制：防止上下文过长导致高成本
3. 模型注意力聚焦：让模型更关注最近的工具结果

注意事项：
----------
1. 编辑发生在 wrap_model_call hook 中，在主模型调用之前
2. 被清除的工具结果不会完全删除，而是替换为占位符
3. 保留的工具结果是最近的 N 条，不包括被排除的工具
4. token_count_method="model" 需要模型支持 get_num_tokens_from_messages 方法
5. 多个编辑策略会按顺序应用
6. 此中间件与 SummarizationMiddleware 功能类似，但实现不同
"""


# ============================================================================
# ShellToolMiddleware 使用指南
# ============================================================================
"""
ShellToolMiddleware 为 Agent 提供持久化的 shell 会话工具。
Agent 可以通过此中间件执行 shell 命令，适用于代码开发、文件操作等场景。

工作原理：
- 创建一个持久化的 shell 会话（默认使用 bash）
- Agent 通过 shell 工具执行命令
- 支持超时控制、输出截断、PII 脱敏
- 会话在 Agent 运行期间保持活跃

三种执行策略：
------------

1. HostExecutionPolicy
   - 直接在主机上执行命令
   - 适用于可信环境或已有容器/VM 隔离的场景
   - 提供完整的宿主访问权限

2. DockerExecutionPolicy
   - 每次 Agent 运行启动独立的 Docker 容器
   - 提供更强的隔离性
   - 支持只读根文件系统
   - 支持用户映射

3. CodexSandboxExecutionPolicy
   - 使用 Codex CLI 沙箱执行
   - 提供系统调用和文件系统限制

使用示例：
----------

1. 基本用法（主机执行）：

    from langchain.agents import create_agent
    from langchain.agents.middleware import ShellToolMiddleware, HostExecutionPolicy

    agent = create_agent(
        model="gpt-4.1",
        tools=[search_tool],
        middleware=[
            ShellToolMiddleware(
                workspace_root="/workspace",
                execution_policy=HostExecutionPolicy(),
            ),
        ],
    )

2. Docker 容器隔离：

    from langchain.agents.middleware import ShellToolMiddleware, DockerExecutionPolicy

    ShellToolMiddleware(
        workspace_root="/workspace",
        execution_policy=DockerExecutionPolicy(
            image="python:3.11",
            read_only=True,
        ),
    )

3. 自定义 shell 命令：

    ShellToolMiddleware(
        shell_command=["/bin/bash", "--login"],
    )

4. 启动和关闭命令：

    ShellToolMiddleware(
        workspace_root="/workspace",
        startup_commands=["export PATH=/usr/local/bin:$PATH"],
        shutdown_commands=["rm -rf /tmp/*"],
    )

5. 自定义工具描述：

    ShellToolMiddleware(
        tool_description="执行 shell 命令的持久化会话工具...",
    )

6. 环境变量配置：

    ShellToolMiddleware(
        workspace_root="/workspace",
        env={"DEBUG": "1", "LOG_LEVEL": "info"},
    )

7. PII 脱敏规则：

    from langchain.agents.middleware._redaction import RedactionRule

    ShellToolMiddleware(
        workspace_root="/workspace",
        redaction_rules=[
            RedactionRule(pii_type="email", strategy="redact"),
        ],
    )

参数说明：
----------

workspace_root: str | Path | None
    Shell 会话的工作目录。
    如果不指定，会创建临时目录，Agent 结束时自动清理。

startup_commands: tuple[str, ...] | list[str] | str | None
    会话启动后执行的命令序列。
    用于设置环境变量、创建目录等初始化操作。

shutdown_commands: tuple[str, ...] | list[str] | str | None
    会话关闭前执行的命令序列。
    用于清理临时文件等收尾操作。

execution_policy: BaseExecutionPolicy | None
    执行策略，控制超时、输出限制等。
    默认为 HostExecutionPolicy()。

redaction_rules: tuple[RedactionRule, ...] | None
    PII 脱敏规则，对命令输出进行脱敏处理。
    注意：脱敏发生在命令执行后，不会阻止敏感数据泄露。

tool_description: str | None
    工具描述，覆盖默认描述。

tool_name: str
    工具名称。
    默认: "shell"

shell_command: Sequence[str] | str | None
    Shell 执行命令。
    默认为 /bin/bash。

env: Mapping[str, Any] | None
    环境变量，会传递给 shell 会话。

执行策略配置（HostExecutionPolicy）：
------------------------------------

command_timeout: float
    命令执行超时时间（秒）。
    默认: 60.0

startup_timeout: float
    启动命令超时时间（秒）。
    默认: 30.0

termination_timeout: float
    终止会话超时时间（秒）。
    默认: 10.0

max_output_lines: int | None
    最大输出行数。
    默认: 10000

max_output_bytes: int | None
    最大输出字节数。
    默认: None（无限制）

执行策略配置（DockerExecutionPolicy）：
-------------------------------------

image: str
    Docker 镜像。
    如 "python:3.11"

read_only: bool
    是否使用只读根文件系统。
    默认: False

user: int | None
    运行用户的 UID。
    默认: None（使用默认用户）

command_timeout, startup_timeout, termination_timeout, max_output_lines, max_output_bytes
    同 HostExecutionPolicy

Shell 工具使用方式：
-------------------

Agent 可以调用以下命令：

1. 执行命令：
   {"command": "ls -la /workspace"}

2. 重启会话：
   {"restart": true}

命令输出包含：
- stdout/stderr 内容
- 退出码
- 超时信息
- 截断信息
- 脱敏匹配结果

注意事项：
----------
1. Shell 会话是持久化的，多个命令共享同一会话状态
2. 超时会导致会话重启，可能会话状态丢失
3. 使用 HostExecutionPolicy 时注意安全问题
4. 脱敏规则不会阻止命令执行，只是对输出进行处理
5. 临时目录会在 Agent 结束时自动清理
6. 建议使用绝对路径，避免路径问题
"""


# ============================================================================
# FilesystemFileSearchMiddleware 使用指南
# ============================================================================
"""
FilesystemFileSearchMiddleware 为 Agent 提供文件系统搜索功能。
添加两个搜索工具：Glob（文件模式匹配）和 Grep（内容搜索）。

提供的工具：
-----------

1. glob_search
   快速文件模式匹配工具，支持 glob 模式如 **/*.js 或 src/**/*.ts。
   返回匹配文件的路径列表，按修改时间排序。

2. grep_search
   快速内容搜索工具，使用正则表达式搜索文件内容。
   支持 ripgrep（如果可用）或 Python 回退实现。

使用示例：
----------

1. 基本用法：

    from langchain.agents import create_agent
    from langchain.agents.middleware import FilesystemFileSearchMiddleware

    agent = create_agent(
        model="gpt-4.1",
        tools=[],
        middleware=[
            FilesystemFileSearchMiddleware(
                root_path="/workspace",
            ),
        ],
    )

2. 禁用 ripgrep，使用 Python 搜索：

    FilesystemFileSearchMiddleware(
        root_path="/workspace",
        use_ripgrep=False,
    )

3. 限制最大文件大小：

    FilesystemFileSearchMiddleware(
        root_path="/workspace",
        max_file_size_mb=5,
    )

参数说明：
----------

root_path: str
    搜索的根目录。

use_ripgrep: bool
    是否使用 ripgrep 进行搜索。
    如果 ripgrep 不可用，自动回退到 Python 实现。
    默认: True

max_file_size_mb: int
    搜索的最大文件大小（MB）。
    超过此大小的文件会被跳过。
    默认: 10

glob_search 工具参数：
--------------------

pattern: str
    glob 模式，如 **/*.py 或 src/**/*.ts。

path: str
    搜索的目录路径，默认为根目录。

grep_search 工具参数：
--------------------

pattern: str
    正则表达式搜索模式。

path: str
    搜索的目录路径，默认为根目录。

include: str | None
    文件过滤模式，如 *.py 或 *.{py,pyi}。

output_mode: Literal["files_with_matches", "content", "count"]
    输出格式：
    - files_with_matches: 只返回包含匹配的文件路径
    - content: 返回 file:line:content 格式的匹配行
    - count: 返回每个文件的匹配计数

安全特性：
---------

1. 路径遍历保护：不允许 .. 或 ~ 路径
2. 虚拟路径：返回给 Agent 的是虚拟路径（如 /src/main.py）
3. 根目录限制：所有搜索都限制在 root_path 内

注意事项：
----------
1. ripgrep 优先，失败时自动回退到 Python 实现
2. 文件大小超过 max_file_size_mb 会被跳过
3. 返回的路径是虚拟路径，相对于 root_path
4. grep_search 支持完整的正则表达式语法
5. 搜索结果按文件路径排序返回
"""
