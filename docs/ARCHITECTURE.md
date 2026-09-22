# NovaMind 系统架构

> 设计原则：**协议先行、实现可注入、离线可验证、生产可替换**。
> 每个 AI 功能模块先定义 `typing.Protocol` 接口，再提供至少两种实现（离线兜底 + 生产），由 `core/container.py` 按配置装配。

---

## 1. 分层总览

```
┌──────────────────────────────────────────────────────────────┐
│                         API 层 (FastAPI)                      │
│   /health  /ingest  /ask  /search  /evaluate   (api/)        │
└───────────────────────────┬──────────────────────────────────┘
                            │ 调用
┌───────────────────────────▼──────────────────────────────────┐
│                     Agent 编排层 (agent/)                     │
│   Orchestrator: retrieve → rerank → tool_route → generate    │
│   Tools: Calculator / Clock（可扩展 Tool 协议）               │
└───────┬───────────────┬───────────────┬──────────────────────┘
        │               │               │
┌───────▼──────┐ ┌──────▼───────┐ ┌─────▼────────┐
│ 检索层       │ │ 评测层        │ │ 观测层       │
│ retrieve/    │ │ eval/         │ │ observ/      │
│  HybridRetr. │ │  RAGEvaluator │ │  Tracer      │
│  BM25+Fusion │ │  Golden set   │ │              │
└───────┬──────┘ └──────────────┘ └──────────────┘
        │
┌───────▼───────────────────────────────────────────────┐
│                能力模块（均含双实现）                  │
│  Embedder    : HashEmbedder / OllamaEmbedder          │
│  VectorStore : MemoryVectorStore / QdrantVectorStore   │
│  Reranker    : HeuristicReranker / OnnxReranker        │
│  LLM         : MockLLM / OllamaLLM                     │
└───────────────────────────────────────────────────────┘
        │
┌───────▼───────────────────────────────────────────────┐
│  接入层 ingest/ : Loader(文本/MD/HTML/PDF) → Chunker    │
│  核心契约 core/ : models / errors / config / protocols  │
└───────────────────────────────────────────────────────┘
```

---

## 2. 模块与实现对照

| 模块 | Protocol | 离线兜底实现 | 生产实现 | 关键契约 |
|------|----------|--------------|----------|----------|
| 接入 | — | `Loader` / `Chunker` | 同左（纯本地） | `from_text()` / `chunk()` 滑动窗口 |
| 嵌入 | `Embedder` | `HashEmbedder` 确定性哈希（中文 字+双字、英文 词），`dim` 固定 | `OllamaEmbedder` 调 `/api/embed` | `async embed(texts) -> list[list[float]]` |
| 向量 | `VectorStore` | `MemoryVectorStore` 进程内余弦 | `QdrantVectorStore` 本地模式 | `upsert / search / count / reset` |
| 检索 | `Retriever` | `HybridRetriever`：稠密 + BM25 → RRF 融合 | 同左 | `retrieve(query, top_k) -> list[Hit]` |
| 重排 | `Reranker` | `HeuristicReranker` 词重叠分数 | `OnnxReranker` BGE-reranker（ONNX Runtime） | `rerank(query, hits, top_k)` |
| 生成 | `LLM` | `MockLLM` 从检索上下文抽取要点（faithful、确定性） | `OllamaLLM` 调 `/api/chat` | `chat(messages, temperature) -> str` |
| 智能体 | `Agent` | `AgentOrchestrator`：检索→重排→工具→生成 | 同左 | `run(query) -> AgentResult` |
| 评测 | `Evaluator` | `RAGEvaluator`：context_recall / precision / faithfulness | 同左 | `evaluate(case) -> EvalMetrics` |
| 观测 | `Tracer` | `Tracer` / `Span` 计时 | 同左 | `span(name) -> context manager` |

---

## 3. 数据流（一次 `/ask` 请求）

```
1. API /ask → Orchestrator.run(query)
2. retrieve: 取 query 的 embedding → 稠密 top-k
             同时 BM25 词面召回 top-k
             RRF 融合两路排名 → 候选 hits
3. rerank: 对候选 hits 精排 → 取 NM_RERANK_TOP_K
4. tool_route: 若查询命中工具意图（如“计算 …”）→ 调用对应 Tool
5. generate: 将重排后的上下文 + 工具结果喂给 LLM → 答案
6. 组装 AgentResult(answer, sources, steps) 返回 API
```

每个步骤均经 `Tracer` 记录 span（名称 + 耗时），便于排查。

---

## 4. 离线兜底的「可验证」设计

离线兜底是经过刻意设计的**确定性支点**，而非临时桩：

- `HashEmbedder`：对中文按「字 + 相邻双字」、英文按「词」做稳定哈希，同一文本向量恒定一致（`test_hash_embed_deterministic_and_distinct` 已验证）。
- `MemoryVectorStore`：纯余弦相似度，无外部状态。
- `MockLLM`：从检索到的上下文段中提取要点拼成答案，**不编造**——保证 faithfulness 评测有意义。
- `HeuristicReranker`：基于 query 与候选的词重叠打分，可解释。

因此「离线模式」下系统仍能完整跑通「接入→检索→重排→生成→评测」，使 CI 与干净环境一键复现成为可能。

---

## 5. 切换到生产引擎

只需设置环境变量，无需改动任何业务代码（依赖注入在 `container.build_system` 内完成）：

```bash
set NM_LLM=ollama
set NM_EMBED=ollama
set NM_VECTOR=qdrant
set NM_RERANK=onnx
.venv/Scripts/python.exe tools/serve.py
```

- Ollama 需本地运行并拉取 `nomic-embed-text` 与 `qwen2.5:3b`（或自定义模型）。
- `OnnxReranker` 默认读取 `models/reranker.onnx` 与 `models/tokenizer.json`（可从 ModelScope/HuggingFace 获取 BGE-reranker-v2-m3 的 ONNX 导出）。

---

© 2026 晨星.
