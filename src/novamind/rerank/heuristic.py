"""离线重排兜底：以「查询词与候选文本的词重叠」作为精排信号，结合召回分数。

零依赖，保证评测/自检在无模型环境下可运行。

作者：晨星
"""
from __future__ import annotations

from novamind.core.models import Hit
from novamind.retrieve.bm25 import tokenize


class HeuristicReranker:
    """基于词重叠的启发式重排器。"""

    async def rerank(self, query: str, hits: list[Hit], top_k: int = 4) -> list[Hit]:
        q_tokens = set(tokenize(query))
        scored: list[tuple[Hit, float]] = []
        for h in hits:
            t_tokens = set(tokenize(h.text))
            overlap = len(q_tokens & t_tokens)
            # 词重叠作为微调信号，主排序仍尊重召回分数
            combined = h.score + overlap * 0.01
            scored.append((h, combined))
        scored.sort(key=lambda x: x[1], reverse=True)
        out: list[Hit] = []
        for h, s in scored[:top_k]:
            h.score = round(s, 6)
            out.append(h)
        return out
