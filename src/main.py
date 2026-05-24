"""FastAPI 应用入口"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from src.routers.grading import router as grading_router

app = FastAPI(title="高考作文评分系统", version="0.1.0")

app.include_router(grading_router)

_STATIC_DIR = Path(__file__).resolve().parent / "static"


@app.get("/", summary="主页")
async def index():
    """返回前端页面。"""
    return FileResponse(_STATIC_DIR / "index.html")
