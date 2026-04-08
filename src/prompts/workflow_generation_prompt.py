from string import Template

WORKFLOW_GENERATION_INSTRUCTIONS = """
You are an expert automation assistant for Android workflows.

--- Instructions ---
- Generate a valid workflow JSON strictly following these rules:
  1. There must be exactly one "Start" node with id "-1000".
  2. Task nodes (CmdStage, AppStage, etc.) must use ids starting at "-1001" and decrementing (-1001, -1002, ...).
  3. End nodes must use ids lower than any task id (e.g., "-2000"), and you can have one or more End nodes.
  4. Each task type (CmdStage, AppStage, etc.) can be empty if not used.
  5. "Links" must connect valid ids from Start/Stages/End.
  6. Start node must include a "variables" array where each variable name starts with "$".
  7. All variable names used in workflow stages must begin with "$" (e.g., "$PING_RESULT").
  8. Do not include any explanation, comment or markdown.
  9. Output must be valid strict JSON only.

--- Multi-task composition ---
A workflow commonly chains multiple tasks together. Follow these patterns:

Pattern 1 — Execute then check result:
  Start(-1000) → Task(-1001) → Compare(-1002) → [true: End(-2000) | false: End(-2001)]

Pattern 2 — Execute with retry loop:
  Start(-1000) → Task(-1001) → Compare(-1002) → [true: End(-2000) | false: Increment(-1003)]
                                                                          ↓
                                                          CheckLimit(-1004) → [true: End(-2000) | false: Task(-1001)]

Pattern 3 — Chain multiple tasks sequentially:
  Start(-1000) → Task1(-1001) → Task2(-1002) → Task3(-1003) → End(-2000)

Rules for multi-task workflows:
- Variables used as output of one task and input of another MUST be declared in Start.
- Every node except End MUST have at least one outgoing link in Links.
- Conditional links (true/false) are used after Compare nodes only.
- Unconditional links (to) are used after execution tasks (CmdStage, IntegerSingleOps, etc.).
- You can have multiple End nodes for different exit paths (success, error, max retry reached).
"""

CANONICAL_EXAMPLE = """
--- Canonical example (study this carefully) ---
{
  "Start": [
    {
      "id": "-1000",
      "variables": [
        {"variableName": "$SITE_TEST",        "variableValue": "www.google.com", "is_kpi": false},
        {"variableName": "$ICMP_COUNT",       "variableValue": "5",              "is_kpi": false},
        {"variableName": "$ICMP_INTERVAL_MS", "variableValue": "1000",           "is_kpi": false},
        {"variableName": "$PING_RESULT",      "variableValue": "",               "is_kpi": false},
        {"variableName": "$PING_ERROR",       "variableValue": "",               "is_kpi": false},
        {"variableName": "$RETRY_INDEX",      "variableValue": "0",              "is_kpi": false},
        {"variableName": "$MAX_RETRY",        "variableValue": "5",              "is_kpi": false}
      ],
      "exec_policy": "1"
    }
  ],
  "CmdStage": [
    {
      "id": "-1001",
      "cmd_text": "ping -c $ICMP_COUNT -i $ICMP_INTERVAL_MS $SITE_TEST",
      "cmd_result_output": "$PING_RESULT",
      "cmd_error_output": "$PING_ERROR",
      "commands": [null]
    }
  ],
  "CompareStrings": [
    {
      "id": "-1002",
      "var_x": "$PING_ERROR",
      "var_y": "\\"\\"",
      "compare_type": "Equal"
    }
  ],
  "IntegerSingleOps": [
    {
      "id": "-1003",
      "arithmetic_ops": 1,
      "var_n1": "$RETRY_INDEX",
      "ops_output": "$RETRY_INDEX"
    }
  ],
  "CompareNumber": [
    {
      "id": "-1004",
      "num_x": "$RETRY_INDEX",
      "num_y": "$MAX_RETRY",
      "compare_type": 4
    }
  ],
  "End": [
    {"id": "-2000"}
  ],
  "Links": [
    {"from": "-1000", "to": "-1001"},
    {"from": "-1001", "to": "-1002"},
    {"from": "-1002", "true": "-2000", "false": "-1003"},
    {"from": "-1003", "to": "-1004"},
    {"from": "-1004", "true": "-2000", "false": "-1001"}
  ]
}
"""

WORKFLOW_GENERATION_SYSTEM = f"""
{WORKFLOW_GENERATION_INSTRUCTIONS}
{CANONICAL_EXAMPLE}
"""

WORKFLOW_GENERATION_USER = Template("""
Context:
$context

User instruction:
$instruction
""")


def build_workflow_generation_prompt(
    context: str,
    instruction: str,
    examples: str = "",  # kept for backward compatibility, ignored
) -> tuple[str, str]:
    system = WORKFLOW_GENERATION_SYSTEM
    user = WORKFLOW_GENERATION_USER.safe_substitute(
        context=context.strip() if context else "No task documentation available.",
        instruction=instruction.strip(),
    )
    return system, user