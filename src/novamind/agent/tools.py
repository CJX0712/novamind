"""智能体工具集：可扩展的工具注册表。

作者：晨星
"""
from __future__ import annotations

import ast
import operator
import re
from dataclasses import dataclass


@dataclass
class Tool:
    name: str
    description: str

    def run(self, arg: str) -> str:  # pragma: no cover - 由子类实现
        raise NotImplementedError


class CalculatorTool(Tool):
    """安全四则运算（仅允许数字与 + - * / ( ) 运算符）。"""

    def __init__(self) -> None:
        super().__init__(name="calculator", description="计算四则表达式，如 12*8+3")

    def run(self, arg: str) -> str:
        expr = re.sub(r"[^0-9+\-*/().\s]", "", arg).strip()
        if not expr:
            return "无法解析表达式"
        try:
            # 受限求值：仅基础算子，禁用任意名称
            node = ast.parse(expr, mode="eval")
            allowed = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant,
                       ast.Add, ast.Sub, ast.Mult, ast.Div, ast.USub, ast.UAdd, ast.Pow)
            for n in ast.walk(node):
                if not isinstance(n, allowed):
                    return "不支持的运算"
            result = eval(compile(node, "<calc>", "eval"),
                          {"__builtins__": {}},
                          {"__operator__": operator})
            return str(result)
        except Exception:  # noqa: BLE001 - 工具级容错
            return "计算失败"


class ClockTool(Tool):
    """返回当前时间（确定性，仅用于演示工具路由）。"""

    def __init__(self) -> None:
        super().__init__(name="clock", description="返回当前系统时间")

    def run(self, arg: str) -> str:
        import datetime

        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class ToolRegistry:
    """工具注册表，供智能体按名调用。"""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}
        for t in (CalculatorTool(), ClockTool()):
            self._tools[t.name] = t

    def list(self) -> list[Tool]:
        return list(self._tools.values())

    def call(self, name: str, arg: str) -> str:
        tool = self._tools.get(name)
        if not tool:
            return f"未知工具: {name}"
        return tool.run(arg)
