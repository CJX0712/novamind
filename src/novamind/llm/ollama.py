"""生产 LLM 实现：调用 Ollama /api/chat（HTTP，免编译）。

作者：晨星
"""
from __future__ import annotations

import httpx

from novamind.core.errors import BackendUnavailable, GenerationError
from novamind.core.models import Message


class OllamaLLM:
    """通过 Ollama 本地服务进行对话生成。"""

    def __init__(self, base_url: str, model: str, timeout: float = 60.0) -> None:
        self._base = base_url.rstrip("/")
        self.model = model
        self._timeout = timeout

    async def chat(self, messages: list[Message], *, temperature: float = 0.2) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {"temperature": temperature},
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    f"{self._base}/api/chat", json=payload
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as exc:
            raise BackendUnavailable(
                f"Ollama 对话服务不可达 ({self._base}): {exc}"
            ) from exc
        try:
            return data["message"]["content"].strip()
        except (KeyError, TypeError) as exc:  # pragma: no cover
            raise GenerationError(f"Ollama 返回结构异常: {data}") from exc
