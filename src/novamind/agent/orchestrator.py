"""智能体编排：检索 → 重排 → 工具路由 → 生成，输出带证据的答案。

作者：晨星
"""
from __future__ import annotations

import re

from novamind.core.models import AgentResult, AgentStep, Hit, Message
from novamind.agent.tools import ToolRegistry

_MATH_HINT = re.compile(r"计算|算一下|[0-9]+\s*[\*\+\-/]\s*[0-9]+|=")


class AgentOrchestrator:
    """RAG 智能体：先尝试工具，再走检索增强生成。"""

    def __init__(self, retriever, reranker, llm, top_k: int = 8, rerank_top_k: int = 4) -> None:
        self.retriever = retriever
        self.reranker = reranker
        self.llm = llm
        self.top_k = top_k
        self.rerank_top_k = rerank_top_k
        self.tools = ToolRegistry()

    async def run(self, query: str) -> AgentResult:
        steps: list[AgentStep] = []

        # 1) 工具路由：简单四则运算直接走计算器
        if _MATH_HINT.search(query):
            steps.append(AgentStep(action="route", detail="命中计算意图", tool="calculator"))
            answer = self.tools.call("calculator", query)
            steps.append(AgentStep(action="tool_call", detail=answer, tool="calculator"))
            return AgentResult(answer=f"计算结果为：{answer}", steps=steps, sources=[])

        # 2) 检索
        hits = await self.retriever.retrieve(query, top_k=self.top_k)
        steps.append(AgentStep(action="retrieve", detail=f"召回 {len(hits)} 个候选"))
        if not hits:
            return AgentResult(answer="未在资料中找到相关内容。", steps=steps, sources=[])

        # 3) 重排
        reranked = await self.reranker.rerank(query, hits, top_k=self.rerank_top_k)
        steps.append(AgentStep(action="rerank", detail=f"精排保留 {len(reranked)} 个"))
        context = "\n\n".join(f"[{i + 1}] {h.text}" for i, h in enumerate(reranked))

        # 4) 生成
        messages = [
            Message(
                role="system",
                content="你是严谨的助手，仅依据所给资料作答，不编造资料外内容。",
            ),
            Message(
                role="user",
                content=f"Context:\n{context}\n\nQuestion: {query}\n\n请基于 Context 作答。",
            ),
        ]
        answer = await self.llm.chat(messages)
        steps.append(AgentStep(action="generate", detail="已生成回答"))
        return AgentResult(answer=answer, steps=steps, sources=reranked)
