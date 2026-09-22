"""离线向量库兜底：进程内余弦相似度检索。零依赖，保证可复现。

作者：晨星
"""
from __future__ import annotations

from novamind.core.models import Chunk, Hit


def _cosine(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


class MemoryVectorStore:
    """内存向量库：保存分块与向量，按余弦相似度检索。"""

    def __init__(self) -> None:
        self._chunks: dict[str, Chunk] = {}
        self._vecs: dict[str, list[float]] = {}

    async def upsert(self, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("chunks 与 vectors 数量不一致")
        for c, v in zip(chunks, vectors):
            self._chunks[c.id] = c
            self._vecs[c.id] = v

    async def search(self, vector: list[float], top_k: int) -> list[Hit]:
        scored = [
            (cid, _cosine(vector, vec)) for cid, vec in self._vecs.items()
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        hits: list[Hit] = []
        for cid, score in scored[:top_k]:
            c = self._chunks[cid]
            hits.append(
                Hit(
                    chunk_id=cid,
                    doc_id=c.doc_id,
                    text=c.text,
                    score=round(score, 6),
                    metadata=c.metadata,
                )
            )
        return hits

    async def get_chunks(self) -> list[Chunk]:
        return list(self._chunks.values())

    async def count(self) -> int:
        return len(self._chunks)

    async def reset(self) -> None:
        self._chunks.clear()
        self._vecs.clear()
