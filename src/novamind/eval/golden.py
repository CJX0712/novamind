"""离线黄金评测集：用于自检检索与生成链路，无需任何模型。

作者：晨星
"""
from __future__ import annotations

from novamind.core.models import Document, EvalCase

# 固定语料，供测试与评测灌入
CORPUS: list[Document] = [
    Document(
        id="doc-novamind",
        text=(
            "NovaMind 是一套本地优先、模块化的 AI 智能体系统。"
            "它由接入、嵌入、向量库、检索、重排、生成、智能体编排与评测八个核心模块构成，"
            "每个模块以协议定义接口，运行时注入生产或兜底实现，保证可独立验证与协同。"
            "系统默认使用 Ollama 作为本地大模型与嵌入引擎，在干净环境中可用哈希嵌入与内存向量库离线运行。"
        ),
        metadata={"topic": "system"},
    ),
    Document(
        id="doc-deploy",
        text=(
            "部署 NovaMind 只需克隆仓库并创建隔离环境，安装锁定版本的依赖后执行 verify 自检。"
            "系统通过环境变量切换 LLM、嵌入、向量库与重排后端，CI 在干净 runner 上离线复现全部测试。"
        ),
        metadata={"topic": "deploy"},
    ),
]

GOLDEN_CASES: list[EvalCase] = [
    EvalCase(
        query="NovaMind 由哪些核心模块组成？",
        relevant_doc_ids=["doc-novamind"],
        reference_answer="接入、嵌入、向量库、检索、重排、生成、智能体编排、评测",
    ),
    EvalCase(
        query="如何部署 NovaMind？",
        relevant_doc_ids=["doc-deploy"],
        reference_answer="克隆仓库、建隔离环境、装锁定依赖、跑 verify",
    ),
]
