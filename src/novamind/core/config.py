"""运行配置。所有外部后端（LLM/嵌入/向量/重排）均通过环境变量切换，
默认走离线兜底实现，保证干净环境零依赖可运行。

作者：晨星
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """系统运行配置。backend 取值：ollama / mock / qdrant / memory / onnx / heuristic。"""

    llm_backend: str = "mock"
    embed_backend: str = "hash"
    vector_backend: str = "memory"
    rerank_backend: str = "heuristic"
    ollama_base_url: str = "http://127.0.0.1:11434"
    llm_model: str = "qwen2.5:3b"
    embed_model: str = "nomic-embed-text"
    rerank_model: str = "BAAI/bge-reranker-v2-m3"
    top_k: int = 8
    rerank_top_k: int = 4
    chunk_size: int = 500
    chunk_overlap: int = 80
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "Settings":
        """从环境变量读取；未设置时保留离线兜底默认值。"""
        return cls(
            llm_backend=os.getenv("NM_LLM", "mock"),
            embed_backend=os.getenv("NM_EMBED", "hash"),
            vector_backend=os.getenv("NM_VECTOR", "memory"),
            rerank_backend=os.getenv("NM_RERANK", "heuristic"),
            ollama_base_url=os.getenv("NM_OLLAMA_URL", "http://127.0.0.1:11434"),
            llm_model=os.getenv("NM_LLM_MODEL", "qwen2.5:3b"),
            embed_model=os.getenv("NM_EMBED_MODEL", "nomic-embed-text"),
            rerank_model=os.getenv("NM_RERANK_MODEL", "BAAI/bge-reranker-v2-m3"),
            top_k=int(os.getenv("NM_TOP_K", "8")),
            rerank_top_k=int(os.getenv("NM_RERANK_TOP_K", "4")),
            chunk_size=int(os.getenv("NM_CHUNK_SIZE", "500")),
            chunk_overlap=int(os.getenv("NM_CHUNK_OVERLAP", "80")),
            log_level=os.getenv("NM_LOG", "INFO"),
        )
