"""轻量链路追踪：记录 span 耗时，供可观测与调试。

作者：晨星
"""
from __future__ import annotations

import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("novamind")


class Tracer:
    """记录各阶段耗时，支持上下文管理器式 span。"""

    def __init__(self) -> None:
        self.spans: list[tuple[str, float]] = []

    def span(self, name: str) -> "Span":
        return Span(self, name)


class Span:
    def __init__(self, tracer: Tracer, name: str) -> None:
        self._tracer = tracer
        self.name = name
        self._start = 0.0

    def __enter__(self) -> "Span":
        self._start = time.time()
        logger.info("span start: %s", self.name)
        return self

    def __exit__(self, *exc: object) -> None:
        dur = time.time() - self._start
        self._tracer.spans.append((self.name, dur))
        logger.info("span end: %s (%.3fs)", self.name, dur)
