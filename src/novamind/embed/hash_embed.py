"""离线嵌入兜底：确定性哈希向量。中文走字 + 双字，英文走词，L2 归一化。

这是「干净环境零依赖可复现」的支点——不依赖任何模型即可让检索/向量库跑通。

作者：晨星
"""
from __future__ import annotations

import hashlib
import math
import re

_CJK = re.compile(r"[\u4e00-\u9fff]")
_WORD = re.compile(r"[a-z0-9]+")


class HashEmbedder:
    """确定性哈希嵌入器，dim 固定，结果与平台/时间无关。"""

    def __init__(self, dim: int = 256) -> None:
        self.dim = dim

    def _tokens(self, text: str) -> list[str]:
        text = text.lower()
        tokens: list[str] = []
        # 中文：单字与相邻双字
        chars = [c for c in text if _CJK.match(c)]
        tokens.extend(chars)
        for i in range(len(chars) - 1):
            tokens.append(chars[i] + chars[i + 1])
        # 英文/数字：词
        tokens.extend(_WORD.findall(text))
        return tokens

    def _vec(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for tok in self._tokens(text):
            h = int.from_bytes(
                hashlib.sha1(tok.encode("utf-8")).digest()[:4], "little"
            )
            vec[h % self.dim] += 1.0
        norm = math.sqrt(sum(v * v for v in vec))
        if norm == 0.0:
            return vec
        return [v / norm for v in vec]

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vec(t) for t in texts]

    async def embed_one(self, text: str) -> list[float]:
        return self._vec(text)
