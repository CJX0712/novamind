"""混合检索：稠密向量 + BM25 关键词，经 RRF 倒数排名融合。

作者：晨星
"""
from __future__ import annotations

from novamind.core.models import Chunk, Hit
from novamind.retrieve.bm25 import BM25Index


def reciprocal_rank_fusion(
    lists: list[list[Hit]], k: int = 60
) -> list[Hit]:
    """对多路召回结果做 RRF 融合。key 用 chunk_id 去重。"""
    fused: dict[str, Hit] = {}
    scores: dict[str, float] = {}
    for hits in lists:
        for rank, h in enumerate(hits):
            s = 1.0 / (k + rank + 1)
            if h.chunk_id in fused:
                scores[h.chunk_id] += s
            else:
                fused[h.chunk_id] = h
                scores[h.chunk_id] = s
    ordered = sorted(fused.values(), key=lambda h: scores[h.chunk_id], reverse=True)
    for h in ordered:
        h.score = round(scores[h.chunk_id], 6)
    return ordered


class HybridRetriever:
    """组合 Embedder + VectorStore（稠密）与 BM25（关键词）。"""

    def __init__(
        self,
        embedder,
        vector_store,
        bm25: BM25Index,
        top_k: int = 8,
        dense_top_k: int = 16,
    ) -> None:
        self.embedder = embedder
        self.store = vector_store
        self.bm25 = bm25
        self.top_k = top_k
        self.dense_top_k = dense_top_k

    async def index(self, chunks: list[Chunk]) -> None:
        self.bm25.build(chunks)

    async def retrieve(self, query: str, top_k: int | None = None) -> list[Hit]:
        top_k = top_k or self.top_k
        vec = (await self.embedder.embed([query]))[0]
        dense = await self.store.search(vec, self.dense_top_k)
        lexical = self.bm25.search(query, self.dense_top_k)
        fused = reciprocal_rank_fusion([dense, lexical])
        return fused[:top_k]
