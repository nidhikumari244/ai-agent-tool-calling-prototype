# AI Agent Tool-Calling Prototype

A small Python CLI prototype for an AI Agent Development internship application. The agent plans tool calls, executes validated tool wrappers, returns structured JSON output, applies basic guardrails, and includes a 10-prompt test harness.

## Features

- Tool-using agent workflow with plan, tool calls, observations, and final answer
- Tool wrappers for:
  - arithmetic calculation
  - text analysis
  - unit conversion
  - local knowledge lookup
- Retries, timeout-style bounded execution, validation, and logging around tool calls
- Guardrails for unsafe prompts
- Structured JSON output with schema validation
- Mini test harness with 10 prompts and pass/fail reporting
- Standard-library only Python project

## Project Structure

```text
ai-agent-tool-calling-prototype/
  ai_agent/
    agent.py
    cli.py
    guardrails.py
    logging_config.py
    schema.py
    test_harness.py
    tools.py
  logs/
    .gitkeep
  README.md
  requirements.txt
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

No third-party packages are required.

## Run Examples

Run a calculator prompt:

```bash
python -m ai_agent.cli run "Calculate 25 * 4 + 10"
```

Run a unit conversion:

```bash
python -m ai_agent.cli run "Convert 10 km to miles"
```

Run text analysis:

```bash
python -m ai_agent.cli run "Analyze text 'Agents call tools. Tools return results.'"
```

Run a knowledge lookup:

```bash
python -m ai_agent.cli run "Explain JSON schema"
```

Run the test harness:

```bash
python -m ai_agent.test_harness
```

## Output Format

The agent returns JSON:

```json
{
  "task": "Calculate 25 * 4 + 10",
  "plan": ["Use calculator for arithmetic."],
  "tool_calls": [
    {
      "tool": "calculator",
      "arguments": {"expression": "25 * 4 + 10"},
      "status": "success",
      "result": {"expression": "25 * 4 + 10", "value": 110.0}
    }
  ],
  "final_answer": "Calculator result: 25 * 4 + 10 = 110.0.",
  "safety": {
    "blocked": false,
    "reason": "Prompt passed basic safety checks."
  },
  "success": true,
  "schema_errors": []
}
```

## Logging

Logs are written to `logs/agent.log` by default. The test harness writes to `logs/test_harness.log`.

## Assumptions

- This is a lightweight prototype, so planning is rule-based instead of using a paid LLM API.
- The focus is on agent engineering fundamentals: planning, tool wrappers, validation, structured output, guardrails, logging, and testing.
- The calculator intentionally supports only safe arithmetic syntax.
