"""文档分块：按字符窗口滑动切分，保留重叠区以保留上下文。

作者：晨星
"""
from __future__ import annotations

from novamind.core.errors import IngestionError
from novamind.core.models import Chunk, Document


class Chunker:
    """定长滑动窗口分块器。中文按字符计数（CJK 无空格分词）。"""

    def __init__(self, chunk_size: int = 500, overlap: int = 80) -> None:
        if chunk_size <= overlap:
            raise IngestionError("chunk_size 必须大于 overlap")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, doc: Document) -> list[Chunk]:
        text = doc.text
        if len(text) <= self.chunk_size:
            return [
                Chunk(
                    id=f"{doc.id}-0",
                    doc_id=doc.id,
                    text=text,
                    index=0,
                    metadata=doc.metadata,
                )
            ]
        step = self.chunk_size - self.overlap
        out: list[Chunk] = []
        idx = 0
        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            piece = text[start:end]
            out.append(
                Chunk(
                    id=f"{doc.id}-{idx}",
                    doc_id=doc.id,
                    text=piece,
                    index=idx,
                    metadata=doc.metadata,
                )
            )
            idx += 1
            if end == len(text):
                break
            start += step
        return out
