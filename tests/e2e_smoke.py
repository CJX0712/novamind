"""自包含端到端自检：进程内 ASGI 全链路（FastAPI TestClient，无 socket、无端口冲突）。

覆盖核心成功流 + 错误流，证明系统真的能跑起来，而非仅单测通过。
默认离线（mock）后端，无需 Ollama/网络。

真实服务可用以下命令拉起（独立进程、真实 socket）：
    uvicorn novamind.api.app:app --port 8300

作者：晨星
"""
from __future__ import annotations

import pathlib
import sys

# src 布局引导：保证 `python tests/e2e_smoke.py` 直接运行时可 import novamind
_SRC = str(pathlib.Path(__file__).resolve().parents[1] / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from fastapi.testclient import TestClient  # noqa: E402
import logging  # noqa: E402

logging.getLogger("httpx").setLevel(logging.WARNING)

from novamind.api.app import create_app  # noqa: E402
from novamind.core.config import Settings  # noqa: E402


def main() -> int:
    app = create_app(
        Settings(
            llm_backend="mock",
            embed_backend="hash",
            vector_backend="memory",
            rerank_backend="heuristic",
        )
    )

    # 装配自检：断言 served app 路由齐全，避免「僵尸进程 / 路由未挂载」导致静默 404
    mounted = {getattr(r, "path", None) for r in app.routes}
    for need in ("/health", "/ingest", "/ask", "/search", "/evaluate"):
        assert need in mounted, f"路由缺失: {need}"

    client = TestClient(app)
    passed = failed = 0

    def check(name: str, cond: bool, detail: str = "") -> None:
        nonlocal passed, failed
        if cond:
            passed += 1
            print(f"  通过: {name}")
        else:
            failed += 1
            print(f"  失败: {name} -> {detail}")

    h = client.get("/health")
    check("health 就绪", h.status_code == 200 and h.json().get("status") == "ok", h.text)

    ing = client.post(
        "/ingest",
        json={"text": "NovaMind 是本地优先的模块化 AI 智能体系统，包含检索与生成模块。"},
    )
    check(
        "ingest 成功",
        ing.status_code == 200 and ing.json().get("ingested_chunks", 0) >= 1,
        ing.text,
    )

    ask = client.post("/ask", json={"query": "NovaMind 是什么？"})
    check("ask 成功", ask.status_code == 200 and bool(ask.json().get("answer")), ask.text)

    ev = client.post("/evaluate")
    check(
        "evaluate 成功",
        ev.status_code == 200 and "avg_context_recall" in ev.json(),
        ev.text,
    )

    bad = client.post("/ingest", json={"text": "   "})
    check("空文档被拒", bad.status_code >= 400, bad.text)

    s = client.post("/search", json={"query": "模块化 AI", "top_k": 3})
    check(
        "search 返回命中",
        s.status_code == 200 and isinstance(s.json().get("hits"), list),
        s.text,
    )

    print(f"\nE2E 汇总: 通过 {passed} / 失败 {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
