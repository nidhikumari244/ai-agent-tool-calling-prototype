from __future__ import annotations

from typing import Any


REQUIRED_OUTPUT_FIELDS = {
    "task": str,
    "plan": list,
    "tool_calls": list,
    "final_answer": str,
    "safety": dict,
    "success": bool,
}

REQUIRED_TOOL_CALL_FIELDS = {
    "tool": str,
    "arguments": dict,
    "status": str,
    "result": dict,
}


def validate_agent_output(output: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    for field, expected_type in REQUIRED_OUTPUT_FIELDS.items():
        if field not in output:
            errors.append(f"missing field: {field}")
        elif not isinstance(output[field], expected_type):
            errors.append(f"{field} must be {expected_type.__name__}")

    for index, call in enumerate(output.get("tool_calls", [])):
        if not isinstance(call, dict):
            errors.append(f"tool_calls[{index}] must be object")
            continue
        for field, expected_type in REQUIRED_TOOL_CALL_FIELDS.items():
            if field not in call:
                errors.append(f"tool_calls[{index}] missing field: {field}")
            elif not isinstance(call[field], expected_type):
                errors.append(f"tool_calls[{index}].{field} must be {expected_type.__name__}")

        if call.get("status") not in {"success", "failed"}:
            errors.append(f"tool_calls[{index}].status must be success or failed")

    safety = output.get("safety", {})
    if isinstance(safety, dict):
        if "blocked" not in safety or not isinstance(safety.get("blocked"), bool):
            errors.append("safety.blocked must be bool")
        if "reason" not in safety or not isinstance(safety.get("reason"), str):
            errors.append("safety.reason must be string")

    return errors
