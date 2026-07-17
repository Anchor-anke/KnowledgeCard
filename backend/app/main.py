"""FastAPI entry point for the local KnowledgeCard AI summary backend."""

from __future__ import annotations

import os
from typing import Optional

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover - requirements install python-dotenv
    pass

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .ai_client import AISettings, OpenAICompatibleAIClient
from .jobs import SummaryJobService
from .pdf_parser import PDFExtractionError, extract_pdf_text


class TextSummaryRequest(BaseModel):
    title: str = "未命名资料"
    text: str


def _max_input_chars() -> int:
    return AISettings.from_env().max_input_chars


def _allowed_origins():
    raw = os.getenv("CORS_ALLOW_ORIGINS", "*")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


app = FastAPI(
    title="KnowledgeCard AI Summary Backend",
    version="0.1.0",
    description="Local prototype for text/PDF summarization and user-reviewable card drafts.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

job_service = SummaryJobService(OpenAICompatibleAIClient())


@app.get("/health")
def health():
    client = job_service.ai_client
    settings = getattr(client, "settings", None)
    return {
        "status": "ok",
        "service": "knowledgecard-ai-summary",
        "ai_configured": bool(getattr(client, "configured", False)),
        "ai_model": getattr(settings, "model", None),
        "ai_base_url": getattr(settings, "base_url", None),
    }


@app.post("/api/v1/summaries/text", status_code=status.HTTP_202_ACCEPTED)
def create_text_summary(
    request: TextSummaryRequest,
    background_tasks: BackgroundTasks,
):
    text = request.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="text 不能为空")
    if len(text) > _max_input_chars():
        raise HTTPException(
            status_code=413,
            detail=f"text 超过本地测试限制（最多 {_max_input_chars()} 个字符）",
        )
    return job_service.create_task(
        title=request.title,
        source_type="text",
        source_name=None,
        text=text,
        background_tasks=background_tasks,
    ).public()


@app.post("/api/v1/summaries/pdf", status_code=status.HTTP_202_ACCEPTED)
async def create_pdf_summary(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(""),
):
    filename = file.filename or "document.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="当前只支持 PDF 文件")

    try:
        content = await file.read()
        text = extract_pdf_text(content)
    except PDFExtractionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        await file.close()

    if len(text) > _max_input_chars():
        raise HTTPException(
            status_code=413,
            detail=f"PDF 提取文字超过本地测试限制（最多 {_max_input_chars()} 个字符）",
        )
    return job_service.create_task(
        title=title or filename,
        source_type="pdf",
        source_name=filename,
        text=text,
        background_tasks=background_tasks,
    ).public()


@app.get("/api/v1/summaries/{task_id}")
def get_summary(task_id: str):
    task = job_service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="总结任务不存在")
    return task.public()


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=True,
    )
