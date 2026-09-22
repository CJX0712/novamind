"""核心数据模型：文档、分块、命中、消息、评测样本。

作者：晨星
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Document:
    """一篇被接入系统、待分块/索引的原始文档。"""

    id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Chunk:
    """文档分块后的最小检索单元。"""

    id: str
    doc_id: str
    text: str
    index: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Hit:
    """一次检索/重排返回的命中结果。"""

    chunk_id: str
    doc_id: str
    text: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Message:
    """一次对话消息。role 取值 user / assistant / system。"""

    role: str
    content: str


@dataclass
class AgentStep:
    """智能体编排过程中的单步记录，用于可观测与回放。"""

    action: str
    detail: str
    tool: str | None = None


@dataclass
class AgentResult:
    """智能体最终输出。"""

    answer: str
    steps: list[AgentStep] = field(default_factory=list)
    sources: list[Hit] = field(default_factory=list)


@dataclass
class EvalCase:
    """评测黄金样本：问句 + 应召回的文档 + 参考答案。"""

    query: str
    relevant_doc_ids: list[str]
    reference_answer: str | None = None


@dataclass
class EvalMetrics:
    """评测指标集合。"""

    context_recall: float
    context_precision: float
    faithfulness: float
    answered: bool
    notes: str = ""
