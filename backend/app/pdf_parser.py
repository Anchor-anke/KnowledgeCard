"""PDF text extraction for the local AI summary prototype."""

from __future__ import annotations

import os
from io import BytesIO

from pypdf import PdfReader


class PDFExtractionError(ValueError):
    """Raised when a PDF cannot provide usable text."""


def max_pdf_bytes() -> int:
    try:
        return max(int(os.getenv("MAX_PDF_BYTES", 10 * 1024 * 1024)), 1024)
    except (TypeError, ValueError):
        return 10 * 1024 * 1024


def extract_pdf_text(content: bytes) -> str:
    if not content:
        raise PDFExtractionError("PDF 文件为空")
    if len(content) > max_pdf_bytes():
        raise PDFExtractionError("PDF 文件超过本地测试大小限制")

    try:
        reader = PdfReader(BytesIO(content))
        pages = []
        for index, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if text:
                pages.append(f"[第 {index} 页]\n{text}")
    except Exception as exc:
        raise PDFExtractionError("PDF 无法读取，请确认文件未损坏") from exc

    if not pages:
        raise PDFExtractionError("PDF 没有可提取的文字，目前不支持扫描版 PDF")
    return "\n\n".join(pages)
