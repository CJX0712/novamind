"""生产重排实现：ONNX 跨编码器（如 BGE-Reranker），模型自 ModelScope 拉取。

离线/无模型环境下系统自动回退 HeuristicReranker，保证可复现。

作者：晨星
"""
from __future__ import annotations

from novamind.core.errors import BackendUnavailable
from novamind.core.models import Hit


class OnnxReranker:
    """基于 ONNXRuntime 的跨编码器重排器。"""

    def __init__(self, model_path: str, tokenizer_path: str) -> None:
        try:
            import onnxruntime as ort
            from tokenizers import Tokenizer
        except ImportError as exc:  # pragma: no cover
            raise BackendUnavailable("ONNX 重排需要 onnxruntime + tokenizers") from exc
        import os

        if not os.path.exists(model_path) or not os.path.exists(tokenizer_path):
            raise BackendUnavailable(
                f"重排模型缺失: model={model_path} tokenizer={tokenizer_path}"
            )
        self._sess = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
        self._tok = Tokenizer.from_file(tokenizer_path)
        self._inputs = [i.name for i in self._sess.get_inputs()]

    async def rerank(self, query: str, hits: list[Hit], top_k: int = 4) -> list[Hit]:
        if not hits:
            return []
        pairs = [(query, h.text) for h in hits]
        enc = self._tok(
            [p[0] for p in pairs],
            [p[1] for p in pairs],
            padding=True,
            truncation=True,
            max_length=512,
        )
        feeds = {
            "input_ids": enc["input_ids"],
            "attention_mask": enc["attention_mask"],
            "token_type_ids": enc["token_type_ids"],
        }
        feeds = {k: v for k, v in feeds.items() if k in self._inputs}
        logits = self._sess.run(None, feeds)[0]
        scores = [float(x[0]) for x in logits]
        ranked = sorted(zip(hits, scores), key=lambda x: x[1], reverse=True)
        out: list[Hit] = []
        for h, s in ranked[:top_k]:
            h.score = round(s, 6)
            out.append(h)
        return out
