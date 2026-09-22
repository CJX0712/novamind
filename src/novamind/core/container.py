"""依赖装配：依据 Settings 选择各模块的生产/兜底实现并组合成完整系统。

这是「协议 + 注入实现」落地的核心——新增后端只需在此注册，不改业务代码。

作者：晨星
"""
from __future__ import annotations

from dataclasses import dataclass

from novamind.core.config import Settings
from novamind.core.errors import ConfigError
from novamind.core.models import Document
from novamind.agent.orchestrator import AgentOrchestrator
from novamind.embed.hash_embed import HashEmbedder
from novamind.embed.ollama import OllamaEmbedder
from novamind.eval.metrics import RAGEvaluator
from novamind.ingest.chunker import Chunker
from novamind.llm.mock import MockLLM
from novamind.llm.ollama import OllamaLLM
from novamind.observ.tracer import Tracer
from novamind.retrieve.bm25 import BM25Index
from novamind.retrieve.fusion import HybridRetriever
from novamind.rerank.heuristic import HeuristicReranker
from novamind.rerank.onnx_rerank import OnnxReranker
from novamind.vector.memory_store import MemoryVectorStore
from novamind.vector.qdrant_store import QdrantVectorStore


@dataclass
class System:
    """组合后的完整 AI 系统，持有全部模块引用与便捷方法。"""

    settings: Settings
    embedder: object
    vector: object
    reranker: object
    llm: object
    bm25: BM25Index
    retriever: HybridRetriever
    agent: AgentOrchestrator
    evaluator: RAGEvaluator
    tracer: Tracer

    async def ingest(self, docs: list[Document]) -> int:
        """接入文档：分块 → 嵌入 → 入库 → 建 BM25 索引。"""
        chunker = Chunker(self.settings.chunk_size, self.settings.chunk_overlap)
        chunks = [c for d in docs for c in chunker.chunk(d)]
        if not chunks:
            return 0
        vectors = await self.embedder.embed([c.text for c in chunks])
        await self.vector.upsert(chunks, vectors)
        await self.retriever.index(chunks)
        return len(chunks)

    async def answer(self, query: str):
        return await self.agent.run(query)


def build_system(settings: Settings | None = None) -> System:
    settings = settings or Settings.from_env()

    # 嵌入
    if settings.embed_backend == "ollama":
        embedder: object = OllamaEmbedder(settings.ollama_base_url, settings.embed_model)
    elif settings.embed_backend == "hash":
        embedder = HashEmbedder()
    else:
        raise ConfigError(f"未知 embed_backend: {settings.embed_backend}")

    # 向量库
    if settings.vector_backend == "qdrant":
        vector: object = QdrantVectorStore()
    elif settings.vector_backend == "memory":
        vector = MemoryVectorStore()
    else:
        raise ConfigError(f"未知 vector_backend: {settings.vector_backend}")

    # 重排
    if settings.rerank_backend == "onnx":
        reranker = OnnxReranker(
            model_path="models/reranker.onnx", tokenizer_path="models/tokenizer.json"
        )
    elif settings.rerank_backend == "heuristic":
        reranker = HeuristicReranker()
    else:
        raise ConfigError(f"未知 rerank_backend: {settings.rerank_backend}")

    # LLM
    if settings.llm_backend == "ollama":
        llm: object = OllamaLLM(settings.ollama_base_url, settings.llm_model)
    elif settings.llm_backend == "mock":
        llm = MockLLM()
    else:
        raise ConfigError(f"未知 llm_backend: {settings.llm_backend}")

    bm25 = BM25Index()
    retriever = HybridRetriever(embedder, vector, bm25, top_k=settings.top_k)
    agent = AgentOrchestrator(
        retriever, reranker, llm, top_k=settings.top_k, rerank_top_k=settings.rerank_top_k
    )
    evaluator = RAGEvaluator(retriever, reranker, agent)
    tracer = Tracer()
    return System(
        settings=settings,
        embedder=embedder,
        vector=vector,
        reranker=reranker,
        llm=llm,
        bm25=bm25,
        retriever=retriever,
        agent=agent,
        evaluator=evaluator,
        tracer=tracer,
    )
