"""本地服务启动器：以真实 socket 拉起 NovaMind API（供前端 web/index.html 连接）。

默认端口 8300，可用 `python tools/serve.py --port 9000` 修改。
后端由环境变量决定（见 novamind.core.config.Settings.from_env），默认离线兜底。

作者：晨星
"""
from __future__ import annotations

import argparse
import pathlib
import sys

# src 布局引导：保证 `python tools/serve.py` 直接运行时可 import novamind
_SRC = str(pathlib.Path(__file__).resolve().parents[1] / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import uvicorn  # noqa: E402

from novamind.api.app import app  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="NovaMind 本地服务")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8300)
    args = parser.parse_args()
    print(f"NovaMind API → http://{args.host}:{args.port}  (docs: /docs)")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    return 0


if __name__ == "__main__":
    sys.exit(main())
