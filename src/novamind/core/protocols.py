"""模块契约（Protocol）。每个 AI 功能模块都先定义接口，再提供可注入的
生产实现与离线兜底实现，从而满足「单一职责 + 可独立验证 + 可协同」。

作者：晨星
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from novamind.core.models import (
    AgentResult,
    Chunk,
    Document,
    EvalCase,
    EvalMetrics,
    Hit,
    Message,
)


@runtime_checkable
class Embedder(Protocol):
    """文本 -> 向量。"""

    dim: int

    async def embed(self, texts: list[str]) -> list[list[float]]: ...


@runtime_checkable
class VectorStore(Protocol):
    """向量存储与相似检索。"""

    async def upsert(self, chunks: list[Chunk], vectors: list[list[float]]) -> None: ...

    async def search(self, vector: list[float], top_k: int) -> list[Hit]: ...

    async def count(self) -> int: ...

    async def reset(self) -> None: ...


@runtime_checkable
class Retriever(Protocol):
    """多路检索并融合。"""

    async def retrieve(self, query: str, top_k: int) -> list[Hit]: ...


@runtime_checkable
class Reranker(Protocol):
    """对候选集精排。"""

    async def rerank(self, query: str, hits: list[Hit], top_k: int) -> list[Hit]: ...


@runtime_checkable
class LLM(Protocol):
    """对话生成。"""

    async def chat(self, messages: list[Message], *, temperature: float = 0.2) -> str: ...


@runtime_checkable
class Agent(Protocol):
    """多步编排，返回答案与证据。"""

    async def run(self, query: str) -> AgentResult: ...


@runtime_checkable
class Evaluator(Protocol):
    """基于黄金集评测系统。"""

    async def evaluate(self, case: EvalCase) -> EvalMetrics: ...


@runtime_checkable
class Tracer(Protocol):
    """轻量链路追踪。"""

    def span(self, name: str) -> "Span": ...


class Span:
    """上下文管理器式 span，记录耗时与状态。"""

    name: str

    def __enter__(self) -> "Span":
        return self

    def __exit__(self, *exc: object) -> None:
        return None
