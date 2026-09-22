"""BM25  lexical 检索（关键词召回）。中文走字+双字，英文走词。

作者：晨星
"""
from __future__ import annotations

import math
import re

from novamind.core.models import Chunk, Hit

_CJK = re.compile(r"[\u4e00-\u9fff]")
_WORD = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    text = text.lower()
    toks: list[str] = []
    chars = [c for c in text if _CJK.match(c)]
    toks.extend(chars)
    for i in range(len(chars) - 1):
        toks.append(chars[i] + chars[i + 1])
    toks.extend(_WORD.findall(text))
    return toks


class BM25Index:
    """Okapi BM25 索引，进程内，零依赖。"""

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self._chunks: list[Chunk] = []
        self._tf: list[dict[str, int]] = []
        self._df: dict[str, int] = {}
        self._idf: dict[str, float] = {}
        self._avgdl = 0.0
        self._ready = False

    def build(self, chunks: list[Chunk]) -> None:
        self._chunks = chunks
        self._tf = []
        lengths = []
        self._df = {}
        for c in chunks:
            toks = tokenize(c.text)
            lengths.append(len(toks))
            freq: dict[str, int] = {}
            for t in toks:
                freq[t] = freq.get(t, 0) + 1
            self._tf.append(freq)
            for t in freq:
                self._df[t] = self._df.get(t, 0) + 1
        n = len(chunks) or 1
        self._avgdl = (sum(lengths) / n) if chunks else 0.0
        for t, d in self._df.items():
            self._idf[t] = math.log(1 + (n - d + 0.5) / (d + 0.5))
        self._ready = True

    def search(self, query: str, top_k: int = 8) -> list[Hit]:
        if not self._ready or not self._chunks:
            return []
        q_toks = tokenize(query)
        scores: list[float] = []
        for i, freq in enumerate(self._tf):
            dl = sum(freq.values())
            score = 0.0
            for t in set(q_toks):
                if t not in freq:
                    continue
                idf = self._idf.get(t, 0.0)
                tf = freq[t]
                denom = tf + self.k1 * (1 - self.b + self.b * dl / (self._avgdl or 1))
                score += idf * (tf * (self.k1 + 1)) / denom
            scores.append(score)
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        hits: list[Hit] = []
        for i in ranked[:top_k]:
            c = self._chunks[i]
            hits.append(
                Hit(
                    chunk_id=c.id,
                    doc_id=c.doc_id,
                    text=c.text,
                    score=round(scores[i], 6),
                    metadata=c.metadata,
                )
            )
        return hits
