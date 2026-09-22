"""NovaMind 离线单测：全程 mock/hash/memory/heuristic，无 Key、无网、无模型。

作者：晨星
"""
from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient

from novamind.core.config import Settings
from novamind.core.container import build_system
from novamind.core.models import Document
from novamind.embed.hash_embed import HashEmbedder
from novamind.eval.golden import CORPUS, GOLDEN_CASES
from novamind.ingest.chunker import Chunker
from novamind.retrieve.bm25 import BM25Index


def test_chunker_splits_long_text():
    doc = Document(id="d1", text="人工智能" * 400)
    chunks = Chunker(chunk_size=200, overlap=40).chunk(doc)
    assert len(chunks) > 1
    assert all(c.doc_id == "d1" for c in chunks)


def test_hash_embed_deterministic_and_distinct():
    emb = HashEmbedder(dim=128)
    a = asyncio.run(emb.embed(["晨星 构建 AI 系统"]))
    b = asyncio.run(emb.embed(["晨星 构建 AI 系统"]))
    assert a[0] == b[0]
    c = asyncio.run(emb.embed(["完全不相关的其他内容"]))
    assert a[0] != c[0]
    assert len(a[0]) == 128


def test_memory_store_search_ranks():
    from novamind.vector.memory_store import MemoryVectorStore

    store = MemoryVectorStore()
    emb = HashEmbedder(dim=64)
    docs = [
        Document(id="x", text="苹果是一种水果"),
        Document(id="y", text="显卡用于深度学习训练"),
    ]
    chunks = [c for d in docs for c in Chunker(1000, 0).chunk(d)]
    vecs = asyncio.run(emb.embed([c.text for c in chunks]))
    asyncio.run(store.upsert(chunks, vecs))
    q = asyncio.run(emb.embed_one("深度学习 显卡"))
    hits = asyncio.run(store.search(q, top_k=2))
    assert hits and hits[0].doc_id == "y"


def test_bm25_lexical_recall():
    idx = BM25Index()
    docs = [
        Document(id="a", text="Ollama 提供本地大模型推理能力"),
        Document(id="b", text="Docker 用于容器化部署"),
    ]
    chunks = [c for d in docs for c in Chunker(1000, 0).chunk(d)]
    idx.build(chunks)
    hits = idx.search("Ollama 本地推理", top_k=1)
    assert hits and hits[0].doc_id == "a"


def test_retriever_fusion_returns_hits():
    sys = build_system(Settings(embed_backend="hash", vector_backend="memory", rerank_backend="heuristic", llm_backend="mock"))
    asyncio.run(sys.ingest(CORPUS))
    hits = asyncio.run(sys.retriever.retrieve("NovaMind 模块", top_k=3))
    assert len(hits) >= 1


def test_agent_answers_with_sources():
    sys = build_system(Settings(embed_backend="hash", vector_backend="memory", rerank_backend="heuristic", llm_backend="mock"))
    asyncio.run(sys.ingest(CORPUS))
    res = asyncio.run(sys.agent.run("NovaMind 由哪些核心模块组成？"))
    assert res.answer
    assert any(s.chunk_id for s in res.sources)


def test_calculator_tool_routing():
    sys = build_system(Settings(embed_backend="hash", vector_backend="memory", rerank_backend="heuristic", llm_backend="mock"))
    res = asyncio.run(sys.agent.run("请帮我计算 12 * 8 + 3"))
    assert "99" in res.answer
    assert res.steps and res.steps[0].tool == "calculator"


def test_eval_metrics_reasonable():
    sys = build_system(Settings(embed_backend="hash", vector_backend="memory", rerank_backend="heuristic", llm_backend="mock"))
    asyncio.run(sys.ingest(CORPUS))
    for case in GOLDEN_CASES:
        m = asyncio.run(sys.evaluator.evaluate(case))
        assert m.context_recall >= 0.0
        assert m.answered is True
        assert m.faithfulness >= 0.0


def test_api_endpoints_offline():
    from novamind.api.app import create_app

    app = create_app(Settings(embed_backend="hash", vector_backend="memory", rerank_backend="heuristic", llm_backend="mock"))
    client = TestClient(app)
    h = client.get("/health")
    assert h.status_code == 200
    assert h.json()["status"] == "ok"
    ing = client.post("/ingest", json={"text": "NovaMind 支持本地优先的 AI 智能体编排。"})
    assert ing.status_code == 200 and ing.json()["ingested_chunks"] >= 1
    ask = client.post("/ask", json={"query": "NovaMind 是什么？"})
    assert ask.status_code == 200 and ask.json()["answer"]
    ev = client.post("/evaluate")
    assert ev.status_code == 200 and ev.json()["avg_context_recall"] >= 0.0
