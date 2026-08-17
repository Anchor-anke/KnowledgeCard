"""FastAPI entry point for the local KnowledgeCard AI summary backend."""

from __future__ import annotations

import hashlib
import hmac
import os
from typing import Optional

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover - requirements install python-dotenv
    pass

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    Form,
    Header,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .ai_client import AISettings, OpenAICompatibleAIClient
from .jobs import SummaryJobService
from .pdf_parser import PDFExtractionError, extract_pdf_text, max_pdf_bytes


class TextSummaryRequest(BaseModel):
    title: str = "未命名资料"
    text: str


def _max_input_chars() -> int:
    return AISettings.from_env().max_input_chars


def _allowed_origins():
    raw = os.getenv(
        "CORS_ALLOW_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,null",
    )
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def _allow_insecure_dev_identity() -> bool:
    return os.getenv("ALLOW_INSECURE_DEV_IDENTITY", "true").strip().lower() in {
        "1",
        "true",
        "yes",
    }


def current_user_id(
    x_user_id: Optional[str] = Header(default=None, alias="X-User-ID"),
    x_user_signature: Optional[str] = Header(default=None, alias="X-User-Signature"),
) -> str:
    """Resolve the authenticated user supplied by the identity gateway.

    Local development can use an unsigned X-User-ID. Deployments must set
    USER_ID_SIGNING_SECRET so clients cannot choose another user's identity.
    """
    user_id = (x_user_id or "").strip()
    if not user_id or len(user_id) > 128:
        raise HTTPException(status_code=401, detail="缺少有效的用户身份")

    signing_secret = os.getenv("USER_ID_SIGNING_SECRET", "").strip()
    if signing_secret:
        expected = hmac.new(
            signing_secret.encode("utf-8"),
            user_id.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        if not x_user_signature or not hmac.compare_digest(x_user_signature, expected):
            raise HTTPException(status_code=401, detail="用户身份签名无效")
    elif not _allow_insecure_dev_identity():
        raise HTTPException(status_code=503, detail="服务尚未配置用户身份验证")
    return user_id


async def _read_upload_limited(file: UploadFile, limit: int) -> bytes:
    """Read at most limit bytes, avoiding an unbounded upload read."""
    chunks = bytearray()
    remaining = limit + 1
    while remaining > 0:
        chunk = await file.read(min(1024 * 1024, remaining))
        if not chunk:
            break
        chunks.extend(chunk)
        remaining -= len(chunk)
        if len(chunks) > limit:
            raise HTTPException(status_code=413, detail="PDF 文件超过本地测试大小限制")
    return bytes(chunks)


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
    user_id: str = Depends(current_user_id),
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
        owner_id=user_id,
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
    user_id: str = Depends(current_user_id),
):
    filename = file.filename or "document.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="当前只支持 PDF 文件")

    try:
        content = await _read_upload_limited(file, max_pdf_bytes())
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
        owner_id=user_id,
        title=title or filename,
        source_type="pdf",
        source_name=filename,
        text=text,
        background_tasks=background_tasks,
    ).public()


@app.get("/api/v1/summaries/{task_id}")
def get_summary(task_id: str, user_id: str = Depends(current_user_id)):
    task = job_service.get_task(task_id, owner_id=user_id)
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
