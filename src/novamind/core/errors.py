"""统一异常体系。所有模块抛出的业务错误均继承自 NovaMindError。

作者：晨星
"""
from __future__ import annotations


class NovaMindError(Exception):
    """所有 NovaMind 业务异常的基类。"""


class ConfigError(NovaMindError):
    """配置非法或缺失后端实现。"""


class BackendUnavailable(NovaMindError):
    """生产后端（如 Ollama / Qdrant）不可达。"""


class IngestionError(NovaMindError):
    """文档接入或分块失败。"""


class RetrievalError(NovaMindError):
    """检索/向量库操作失败。"""


class GenerationError(NovaMindError):
    """LLM 生成失败。"""
