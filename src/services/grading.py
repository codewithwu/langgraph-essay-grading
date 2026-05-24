"""评分服务：桥接 LangGraph 图到 async 接口"""

import asyncio
import queue
import threading
from collections.abc import AsyncGenerator

from langgraph_essay_grading import EssayState, graph


def _run_graph_stream(state: EssayState, q: queue.Queue) -> None:
    """在独立线程中运行图流，将事件放入队列。"""
    try:
        for event in graph.stream(state, stream_mode="updates"):
            q.put(event)
    except Exception as e:
        q.put(e)
    finally:
        q.put(None)


async def grade_essay_stream(state: EssayState) -> AsyncGenerator[dict, None]:
    """异步生成器：逐节点产出评分事件。"""
    q: queue.Queue = queue.Queue()
    thread = threading.Thread(target=_run_graph_stream, args=(state, q), daemon=True)
    thread.start()

    while True:
        event = await asyncio.to_thread(q.get)
        if event is None:
            break
        if isinstance(event, Exception):
            raise event
        yield event


def grade_essay_sync(state: EssayState) -> dict:
    """同步调用图，返回最终状态。"""
    return graph.invoke(state)
