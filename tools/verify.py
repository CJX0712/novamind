"""一键自检入口：单测（离线）+ 端到端（真实拉起服务）。

作者：晨星
"""
from __future__ import annotations

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 用当前解释器，避免硬编码平台专属 venv 路径
# (Windows: .venv/Scripts/python.exe, POSIX: .venv/bin/python)
VENV_PY = sys.executable
BASE_TEMP = os.path.join(ROOT, "data", ".pytest-tmp")


def run(cmd: list[str]) -> int:
    print("\n>>> " + " ".join(cmd))
    return subprocess.run(cmd).returncode


def main() -> int:
    rc = run(
        [VENV_PY, "-m", "pytest", "tests/test_system.py", "-q",
         "--basetemp", BASE_TEMP, "-p", "no:cacheprovider"]
    )
    if rc != 0:
        print("单测失败，终止。")
        return rc
    rc = run([VENV_PY, "tests/e2e_smoke.py"])
    if rc != 0:
        print("E2E 失败，终止。")
        return rc
    print("\n全部自检通过：单测 + 端到端。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
