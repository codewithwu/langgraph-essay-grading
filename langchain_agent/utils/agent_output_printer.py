"""Agent 输出美化打印工具"""

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.messages import SystemMessage
from langchain_core.messages import ToolMessage
from rich.console import Console
from rich.panel import Panel


class AgentOutputPrinter:
    """Agent 输出美化打印工具类"""

    def __init__(self):
        self.console = Console()

    @staticmethod
    def pprint(output: dict) -> None:
        """打印 Agent 输出的美观格式

        Args:
            output: Agent 输出字典，包含 messages 列表

        示例:
            from langchain_agent.utils.agent_output_printer import AgentOutputPrinter

            result = agent.invoke({"messages": [("user", "hello")]})
            AgentOutputPrinter.pprint(result)
        """
        printer = AgentOutputPrinter()
        printer._print_output(output)

    def _print_output(self, output: dict) -> None:
        """打印整个 agent 输出"""
        messages = output.get("messages", [])
        if not messages:
            self.console.print("[yellow]No messages in output[/yellow]")
            return

        self.console.print(
            Panel("[b]Agent Output[/b]", border_style="green", padding=(1, 1))
        )
        self.console.print()

        for i, msg in enumerate(messages):
            self._print_message(msg, i)

        # 打印 structured_response（如果有）
        structured = output.get("structured_response")
        if structured is not None:
            self.console.print()
            self.console.print(
                Panel(
                    str(structured),
                    title="[b]structured_response[/b]",
                    border_style="yellow",
                    padding=(1, 1),
                )
            )

    def _print_message(self, msg: BaseMessage | dict, index: int) -> None:
        """打印单条消息"""
        if isinstance(msg, dict):
            msg = self._dict_to_message(msg)

        msg_type = type(msg).__name__
        border_style = self._get_message_color(msg_type)

        title = f"[b]{msg_type}[/b] [dim]#{index + 1}[/dim]"

        # 构建完整内容
        body = self._build_message_body(msg)

        self.console.print(
            Panel(
                body,
                title=title,
                border_style=border_style,
                padding=(1, 1),
            )
        )

    def _build_message_body(self, msg: BaseMessage) -> str:
        """构建消息完整内容"""
        lines = []

        # 1. content - 主要文本内容
        if isinstance(msg, (SystemMessage, HumanMessage, AIMessage)):
            content = msg.content if msg.content else "[dim](empty)[/dim]"
            lines.append(f"[b]content[/b]:\n{content}")
        elif isinstance(msg, ToolMessage):
            lines.append(f"[b]content[/b]:\n{msg.content}")

        # 2. 通用字段 - id
        msg_id = getattr(msg, "id", None)
        if msg_id:
            lines.append(f"[b]id[/b]: {msg_id}")

        # 3. AIMessage 特有字段
        if isinstance(msg, AIMessage):
            # additional_kwargs
            additional = getattr(msg, "additional_kwargs", None) or {}
            if additional:
                lines.append("[b]additional_kwargs[/b]:")
                for k, v in additional.items():
                    lines.append(f"  {k}: {v}")

            # response_metadata
            meta = getattr(msg, "response_metadata", None) or {}
            if meta:
                lines.append("[b]response_metadata[/b]:")
                for k, v in meta.items():
                    if isinstance(v, dict):
                        lines.append(f"  {k}:")
                        for sk, sv in v.items():
                            lines.append(f"    {sk}: {sv}")
                    else:
                        lines.append(f"  {k}: {v}")

            # usage_metadata
            usage = getattr(msg, "usage_metadata", None) or {}
            if usage:
                lines.append("[b]usage_metadata[/b]:")
                for k, v in usage.items():
                    if isinstance(v, dict):
                        lines.append(f"  {k}:")
                        for sk, sv in v.items():
                            lines.append(f"    {sk}: {sv}")
                    else:
                        lines.append(f"  {k}: {v}")

            # tool_calls
            tool_calls = getattr(msg, "tool_calls", None) or []
            if tool_calls:
                lines.append("[b]tool_calls[/b]:")
                for tc in tool_calls:
                    lines.append(f"  - name: {tc.get('name')}")
                    lines.append(f"    args: {tc.get('args')}")
                    lines.append(f"    id: {tc.get('id')}")
                    lines.append(f"    type: {tc.get('type')}")

            # invalid_tool_calls
            invalid = getattr(msg, "invalid_tool_calls", None) or []
            if invalid:
                lines.append(f"[b]invalid_tool_calls[/b]: {invalid}")

        # 4. ToolMessage 特有字段
        if isinstance(msg, ToolMessage):
            if msg.name:
                lines.append(f"[b]name[/b]: {msg.name}")
            if msg.tool_call_id:
                lines.append(f"[b]tool_call_id[/b]: {msg.tool_call_id}")

        return "\n".join(lines)

    def _dict_to_message(self, msg_dict: dict) -> BaseMessage:
        """将字典转换为对应类型的消息对象"""
        content = msg_dict.get("content", "")
        msg_type = msg_dict.get("type", "")

        if msg_type == "system":
            return SystemMessage(content=content)
        elif msg_type == "human":
            return HumanMessage(content=content)
        elif msg_type == "ai":
            return AIMessage(
                content=content,
                additional_kwargs=msg_dict.get("additional_kwargs", {}),
                response_metadata=msg_dict.get("response_metadata", {}),
                id=msg_dict.get("id"),
                tool_calls=msg_dict.get("tool_calls", []),
                invalid_tool_calls=msg_dict.get("invalid_tool_calls", []),
                usage_metadata=msg_dict.get("usage_metadata"),
            )
        elif msg_type == "tool":
            return ToolMessage(
                content=content,
                name=msg_dict.get("name"),
                id=msg_dict.get("id"),
                tool_call_id=msg_dict.get("tool_call_id"),
            )
        else:
            # 兜底创建 AIMessage
            return AIMessage(content=content)

    def _get_message_color(self, msg_type: str) -> str:
        """根据消息类型获取颜色"""
        colors = {
            "SystemMessage": "blue",
            "HumanMessage": "green",
            "AIMessage": "cyan",
            "ToolMessage": "magenta",
        }
        return colors.get(msg_type, "white")
