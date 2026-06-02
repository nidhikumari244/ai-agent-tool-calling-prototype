from __future__ import annotations

import ast
import logging
import operator
import re
import time
from collections import Counter
from dataclasses import dataclass
from typing import Any, Callable


logger = logging.getLogger("tools")


@dataclass
class ToolResult:
    ok: bool
    data: dict[str, Any]
    error: str = ""


class ToolValidationError(ValueError):
    pass


def with_retries(max_attempts: int = 2, delay_seconds: float = 0.1) -> Callable:
    def decorator(func: Callable[..., ToolResult]) -> Callable[..., ToolResult]:
        def wrapper(*args: Any, **kwargs: Any) -> ToolResult:
            last_error = ""
            for attempt in range(1, max_attempts + 1):
                start = time.perf_counter()
                try:
                    logger.info("tool_start | tool=%s attempt=%s args=%s kwargs=%s", func.__name__, attempt, args, kwargs)
                    result = func(*args, **kwargs)
                    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
                    logger.info("tool_end | tool=%s attempt=%s elapsed_ms=%s result=%s", func.__name__, attempt, elapsed_ms, result)
                    return result
                except Exception as exc:
                    last_error = str(exc)
                    logger.exception("tool_error | tool=%s attempt=%s error=%s", func.__name__, attempt, exc)
                    if attempt < max_attempts:
                        time.sleep(delay_seconds)
            return ToolResult(ok=False, data={}, error=last_error)

        return wrapper

    return decorator


ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def _eval_expression(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in ALLOWED_OPERATORS:
        return ALLOWED_OPERATORS[type(node.op)](_eval_expression(node.left), _eval_expression(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in ALLOWED_OPERATORS:
        return ALLOWED_OPERATORS[type(node.op)](_eval_expression(node.operand))
    raise ToolValidationError("expression contains unsupported syntax")


@with_retries()
def calculator(expression: str) -> ToolResult:
    if not expression or len(expression) > 120:
        raise ToolValidationError("expression is required and must be under 120 characters")
    if not re.fullmatch(r"[0-9+\-*/(). ^]+", expression):
        raise ToolValidationError("expression may only contain numbers and arithmetic operators")

    normalized = expression.replace("^", "**")
    tree = ast.parse(normalized, mode="eval")
    value = _eval_expression(tree.body)
    return ToolResult(ok=True, data={"expression": expression, "value": round(value, 6)})


@with_retries()
def text_analyzer(text: str) -> ToolResult:
    if not text.strip():
        raise ToolValidationError("text is required")
    words = re.findall(r"[A-Za-z0-9']+", text.lower())
    sentences = [item for item in re.split(r"[.!?]+", text) if item.strip()]
    common = Counter(words).most_common(5)
    return ToolResult(
        ok=True,
        data={
            "characters": len(text),
            "words": len(words),
            "sentences": len(sentences),
            "top_words": [{"word": word, "count": count} for word, count in common],
        },
    )


@with_retries()
def unit_converter(value: float, from_unit: str, to_unit: str) -> ToolResult:
    conversions = {
        ("km", "miles"): 0.621371,
        ("miles", "km"): 1.60934,
        ("kg", "lb"): 2.20462,
        ("lb", "kg"): 0.453592,
        ("c", "f"): None,
        ("f", "c"): None,
    }
    key = (from_unit.lower(), to_unit.lower())
    if key not in conversions:
        raise ToolValidationError(f"unsupported conversion: {from_unit} to {to_unit}")

    if key == ("c", "f"):
        converted = value * 9 / 5 + 32
    elif key == ("f", "c"):
        converted = (value - 32) * 5 / 9
    else:
        converted = value * conversions[key]

    return ToolResult(
        ok=True,
        data={
            "input_value": value,
            "from_unit": from_unit,
            "to_unit": to_unit,
            "converted_value": round(converted, 4),
        },
    )


@with_retries()
def knowledge_lookup(topic: str) -> ToolResult:
    knowledge_base = {
        "agent": "An agent is software that can plan actions, call tools, observe results, and produce a final answer.",
        "json schema": "JSON schema validation checks whether structured output contains required fields and valid value types.",
        "retry": "Retries help tools recover from temporary failures, but should be bounded to avoid loops.",
        "timeout": "Timeouts prevent tool calls from hanging forever when an API or parser is slow.",
        "logging": "Logging records tool calls, inputs, outputs, and errors for debugging and auditability.",
    }
    normalized = topic.strip().lower()
    if normalized not in knowledge_base:
        raise ToolValidationError(f"unknown topic: {topic}")
    return ToolResult(ok=True, data={"topic": normalized, "answer": knowledge_base[normalized]})


TOOLS: dict[str, Callable[..., ToolResult]] = {
    "calculator": calculator,
    "text_analyzer": text_analyzer,
    "unit_converter": unit_converter,
    "knowledge_lookup": knowledge_lookup,
}
