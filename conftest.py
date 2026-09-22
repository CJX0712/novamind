"""Pytest 引导：将 src 布局加入 import 路径，使 `import novamind` 可用。

作者：晨星
"""
from __future__ import annotations

import pathlib
import sys

_SRC = str(pathlib.Path(__file__).resolve().parent / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)
