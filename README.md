# NovaMind

> 本地优先、模块化、端到端可实际运行的 AI 智能体系统。
> 检索增强生成（RAG）+ 工具编排，按单一职责划分模块，协议式接口，可独立验证、可协同组成完整链路。

**作者：晨星** · License: MIT · Python ≥ 3.12

---

## 特性

- **模块化单一职责**：接入 / 嵌入 / 向量 / 检索 / 重排 / 生成 / 智能体 / 评测 / 观测 / API 各司其职，接口用 `typing.Protocol` 定义。
- **协议 + 注入实现**：每个模块都有「生产实现」与「离线兜底实现」，通过配置自由组合，**零依赖、零模型、零网络即可完整跑通**。
- **离线可验证**：默认 `hash` 嵌入 + `memory` 向量 + `heuristic` 重排 + `mock` 生成，无需 Ollama / 模型权重即可自检。
- **生产就绪**：一键切换到 Ollama（本地大模型）+ Qdrant（向量库）+ ONNX 重排（BGE-reranker），无需改业务代码。
- **混合检索**：稠密向量 + BM25 词面召回，经 RRF（Reciprocal Rank Fusion）倒数排名融合。
- **工具编排**：智能体支持计算器、时钟等工具路由；可扩展 `Tool` 协议。
- **一键自检**：`pytest` 单测（9 项）+ 进程内 ASGI 端到端（6 项）全绿。
- **P0 质量门禁**：内置 emoji 图标扫描（`tools/scan_emoji.py`），UI 全部使用 SVG 图标，禁用 emoji 作功能图标。

---

## 一分钟上手（离线，无需任何外部服务）

```bash
# 1. 创建并激活虚拟环境（Windows 用 Scripts\python.exe）
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt

# 2. 一键自检（单测 + 端到端）
.venv/Scripts/python.exe tools/verify.py

# 3. 启动 API 服务（默认 http://127.0.0.1:8300）
.venv/Scripts/python.exe tools/serve.py

# 4. 另开终端，打开前端控制台
#    用浏览器打开 web/index.html，API 地址填 http://127.0.0.1:8300
```

---

## 项目结构

```
novamind/
├── src/novamind/                # 源码（src 布局）
│   ├── core/                    # models / errors / config / protocols / container
│   ├── ingest/                  # loader（多格式加载）、chunker（滑动窗口分块）
│   ├── embed/                   # hash_embed（离线） / ollama（生产）
│   ├── vector/                  # memory_store（离线） / qdrant_store（生产）
│   ├── retrieve/                # bm25（词面召回） / fusion（RRF 混合融合）
│   ├── rerank/                  # heuristic（离线） / onnx_rerank（生产）
│   ├── llm/                     # mock（离线） / ollama（生产）
│   ├── agent/                   # tools（工具路由） / orchestrator（多步编排）
│   ├── eval/                    # metrics（RAG 评测） / golden（离线黄金集）
│   ├── observ/                  # tracer（轻量链路追踪）
│   └── api/                     # schemas / routes / app（FastAPI 装配）
├── web/index.html               # 单文件前端控制台（暗色、零依赖、SVG 图标）
├── tests/                       # test_system.py（单测） / e2e_smoke.py（端到端）
├── tools/                       # verify.py（自检） / serve.py（服务） / scan_emoji.py（P0 门禁）
├── docs/                        # ARCHITECTURE / SPEC / DEPLOYMENT / USAGE / decisions(ADR)
├── openapi.yaml                 # API OpenAPI 3.0 契约
├── requirements.txt             # 版本锁定的依赖清单
├── pyproject.toml              # 构建配置
└── freeze.txt                   # pip freeze 完整锁（干净环境复现证据）
```

---

## 配置（环境变量，默认离线兜底）

| 变量 | 含义 | 可选值 | 默认 |
|------|------|--------|------|
| `NM_LLM` | 生成后端 | `mock` / `ollama` | `mock` |
| `NM_EMBED` | 嵌入后端 | `hash` / `ollama` | `hash` |
| `NM_VECTOR` | 向量库 | `memory` / `qdrant` | `memory` |
| `NM_RERANK` | 重排后端 | `heuristic` / `onnx` | `heuristic` |
| `NM_OLLAMA_URL` | Ollama 地址 | URL | `http://127.0.0.1:11434` |
| `NM_LLM_MODEL` | Ollama 生成模型 | 如 `qwen2.5:3b` | `qwen2.5:3b` |
| `NM_EMBED_MODEL` | Ollama 嵌入模型 | 如 `nomic-embed-text` | `nomic-embed-text` |
| `NM_RERANK_MODEL` | ONNX 重排模型 | 如 `BAAI/bge-reranker-v2-m3` | `BAAI/bge-reranker-v2-m3` |
| `NM_TOP_K` | 检索候选数 | int | `8` |
| `NM_RERANK_TOP_K` | 重排后保留数 | int | `4` |
| `NM_CHUNK_SIZE` / `NM_CHUNK_OVERLAP` | 分块大小 / 重叠 | int | `500` / `80` |

---

## 典型链路

```
文档 → Loader → Chunker → Embedder → VectorStore (upsert)
                                      ↓
查询 → HybridRetriever(稠密 + BM25 → RRF 融合) → Reranker → LLM/Agent → 答案 + 来源 + 步骤
                                      ↓
                                  Evaluator(黄金集评测)
```

详见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) 与 [docs/SPEC.md](docs/SPEC.md)。

---

## 质量保障

- **单测**：`tests/test_system.py`，覆盖分块、嵌入、向量检索、BM25、混合检索、智能体、计算器工具、评测、API，全绿。
- **端到端**：`tests/e2e_smoke.py` 用 FastAPI `TestClient` 跑通 health→ingest→ask→evaluate→错误流→search，无端口冲突、可复现。
- **P0 门禁**：`tools/scan_emoji.py` 扫描源码，确保 UI 不使用 emoji 作功能图标（使用锁定的 SVG 图标）。
- **CI**：`.github/workflows/ci.yml` 在 Python 3.12 / 3.13 矩阵下运行 `tools/verify.py`。

---

© 2026 晨星. 以 MIT 协议发布。
