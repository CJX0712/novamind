"""生产向量库：Qdrant 本地模式（无需独立服务进程，零外部依赖）。

作者：晨星
"""
from __future__ import annotations

from novamind.core.errors import BackendUnavailable
from novamind.core.models import Chunk, Hit

_COLLECTION = "novamind"


class QdrantVectorStore:
    """基于 Qdrant 本地（内存/磁盘）模式的向量库。"""

    def __init__(self, path: str = ":memory:") -> None:
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
        except ImportError as exc:  # pragma: no cover
            raise BackendUnavailable("Qdrant 后端需要 qdrant-client") from exc
        self._client = QdrantClient(path=path)
        self._VectorParams = VectorParams
        self._Distance = Distance
        self._dim: int | None = None

    def _ensure(self, dim: int) -> None:
        if self._dim == dim and self._client.collection_exists(_COLLECTION):
            return
        if self._client.collection_exists(_COLLECTION):
            self._client.delete_collection(_COLLECTION)
        self._client.create_collection(
            _COLLECTION,
            vectors_config=self._VectorParams(
                size=dim, distance=self._Distance.COSINE
            ),
        )
        self._dim = dim

    async def upsert(self, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        if not chunks:
            return
        self._ensure(len(vectors[0]))
        # 用稳定 id：以 chunk 哈希避免重复 upsert 产生重复
        from qdrant_client.models import PointStruct

        pts = [
            PointStruct(
                id=abs(hash(c.id)) % (2**63),
                vector=vectors[i],
                payload={
                    "chunk_id": c.id,
                    "doc_id": c.doc_id,
                    "text": c.text,
                    "metadata": c.metadata,
                },
            )
            for i, c in enumerate(chunks)
        ]
        self._client.upsert(_COLLECTION, pts)

    async def search(self, vector: list[float], top_k: int) -> list[Hit]:
        res = self._client.search(
            _COLLECTION, query_vector=vector, limit=top_k
        )
        hits: list[Hit] = []
        for r in res:
            p = r.payload or {}
            hits.append(
                Hit(
                    chunk_id=p.get("chunk_id", ""),
                    doc_id=p.get("doc_id", ""),
                    text=p.get("text", ""),
                    score=round(float(r.score), 6),
                    metadata=p.get("metadata", {}),
                )
            )
        return hits

    async def get_chunks(self) -> list[Chunk]:
        out: list[Chunk] = []
        offset = None
        while True:
            recs, offset = self._client.scroll(
                _COLLECTION, limit=256, offset=offset
            )
            for r in recs:
                p = r.payload or {}
                out.append(
                    Chunk(
                        id=p.get("chunk_id", ""),
                        doc_id=p.get("doc_id", ""),
                        text=p.get("text", ""),
                        index=0,
                        metadata=p.get("metadata", {}),
                    )
                )
            if offset is None:
                break
        return out

    async def count(self) -> int:
        return self._client.count(_COLLECTION).count

    async def reset(self) -> None:
        if self._client.collection_exists(_COLLECTION):
            self._client.delete_collection(_COLLECTION)
        self._dim = None
