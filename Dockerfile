# NovaMind 多阶段构建镜像：烘焙全部依赖（含 onnxruntime / qdrant-client），默认离线兜底。
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    NM_LLM=mock \
    NM_EMBED=hash \
    NM_VECTOR=memory \
    NM_RERANK=heuristic

WORKDIR /app

# 依赖层（利用构建缓存）
COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt

# 源码层：editable 安装需要 src/ 与 README 已就位，故先 COPY 再安装。
COPY . .
RUN pip install --no-cache-dir -e . --no-deps

EXPOSE 8300
CMD ["sh", "-c", "uvicorn novamind.api.app:app --host 0.0.0.0 --port 8300"]
