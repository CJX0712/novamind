"""API 数据契约（Pydantic）。

作者：晨星
"""
from __future__ import annotations

from pydantic import BaseModel


class IngestRequest(BaseModel):
    text: str
    doc_id: str | None = None


class AskRequest(BaseModel):
    query: str
    top_k: int | None = None


class SearchRequest(BaseModel):
    query: str
    top_k: int = 8


class SourceOut(BaseModel):
    chunk_id: str
    doc_id: str
    text: str
    score: float


class StepOut(BaseModel):
    action: str
    detail: str
    tool: str | None = None


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceOut]
    steps: list[StepOut]


class HealthOut(BaseModel):
    status: str
    backends: dict[str, str]
