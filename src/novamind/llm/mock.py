"""离线 LLM 兜底：基于注入上下文的确定性合成回答。

用于无模型环境下的端到端自检与评测——回答必定可由上下文支撑（faithful），
使离线链路在「无 Key、无网络、无模型」下也能跑通并被评测。

作者：晨星
"""
from __future__ import annotations

import re

from novamind.core.models import Message

_SENT = re.compile(r"[^。！？!?]+[。！？!?]?")


class MockLLM:
    """确定性模拟 LLM：从用户消息中的 Context 段提取要点作答。"""

    async def chat(self, messages: list[Message], *, temperature: float = 0.2) -> str:
        last = messages[-1].content if messages else ""
        return self._synthesize(last)

    @staticmethod
    def _synthesize(text: str) -> str:
        # 优先取 Context 标记之后的内容
        m = re.search(r"Context:\s*(.*?)\n\nQuestion:", text, re.S)
        corpus = m.group(1) if m else text
        sentences = [s.strip() for s in _SENT.findall(corpus) if s.strip()]
        if not sentences:
            return "（离线模拟）未在资料中找到相关依据。"
        head = "。".join(sentences[:2]).rstrip("。") + "。"
        return f"（离线模拟回答）依据资料：{head}"
