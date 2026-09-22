# NovaMind 规格契约（Spec）

> 本文件为团队内部契约：锁定范围、模块、API、配置与验收标准。后续开发以本文件为唯一依据。
> 基于 NovaMind v1.0.0 实现状态生成。状态：已确认。

---

## 1. 产品定义

- **一句话**：本地优先、模块化、端到端可运行的 AI 智能体系统（RAG + 工具编排）。
- **目标用户**：希望私有化部署检索增强生成能力的开发者 / 团队。
- **核心问题**：把「接入、嵌入、向量、检索、重排、生成、编排、评测」拆成可独立验证、可协同的模块，并在零依赖环境下可完整跑通。

---

## 2. MVP 范围（锁定）

| 优先级 | 功能 | 验收摘要 |
|--------|------|----------|
| P0 | 文档接入与分块 | 支持文本/MD/HTML/PDF，滑动窗口分块 |
| P0 | 离线兜底全链路 | mock/hash/memory/heuristic 下 health→ingest→ask→evaluate 全绿 |
| P0 | 混合检索 | 稠密 + BM25 经 RRF 融合 |
| P0 | 工具编排 | 计算器、时钟工具路由；可扩展 Tool 协议 |
| P0 | REST API | /health /ingest /ask /search /evaluate |
| P0 | 单文件前端控制台 | 暗色、零依赖、SVG 图标，调 API |
| P1 | 生产引擎接入 | Ollama（LLM+Embed）、Qdrant（向量）、ONNX 重排 |
| P1 | 黄金集评测 | context_recall / precision / faithfulness |

---

## 3. 明确不做（Out-of-Scope）

| 不做 | 原因 | 何时考虑 |
|------|------|----------|
| 多租户 / 用户认证 | MVP 阶段单机私有部署足够 | 有 SaaS 需求时 |
| 分布式向量集群 | 本地优先定位 | 数据规模超单机时 |
| 可视化知识图谱 | 超出 MVP 范围 | v2.0 |
| 模型微调 | 复用开源成果，不自研 | 有领域适配需求时 |

---

## 4. 技术架构（锁定版本）

| 层 | 技术 | 版本 | 锁定原因 |
|----|------|------|----------|
| 语言 | Python | ≥3.12（已验证 3.12/3.13） | numpy 2.x 硬约束 |
| Web 框架 | FastAPI | 0.115.6 | 类型化路由 + 自动 OpenAPI |
| ASGI 服务 | Uvicorn | 0.34.0 | 标准 ASGI 服务器 |
| 数据校验 | Pydantic | 2.10.4 | 请求/响应契约 |
| HTTP 客户端 | httpx | 0.28.1 | TestClient / Ollama 调用 |
| 向量(生产) | Qdrant 本地模式 | 1.12.1 | 轻量本地向量库 |
| 重排(生产) | ONNX Runtime | 1.20.1 | 跨平台零编译推理 |
| PDF 解析 | pypdf | 5.1.0 | 纯 Python，无系统依赖 |
| 词面召回 | rank-bm25 | 0.2.2 | Okapi BM25 |
| 测试 | pytest | 8.3.4 | 单元 + 端到端 |

---

## 5. API 端点清单（锁定）

| Method | Path | 功能 | 认证 | 请求体 | 响应 |
|--------|------|------|------|--------|------|
| GET | /health | 系统状态与后端 | 无 | — | `{status, backends}` |
| POST | /ingest | 接入文本 | 无 | `{text, doc_id?}` | `{ingested_chunks, doc_id}` |
| POST | /ask | 问答 | 无 | `{query, top_k?}` | `{answer, sources[], steps[]}` |
| POST | /search | 检索 | 无 | `{query, top_k}` | `{hits[]}` |
| POST | /evaluate | 黄金集评测 | 无 | — | `{cases[], avg_context_recall, avg_faithfulness}` |

完整契约见 [`openapi.yaml`](../openapi.yaml)。

---

## 6. 配置（锁定）

通过环境变量注入（前缀 `NM_`），详见 README 配置表与 `core/config.py`。
默认全离线兜底：`NM_LLM=mock NM_EMBED=hash NM_VECTOR=memory NM_RERANK=heuristic`。

---

## 7. 验收标准（EARS 格式）

| 编号 | 功能 | 验收标准 |
|------|------|----------|
| AC-01 | health | When 请求 `/health`，系统**必须**返回 200 与 `status=ok` |
| AC-02 | ingest | When 提交非空文本，系统**必须**返回 200 且 `ingested_chunks ≥ 1` |
| AC-03 | ingest 校验 | If 提交纯空白文本，系统**必须**返回 ≥400 |
| AC-04 | ask | When 先 ingest 再 ask，系统**必须**返回非空 `answer` 与 `sources` |
| AC-05 | search | When 先 ingest 再 search，系统**必须**返回 `hits` 列表 |
| AC-06 | evaluate | When 请求 `/evaluate`，系统**必须**返回 `avg_context_recall` 字段 |
| AC-07 | 离线可跑 | While 使用默认离线配置，系统**必须**在无网络/无模型下完成 AC-01~AC-06 |
| AC-08 | 可替换 | If 设置 `NM_LLM=ollama` 等，系统**应该**切换到对应生产实现而不改业务代码 |

---

## 8. 模块接口（Protocol 摘要）

见 `core/protocols.py`：`Embedder / VectorStore / Retriever / Reranker / LLM / Agent / Evaluator / Tracer`。
各模块实现须满足对应 Protocol（运行时 `runtime_checkable` 可断言）。

---

## 9. 端到端验证步骤

```bash
# 1. 安装（干净环境）
python -m venv .venv && .venv/Scripts/python.exe -m pip install -r requirements.txt

# 2. 一键自检（单测 + 端到端，全离线）
.venv/Scripts/python.exe tools/verify.py

# 3. 启动服务
.venv/Scripts/python.exe tools/serve.py   # http://127.0.0.1:8300

# 4. 核心成功流
curl -X POST http://127.0.0.1:8300/ingest -H "Content-Type: application/json" \
  -d "{\"text\":\"NovaMind 是本地优先的模块化 AI 智能体系统。\"}"
# 断言：200 且 ingested_chunks >= 1

# 5. 关键错误流
curl -X POST http://127.0.0.1:8300/ingest -H "Content-Type: application/json" -d "{\"text\":\"   \"}"
# 断言：>= 400
```

---

© 2026 晨星.
