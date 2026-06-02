from __future__ import annotations

import logging
import re
from typing import Any

from ai_agent.guardrails import check_prompt_safety
from ai_agent.schema import validate_agent_output
from ai_agent.tools import TOOLS, ToolResult


logger = logging.getLogger("agent")


class ToolCallingAgent:
    def run(self, prompt: str) -> dict[str, Any]:
        safety = check_prompt_safety(prompt)
        if safety["blocked"]:
            output = {
                "task": prompt,
                "plan": ["Check prompt safety", "Block unsafe request"],
                "tool_calls": [],
                "final_answer": "I cannot help with this request because it violates the safety guardrails.",
                "safety": safety,
                "success": False,
            }
            output["schema_errors"] = validate_agent_output(output)
            return output

        plan = self._plan(prompt)
        tool_calls = []
        final_parts = []

        for step in plan:
            tool_name = step["tool"]
            arguments = step["arguments"]
            result = self._call_tool(tool_name, arguments)
            tool_calls.append(
                {
                    "tool": tool_name,
                    "arguments": arguments,
                    "status": "success" if result.ok else "failed",
                    "result": result.data if result.ok else {"error": result.error},
                }
            )
            if result.ok:
                final_parts.append(self._summarize_tool_result(tool_name, result.data))
            else:
                final_parts.append(f"{tool_name} failed: {result.error}")

        if not plan:
            final_parts.append("No tool was needed. I can answer only supported calculator, text, conversion, and lookup tasks.")

        output = {
            "task": prompt,
            "plan": [step["reason"] for step in plan] or ["No matching tool selected"],
            "tool_calls": tool_calls,
            "final_answer": " ".join(final_parts),
            "safety": safety,
            "success": all(call["status"] == "success" for call in tool_calls) and bool(tool_calls),
        }
        output["schema_errors"] = validate_agent_output(output)
        logger.info("agent_output | output=%s", output)
        return output

    def _plan(self, prompt: str) -> list[dict[str, Any]]:
        lowered = prompt.lower()
        steps: list[dict[str, Any]] = []

        expression = self._extract_expression(prompt)
        if expression:
            steps.append(
                {
                    "tool": "calculator",
                    "arguments": {"expression": expression},
                    "reason": "Use calculator for arithmetic.",
                }
            )

        conversion = self._extract_conversion(prompt)
        if conversion:
            value, from_unit, to_unit = conversion
            steps.append(
                {
                    "tool": "unit_converter",
                    "arguments": {"value": value, "from_unit": from_unit, "to_unit": to_unit},
                    "reason": "Use unit_converter for unit conversion.",
                }
            )

        if "analyze" in lowered or "count words" in lowered or "text stats" in lowered:
            text = self._extract_quoted_text(prompt) or prompt
            steps.append(
                {
                    "tool": "text_analyzer",
                    "arguments": {"text": text},
                    "reason": "Use text_analyzer for word, sentence, and frequency statistics.",
                }
            )

        topic_aliases = {
            "agent": ["agent", "agents"],
            "json schema": ["json schema", "schema"],
            "retry": ["retry", "retries"],
            "timeout": ["timeout", "timeouts"],
            "logging": ["logging", "logs"],
        }
        for topic, aliases in topic_aliases.items():
            if any(alias in lowered for alias in aliases):
                steps.append(
                    {
                        "tool": "knowledge_lookup",
                        "arguments": {"topic": topic},
                        "reason": f"Use knowledge_lookup for the topic '{topic}'.",
                    }
                )
                break

        return steps

    def _call_tool(self, tool_name: str, arguments: dict[str, Any]) -> ToolResult:
        tool = TOOLS.get(tool_name)
        if tool is None:
            return ToolResult(ok=False, data={}, error=f"unknown tool: {tool_name}")
        return tool(**arguments)

    @staticmethod
    def _extract_expression(prompt: str) -> str | None:
        match = re.search(r"(?:calculate|what is|solve)\s+([0-9+\-*/(). ^]+)", prompt, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    @staticmethod
    def _extract_conversion(prompt: str) -> tuple[float, str, str] | None:
        match = re.search(
            r"convert\s+([0-9]+(?:\.[0-9]+)?)\s*(km|miles|kg|lb|c|f)\s+(?:to|in)\s+(km|miles|kg|lb|c|f)",
            prompt,
            re.IGNORECASE,
        )
        if not match:
            return None
        return float(match.group(1)), match.group(2), match.group(3)

    @staticmethod
    def _extract_quoted_text(prompt: str) -> str | None:
        match = re.search(r"['\"](.+?)['\"]", prompt)
        return match.group(1) if match else None

    @staticmethod
    def _summarize_tool_result(tool_name: str, data: dict[str, Any]) -> str:
        if tool_name == "calculator":
            return f"Calculator result: {data['expression']} = {data['value']}."
        if tool_name == "unit_converter":
            return f"Conversion result: {data['input_value']} {data['from_unit']} = {data['converted_value']} {data['to_unit']}."
        if tool_name == "text_analyzer":
            return f"Text stats: {data['words']} words, {data['sentences']} sentences, {data['characters']} characters."
        if tool_name == "knowledge_lookup":
            return data["answer"]
        return str(data)
