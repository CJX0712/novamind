"""P0 绝对规则门禁：扫描源码中作为「功能图标」的 emoji。

专家团 P0-1 规则禁止在任何 UI 代码 / 设计稿 / HTML 产物中使用 emoji 作功能图标
（图标须用项目锁定的一套可缩放 SVG）。本工具按专家定义的正则在代码文件中检索 emoji，
命中即视为违规，门禁不通过（退出码 1）。

注意：专家给定的正则采用 PCRE/JS 的 `\\x{...}` 写法；Python `re` 使用
`\\uXXXX`（4 位）与 `\\UXXXXXXXX`（8 位）等价区间，已在下方精确转换。

作者：晨星
"""
from __future__ import annotations

import pathlib
import re
import sys

# 与专家 P0-1 正则完全等价的 Unicode 区间（以 (start, end) 整数对表示）。
# 关键：必须用实际码位 chr(start) + "-" + chr(end) 拼装字符类，
# 不能用 \uXXXX 字符串转义（Python 的 \u 只取 4 位，会截断 5/6 位码位导致误匹配）。
_EMOJI_RANGES = [
    (0x1F300, 0x1F9FF),  # 杂项符号与象形/表情
    (0x2600, 0x26FF),    # 杂项符号
    (0x2700, 0x27BF),    # 装饰符号与箭头
    (0xFE00, 0xFE0F),    # 变体选择符
    (0x1F000, 0x1F02F),  # 麻将牌
    (0x1F0A0, 0x1F0FF),  # 扑克牌
    (0x1F100, 0x1F64F),  # 带圈数字/字母 + 表情补充
    (0x1F680, 0x1F6FF),  # 交通与地图符号 + 表情符号
    (0x1F900, 0x1F9FF),  # 表情符号补充
    (0x1FA00, 0x1FA6F),  # 象棋符号等
    (0x1FA70, 0x1FAFF),  # 符号补充
    (0x200D, 0x200D),    # 零宽连接符（组合表情核心）
    (0x20E3, 0x20E3),    # 组合用圈号键帽
    (0xE0020, 0xE007F),  # 语言标签
]
_EMOJI_RE = re.compile(
    "[" + "".join(chr(s) + "-" + chr(e) for s, e in _EMOJI_RANGES) + "]"
)

# 纳入扫描的代码/标记文件类型
_SCAN_SUFFIXES = {".py", ".html", ".htm", ".js", ".ts", ".tsx", ".jsx", ".vue", ".css", ".scss"}

# 跳过目录
_SKIP_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__",
    "build", "dist", ".pytest_cache", ".mypy_cache", ".idea", ".vscode",
}


def scan(root: pathlib.Path) -> list[tuple[pathlib.Path, int, int, str]]:
    hits: list[tuple[pathlib.Path, int, int, str]] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in _SCAN_SUFFIXES:
            continue
        if any(part in _SKIP_DIRS for part in p.parts):
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for ln, line in enumerate(text.splitlines(), start=1):
            for m in _EMOJI_RE.finditer(line):
                hits.append((p, ln, m.start() + 1, m.group()))
    return hits


def main() -> int:
    root = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path.cwd()
    if not root.exists():
        print(f"路径不存在: {root}")
        return 2
    print(f"P0 emoji 门禁扫描: {root}")
    hits = scan(root)
    if not hits:
        print("通过: 未发现作为功能图标的 emoji。")
        return 0
    print(f"\n发现 {len(hits)} 处 emoji 违规（P0-1 禁止作功能图标）：\n")
    for path, ln, col, ch in hits:
        rel = path.relative_to(root)
        print(f"  {rel}:{ln}:{col}  {ch!r}")
    print("\n门禁失败: 请改用项目锁定的 SVG 图标库，移除上述 emoji。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
