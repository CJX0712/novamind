# 部署指南

NovaMind 支持从「零依赖离线」到「本地生产引擎」的多种部署形态。核心原则：**同一份代码，靠环境变量切换后端**。

---

## 1. 离线形态（默认，零依赖）

适合 CI、演示、干净环境一键复现。无需 Ollama、无需模型权重、无需网络。

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe tools/verify.py      # 单测 + 端到端自检
.venv/Scripts/python.exe tools/serve.py       # http://127.0.0.1:8300
```

后端自动为：`mock / hash / memory / heuristic`。

---

## 2. 本地生产引擎形态

接入真实大模型与向量库。前置：本机已安装并运行 [Ollama](https://ollama.com)。

```bash
# 1. 拉取模型
ollama pull nomic-embed-text
ollama pull qwen2.5:3b

# 2. （可选）准备 ONNX 重排模型到 models/
#    ModelScope/HuggingFace 下载 BAAI/bge-reranker-v2-m3 的 ONNX 导出，
#    放置为 models/reranker.onnx 与 models/tokenizer.json

# 3. 以生产后端启动
set NM_LLM=ollama
set NM_EMBED=ollama
set NM_VECTOR=qdrant
set NM_RERANK=onnx
.venv/Scripts/python.exe tools/serve.py
```

后端映射：`OllamaLLM`(/api/chat) / `OllamaEmbedder`(/api/embed) / `QdrantVectorStore`(本地模式) / `OnnxReranker`(ONNX Runtime)。

> 若不使用 ONNX 重排，可保留 `NM_RERANK=heuristic`（仍可用）。Qdrant 以本地模式运行，无需独立服务进程。

---

## 3. 进程管理 / systemd（Linux 示例）

```ini
# /etc/systemd/system/novamind.service
[Unit]
Description=NovaMind API
After=network.target

[Service]
WorkingDirectory=/opt/novamind
ExecStart=/opt/novamind/.venv/bin/python tools/serve.py --port 8300
Environment=NM_LLM=ollama
Environment=NM_EMBED=ollama
Environment=NM_VECTOR=qdrant
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

---

## 4. Docker 部署

仓库内置 `Dockerfile` 与 `docker-compose.yml`（多阶段构建，烘焙依赖，默认离线兜底）。

```bash
# 构建并后台运行
docker compose up -d --build
# 访问 http://localhost:8300 ，文档 /docs

# 启用生产引擎（需容器内能访问宿主机 Ollama，通常以 host 网络或 extra_hosts 映射）
NM_LLM=ollama NM_EMBED=ollama docker compose up -d --build
```

> 说明：Dockerfile 默认安装全部依赖（含 onnxruntime / qdrant-client），无论是否启用对应后端，保证镜像可切换。

---

## 5. 健康检查与回滚

- **健康检查**：`GET /health` 返回 200 即就绪；CI 中 `tools/verify.py` 作为冒烟。
- **回滚**：所有依赖在 `requirements.txt` / `freeze.txt` 锁定版本，回退到任一已发布 commit 即可精确复原运行环境。

---

## 6. 端口与环境变量

| 项 | 默认 | 说明 |
|----|------|------|
| 服务端口 | 8300 | `tools/serve.py --port` |
| Ollama 地址 | `http://127.0.0.1:11434` | `NM_OLLAMA_URL` |
| 文档与交互 | `/docs`（Swagger） | FastAPI 自带 |

---

© 2026 晨星.
