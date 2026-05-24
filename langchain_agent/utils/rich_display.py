"""AIMessage 美化打印工具"""

from langchain_core.messages import AIMessage
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


class AIMessagePrinter:
    """AIMessage 美化打印工具类"""

    def __init__(self):
        self.console = Console()

    @staticmethod
    def pprint(message: AIMessage | dict) -> None:
        """打印 AIMessage 的美观格式

        Args:
            message: AIMessage 对象或字典

        示例:
            response = llm.invoke("hello")
            AIMessagePrinter.pprint(response)

            # 调取各字段的方式:
            # response.content                          # 文本内容
            # response.response_metadata['token_usage'] # Token 统计
            # response.response_metadata['model_name'] # 模型名称
            # response.id                              # 消息ID
            # response.tool_calls                      # 工具调用列表
            # response.usage_metadata['total_tokens']  # 总Token数
        """
        printer = AIMessagePrinter()
        printer._print_message(message)

    def _print_message(self, message: AIMessage | dict) -> None:
        """内部打印方法"""
        if isinstance(message, dict):
            message = AIMessage(**message) if "content" in message else None
        if message is None:
            self.console.print("[red]无效的消息格式[/red]")
            return

        self._print_all_fields(message)

    def _print_all_fields(self, message: AIMessage) -> None:
        """打印所有字段，结构清晰，方便查看如何调取"""

        # 1. content - 主要文本内容
        self.console.print(
            Panel(
                message.content
                if isinstance(message.content, str)
                else str(message.content),
                title="[b]content[/b] <- message.content",
                border_style="cyan",
                padding=(1, 1),
            )
        )

        # 2. id - 消息唯一标识
        self._safe_print("id", message.id, "blue")

        # 3. response_metadata - 响应元数据（嵌套结构）
        meta = message.response_metadata or {}
        if meta:
            self._print_response_metadata(meta)

        # 4. usage_metadata - Token 使用统计
        usage = getattr(message, "usage_metadata", None) or {}
        if usage:
            self._print_usage_metadata(usage)

        # 5. tool_calls - 工具调用列表
        tool_calls = getattr(message, "tool_calls", None) or []
        self._print_tool_calls(tool_calls)

        # 6. invalid_tool_calls - 无效的工具调用
        invalid = getattr(message, "invalid_tool_calls", None) or []
        if invalid:
            self.console.print(
                Panel(
                    str(invalid),
                    title="[b]invalid_tool_calls[/b] <- message.invalid_tool_calls",
                    border_style="red",
                    padding=(1, 1),
                )
            )

        # 7. additional_kwargs - 额外参数
        additional = getattr(message, "additional_kwargs", None) or {}
        if additional:
            table = Table(
                title="[b]additional_kwargs[/b] <- message.additional_kwargs",
                show_header=False,
                box=None,
            )
            table.add_column("key", style="cyan")
            table.add_column("value", style="white")
            for key, value in additional.items():
                table.add_row(key, str(value))
            self.console.print(table)

    def _safe_print(self, title: str, value, color: str) -> None:
        """安全打印非空字段"""
        if value:
            self.console.print(
                Panel(
                    str(value),
                    title=f"[b]{title}[/b] <- message.{title}",
                    border_style=color,
                    padding=(1, 1),
                )
            )

    def _print_response_metadata(self, meta: dict) -> None:
        """打印 response_metadata，扁平化显示路径"""
        table = Table(
            title="[b]response_metadata[/b] <- message.response_metadata",
            show_header=False,
            box=None,
        )
        table.add_column("path", style="cyan")
        table.add_column("value", style="white")

        for key, value in meta.items():
            if isinstance(value, dict):
                # 嵌套字典扁平化显示
                for sub_key, sub_value in value.items():
                    table.add_row(f"{key}.{sub_key}", str(sub_value))
            else:
                table.add_row(key, str(value))

        self.console.print(table)

    def _print_usage_metadata(self, usage: dict) -> None:
        """打印 usage_metadata"""
        table = Table(
            title="[b]usage_metadata[/b] <- message.usage_metadata",
            show_header=False,
            box=None,
        )
        table.add_column("path", style="yellow")
        table.add_column("value", style="white")

        for key, value in usage.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    table.add_row(f"{key}.{sub_key}", str(sub_value))
            else:
                table.add_row(key, str(value))

        self.console.print(table)

    def _print_tool_calls(self, tool_calls: list) -> None:
        """打印 tool_calls"""
        self.console.print(
            Panel(
                str(tool_calls) if tool_calls else "[]",
                title="[b]tool_calls[/b] <- message.tool_calls",
                border_style="magenta",
                padding=(1, 1),
            )
        )
