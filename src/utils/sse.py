"""SSE 事件格式化工具"""

import json

from pydantic import BaseModel


def _json_default(obj):
    """Pydantic 对象序列化兜底。"""
    if isinstance(obj, BaseModel):
        return obj.model_dump()
    return str(obj)


def format_sse_event(node_name: str, data: dict) -> dict:
    """将图节点输出格式化为 SSE 事件。"""
    return {
        "event": node_name,
        "data": json.dumps(
            {"node": node_name, "update": data},
            ensure_ascii=False,
            default=_json_default,
        ),
    }


def format_sse_done() -> dict:
    """生成流结束事件。"""
    return {
        "event": "final",
        "data": json.dumps({"done": True}, ensure_ascii=False),
    }
