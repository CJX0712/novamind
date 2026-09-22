"""文档接入：从多种格式加载为统一 Document。

作者：晨星
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

from novamind.core.errors import IngestionError
from novamind.core.models import Document

_TAG_RE = re.compile(r"<[^>]+>")


def _read_bytes(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:  # pragma: no cover - 文件系统异常
        raise IngestionError(f"无法读取文件 {path}: {exc}") from exc


def _strip_html(html: str) -> str:
    text = _TAG_RE.sub(" ", html)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


class Loader:
    """多格式加载器：txt/md/html/pdf，并支持纯文本直接构造。"""

    @staticmethod
    def from_text(text: str, doc_id: str | None = None) -> Document:
        text = text.strip()
        if not text:
            raise IngestionError("空文档，无法接入")
        doc_id = doc_id or hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]
        return Document(id=doc_id, text=text, metadata={"source": "text"})

    @staticmethod
    def load(path: str | Path) -> Document:
        p = Path(path)
        if not p.exists():
            raise IngestionError(f"文件不存在: {p}")
        suffix = p.suffix.lower()
        raw = _read_bytes(p)
        if suffix in (".txt", ".md", ".text"):
            text = raw.decode("utf-8", errors="replace")
        elif suffix == ".html":
            text = _strip_html(raw.decode("utf-8", errors="replace"))
        elif suffix == ".pdf":
            text = _load_pdf(p)
        else:
            # 兜底按文本读取，保证可用性
            text = raw.decode("utf-8", errors="replace")
        text = text.strip()
        if not text:
            raise IngestionError(f"解析后为空: {p}")
        return Document(
            id=hashlib.sha1(str(p).encode("utf-8")).hexdigest()[:12],
            text=text,
            metadata={"source": str(p), "type": suffix.lstrip(".") or "text"},
        )


def _load_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover
        raise IngestionError("PDF 解析需要 pypdf，请先安装") from exc
    try:
        reader = PdfReader(str(path))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages).strip()
    except Exception as exc:  # pragma: no cover - 损坏 PDF
        raise IngestionError(f"PDF 解析失败 {path}: {exc}") from exc
