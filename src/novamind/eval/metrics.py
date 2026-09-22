"""RAG 评测：上下文召回/精准、回答忠实度。基于黄金集离线可跑。

作者：晨星
"""
from __future__ import annotations

from novamind.core.models import AgentResult, EvalCase, EvalMetrics, Hit
from novamind.retrieve.bm25 import tokenize


class RAGEvaluator:
    """对单条黄金样本评测检索与生成质量。"""

    def __init__(self, retriever, reranker, agent, top_k: int = 10, rerank_top_k: int = 5) -> None:
        self.retriever = retriever
        self.reranker = reranker
        self.agent = agent
        self.top_k = top_k
        self.rerank_top_k = rerank_top_k

    async def evaluate(self, case: EvalCase) -> EvalMetrics:
        hits = await self.retriever.retrieve(case.query, top_k=self.top_k)
        reranked = await self.reranker.rerank(case.query, hits, top_k=self.rerank_top_k)

        rel = set(case.relevant_doc_ids)
        recall_hits = [h for h in hits if h.doc_id in rel]
        ctx_recall = len(recall_hits) / max(1, len(rel))
        rel_in_rerank = [h for h in reranked if h.doc_id in rel]
        ctx_precision = len(rel_in_rerank) / max(1, len(reranked))

        result = await self.agent.run(case.query)
        faith = self._faithfulness(result, reranked)
        answered = bool(result.answer.strip())
        notes = "" if answered else "答案空"
        return EvalMetrics(
            context_recall=round(ctx_recall, 4),
            context_precision=round(ctx_precision, 4),
            faithfulness=round(faith, 4),
            answered=answered,
            notes=notes,
        )

    @staticmethod
    def _faithfulness(result: AgentResult, sources: list[Hit]) -> float:
        answer_tokens = set(tokenize(result.answer))
        answer_tokens.discard("")
        if not answer_tokens:
            return 0.0
        corpus = " ".join(h.text for h in sources)
        src_tokens = set(tokenize(corpus))
        overlap = answer_tokens & src_tokens
        return len(overlap) / len(answer_tokens)
