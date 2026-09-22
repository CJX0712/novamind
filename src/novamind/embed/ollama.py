"""生产嵌入实现：调用 Ollama /api/embed（HTTP，免编译）。

作者：晨星
"""
from __future__ import annotations

import httpx

from novamind.core.errors import BackendUnavailable


class OllamaEmbedder:
    """通过 Ollama 本地服务获取文本向量。"""

    def __init__(self, base_url: str, model: str, timeout: float = 30.0) -> None:
        self._base = base_url.rstrip("/")
        self.model = model
        self._timeout = timeout
        self.dim = 0  # 首次调用后填充

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    f"{self._base}/api/embed",
                    json={"model": self.model, "input": texts},
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as exc:
            raise BackendUnavailable(
                f"Ollama 嵌入服务不可达 ({self._base}): {exc}"
            ) from exc
        embeddings = data.get("embeddings")
        if not embeddings:
            raise BackendUnavailable("Ollama 返回空嵌入，请确认模型已拉取")
        if self.dim == 0:
            self.dim = len(embeddings[0])
        return [list(e) for e in embeddings]
