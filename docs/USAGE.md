# 使用指南

覆盖：API 调用、前端控制台、命令行工具、二次开发（新增后端实现）。

---

## 1. REST API

服务启动后（默认 `http://127.0.0.1:8300`），可用任意 HTTP 客户端调用。完整契约见 [`openapi.yaml`](../openapi.yaml) 与 `/docs` 交互式页面。

### 1.1 健康检查

```bash
curl http://127.0.0.1:8300/health
# {"status":"ok","backends":{"llm":"mock","embed":"hash","vector":"memory","rerank":"heuristic"}}
```

### 1.2 接入文档

```bash
curl -X POST http://127.0.0.1:8300/ingest \
  -H "Content-Type: application/json" \
  -d '{"text":"NovaMind 是本地优先的模块化 AI 智能体系统，包含检索与生成模块。"}'
# {"ingested_chunks":1,"doc_id":"a1b2c3d4e5f6"}
```

### 1.3 问答

```bash
curl -X POST http://127.0.0.1:8300/ask \
  -H "Content-Type: application/json" \
  -d '{"query":"NovaMind 由哪些核心模块组成？"}'
# {"answer":"...","sources":[{"chunk_id":...,"doc_id":...,"text":...,"score":...}],"steps":[...]}
```

### 1.4 检索（仅取上下文）

```bash
curl -X POST http://127.0.0.1:8300/search \
  -H "Content-Type: application/json" \
  -d '{"query":"模块化 AI","top_k":3}'
# {"hits":[{"chunk_id":...,"doc_id":...,"text":...,"score":...}]}
```

### 1.5 评测（离线黄金集）

```bash
curl -X POST http://127.0.0.1:8300/evaluate
# {"cases":[...],"avg_context_recall":0.xxx,"avg_faithfulness":0.xxx}
```

---

## 2. 前端控制台（web/index.html）

单文件、零依赖。用浏览器直接打开 `web/index.html`：

1. 在顶部「API 地址」填入服务地址（默认 `http://127.0.0.1:8300`），点「连接测试」。
2. **接入**：粘贴知识文本 → 接入文档（自动分块、嵌入、入库、建 BM25）。
3. **问答**：输入问题 → 查看答案、引用来源与执行步骤。
4. **检索**：查看混合检索命中。
5. **评测**：一键运行内置黄金集评测，查看 context_recall / faithfulness。

> 前端全程使用内联 SVG 图标（无 emoji），暗色主题，兼容离线部署。

---

## 3. 命令行工具（tools/）

| 工具 | 用途 |
|------|------|
| `tools/verify.py` | 一键自检：先跑 pytest 单测，再跑端到端。全绿即系统可用。 |
| `tools/serve.py` | 以真实 socket 拉起 API（`--port` 可改）。 |
| `tools/scan_emoji.py [path]` | P0 质量门禁：扫描代码，禁止 emoji 作功能图标。 |

```bash
.venv/Scripts/python.exe tools/verify.py
.venv/Scripts/python.exe tools/serve.py --port 9000
.venv/Scripts/python.exe tools/scan_emoji.py .
```

---

## 4. Python SDK 用法

```python
import asyncio
from novamind.core.config import Settings
from novamind.core.container import build_system
from novamind.ingest.loader import Loader

async def main():
    sys = build_system(Settings())  # 默认离线
    docs = [Loader.from_text("NovaMind 是本地优先的模块化 AI 智能体系统。")]
    n = await sys.ingest(docs)
    res = await sys.agent.run("NovaMind 是什么？")
    print(res.answer, res.sources)

asyncio.run(main())
```

---

## 5. 二次开发：新增一个后端实现

以「新增一个 Embedder 实现」为例：

1. 在 `src/novamind/embed/` 新建 `my_embed.py`，实现 `embed(texts) -> list[list[float]]` 且满足 `Embedder` Protocol（提供 `dim` 属性）。
2. 在 `core/container.py` 的 `build_system` 中按配置分支注册：
   ```python
   elif settings.embed_backend == "my":
       embedder = MyEmbedder(...)
   ```
3. 在 `core/config.py` 文档与 README 配置表中登记 `NM_EMBED=my`。
4. 补一条单测（参考 `test_hash_embed_deterministic_and_distinct`）。

> 业务代码（retriever / agent / api）**无需任何改动**——这是协议 + 注入设计的核心收益。

---

© 2026 晨星.
