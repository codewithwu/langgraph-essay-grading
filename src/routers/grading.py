"""评分路由"""

import asyncio

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from langgraph_essay_grading import EssayState
from src.models.requests import GradeRequest
from src.models.responses import GradeResponse, ScoreDetailResponse
from src.services.grading import grade_essay_stream, grade_essay_sync
from src.utils.sse import format_sse_done, format_sse_event

router = APIRouter(prefix="/api/essays", tags=["评分"])


def _to_score_detail(raw) -> ScoreDetailResponse:
    """将 ScoreDetail 对象或 dict 转换为响应模型。"""
    if isinstance(raw, dict):
        return ScoreDetailResponse(**raw)
    return ScoreDetailResponse(score=raw.score, reason=raw.reason)


@router.post("/grade", response_model=GradeResponse)
async def grade_essay(req: GradeRequest):
    """同步评分：提交作文，等待最终结果。"""
    state = EssayState(topic=req.topic, essay=req.sample_essay)
    result = await asyncio.to_thread(grade_essay_sync, state)
    return GradeResponse(
        topic=result["topic"],
        essay=result["essay"],
        relevance=_to_score_detail(result["relevance"]),
        evidence=_to_score_detail(result["evidence"]),
        structure=_to_score_detail(result["structure"]),
        expression=_to_score_detail(result["expression"]),
        final_score=result["final_score"],
    )


@router.post("/grade/stream")
async def grade_essay_stream_endpoint(req: GradeRequest):
    """流式评分：提交作文，实时接收各节点评分进度。"""
    state = EssayState(topic=req.topic, essay=req.sample_essay)

    async def event_generator():
        async for event in grade_essay_stream(state):
            for node_name, update in event.items():
                yield format_sse_event(node_name, update)
        yield format_sse_done()

    return EventSourceResponse(event_generator())


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}
