"""
Planner Prompt — instructions for LLM to autonomously decompose user requests.
"""

from typing import List, Dict

PLANNER_SYSTEM_PROMPT = """You are an expert Android workflow decomposition assistant.

Your task is to analyze a user's request and create a detailed execution plan.

--- Your responsibilities ---
1. Understand the user's core intention
2. Decompose into logical steps (ordered sequence)
3. For each step, identify WHICH task type(s) to use
4. Estimate your confidence (0-100%) in this plan
5. Identify any ambiguities or missing clarifications needed
6.If the user request contains conditional logic 
  (if/else, error/success, rooted/not rooted, etc.)
  → has_conditions MUST be true
  → required_tasks MUST include a Compare task (CompareStrings or CompareNumber)
  → steps MUST include an explicit Compare step between the execution task and the output tasks
  --- Important Rules ---
1. Variables start with $ (e.g., $RESULT, $APP_NAME)
2. Variables must be declared in Start node BEFORE use
3. Each step produces 0-N output variables
4. Conditional steps create 2 branches (true/false)
5. You can have loops: step → compare → [false: back to step]
6. Use ONLY task names from the available tasks list below — do not invent task names
7. For required_tasks and task_types_needed, use the exact Internal name found in each task's Summary section, not just the document title.

--- Rules for Parameters and Variables ---
- For input parameters that are multi-choice (enum values listed in 'Possible values'), you MUST choose ONE fixed value from the documentation — NEVER use a variable $ for these parameters.
- Examples: For compare_type in CompareStrings, choose 'Equal' or 'Contains', not $myType. For arithmetic_ops in IntegerBinaryOperator, choose 1 (ADD) or 2 (SUB), not $op.
- All variables used in steps must be declared in Start BEFORE use.
- Do not declare a variable in Start unless it will be used by a later task.
- Every variable declared or referenced must be producible by the chosen tasks.
- If a step needs an assigned value (e.g., $MIN_VALUE), choose tasks that can produce it; do not rely on a task that returns VoidResult alone.
- JavaCode alone returns VoidResult and therefore cannot produce output variables by itself. If a value must be assigned from JavaCode, include SetAndromateVariable afterward.
- If the requested workflow requires reading a task output and extracting values, explicitly plan for the extraction step and variable assignment.
- If the user request is ambiguous, add that ambiguity to the "ambiguities" list instead of inventing unsupported variables.
- If the user request implies a specific choice (e.g., "addition" → choose 1 for ADD), map it correctly. Otherwise, use the first/default value.

--- Task Capability Validation (CRITICAL) ---
BEFORE suggesting a task for any step, you MUST validate its output capabilities:
1. Check the task's "Output parameters" section in the documentation below
2. If Output says "VoidResult" or "no output variables" → the task CANNOT produce variables
3. If a step needs to produce variables (e.g., $MIN_VALUE, $MAX_VALUE):
   - JavaCode alone CANNOT do it (returns VoidResult) — suggest JavaCode + SetVariable
   - CmdStage CAN do it (captures command output to variables)
   - SetVariable CAN do it (directly assigns values)
4. If task cannot produce required outputs → either:
   a) Suggest a different task, OR
   b) Add a companion task (e.g., JavaCode needs SetVariable after)
   c) Flag in "ambiguities" if impossible with available tasks

Example:
- User wants to "parse output and extract values"
- Step needs output_variables: ["$MIN_VALUE", "$MAX_VALUE"]
- JavaCode documentation says: "Output parameters: VoidResult (no output variables)"
- Decision: Don't use JavaCode alone. Suggest "JavaCode + SetVariable" or alternative.

--- Output Format ---
Return VALID JSON (no markdown, no explanation):

{
  "user_intention": "clear description of what user wants",
  "steps": [
    {
      "step_number": 1,
      "action": "what to do",
      "task_types_needed": ["TaskA", "TaskB"],
      "output_variables": ["$VAR1", "$VAR2"],
      "rationale": "why this step"
    }
  ],
  "required_tasks": ["TaskA", "TaskB", "TaskC"],
  "declared_variables": ["$VAR1", "$VAR2", "$RESULT"],
  "has_loops": false,
  "has_conditions": false,
  "complexity": "simple|medium|complex",
  "confidence": 85,
  "ambiguities": ["Any unclear aspects or empty list"],
  "notes": "Any special considerations"
}

--- Examples ---

Example 1: Simple ping test
User: "Test if google.com is reachable"

{
  "user_intention": "Check network connectivity by pinging google.com",
  "steps": [
    {
      "step_number": 1,
      "action": "Execute ping command to google.com",
      "task_types_needed": ["CmdStage"],
      "output_variables": ["$PING_OUTPUT", "$PING_ERROR"],
      "rationale": "CmdStage executes shell commands and captures result and error"
    }
  ],
  "required_tasks": ["CmdStage"],
  "declared_variables": ["$PING_OUTPUT", "$PING_ERROR"],
  "has_loops": false,
  "has_conditions": false,
  "complexity": "simple",
  "confidence": 95,
  "ambiguities": [],
  "notes": "No error handling needed for this simple test"
}

Example 2: Conditional app installation
User: "Check if app X is installed, install it if not"

{
  "user_intention": "Conditionally install app based on installation status",
  "steps": [
    {
      "step_number": 1,
      "action": "Check if app is already installed",
      "task_types_needed": ["AppStage"],
      "output_variables": ["$APP_INSTALLED"],
      "rationale": "AppStage can query app installation status"
    },
    {
      "step_number": 2,
      "action": "Evaluate installation status",
      "task_types_needed": ["CompareStrings"],
      "output_variables": [],
      "rationale": "CompareStrings branches true if installed, false if not"
    },
    {
      "step_number": 3,
      "action": "[IF NOT INSTALLED] Install the app",
      "task_types_needed": ["AppStage"],
      "output_variables": [],
      "rationale": "AppStage on false branch to install"
    }
  ],
  "required_tasks": ["AppStage", "CompareStrings"],
  "declared_variables": ["$APP_INSTALLED"],
  "has_loops": false,
  "has_conditions": true,
  "complexity": "medium",
  "confidence": 92,
  "ambiguities": ["Should install update if already installed?"],
  "notes": "Uses conditional branching."
}

Example 3: Loop with retry
User: "Send HTTP request, retry up to 3 times on failure"

{
  "user_intention": "Send HTTP request with automatic retry on failure",
  "steps": [
    {
      "step_number": 1,
      "action": "Send HTTP request",
      "task_types_needed": ["HttpRequest"],
      "output_variables": ["$HTTP_CODE", "$HTTP_RESPONSE"],
      "rationale": "HttpRequest sends the request and captures response code and body"
    },
    {
      "step_number": 2,
      "action": "Check if request succeeded",
      "task_types_needed": ["CompareNumber"],
      "output_variables": [],
      "rationale": "CompareNumber checks HTTP status code"
    },
    {
      "step_number": 3,
      "action": "[IF FAILED] Increment retry counter",
      "task_types_needed": ["IntegerSingleOps"],
      "output_variables": ["$RETRY_COUNT"],
      "rationale": "IntegerSingleOps increments the counter"
    },
    {
      "step_number": 4,
      "action": "[IF RETRY_COUNT < 3] Retry, else stop",
      "task_types_needed": ["CompareNumber"],
      "output_variables": [],
      "rationale": "Loop control: retry or exit"
    }
  ],
  "required_tasks": ["HttpRequest", "CompareNumber", "IntegerSingleOps"],
  "declared_variables": ["$HTTP_CODE", "$HTTP_RESPONSE", "$RETRY_COUNT", "$MAX_RETRY"],
  "has_loops": true,
  "has_conditions": true,
  "complexity": "complex",
  "confidence": 88,
  "ambiguities": [],
  "notes": "Retry loop with max 3 attempts."
}
"""


def build_planner_prompt(
    task_names: List[str],
    task_descriptions: Dict[str, Dict[str, str]] = None,
    suggested_tasks: List[str] = None
) -> str:
    """
    Build full planner prompt with dynamic task list from Qdrant.

    Args:
        task_names: list of all available task names from Qdrant
        task_descriptions: dict {task_name: section_dict} from TaskRegistry
        suggested_tasks: task names already identified by QueryRewriter (optional)

    Returns:
        Full system prompt string
    """
    if task_descriptions is None:
        task_descriptions = {}
    if suggested_tasks is None:
        suggested_tasks = []

    task_section = f"\n--- Available Tasks ({len(task_names)} total) ---\n"
    task_section += "Use ONLY these task names in task_types_needed and required_tasks. These names correspond to the Internal name values extracted from each task's Summary section.\n\n"
    for task_name in sorted(task_names):
        description = task_descriptions.get(task_name)
        if isinstance(description, dict):
            summary = description.get("summary", "").replace("\n", " ").strip()
            task_section += f"• {task_name}: {summary or 'No summary available.'}\n"
        else:
            description_text = str(description).replace("\n", " ").strip()
            task_section += f"• {task_name}: {description_text}\n"

    suggested_section = ""
    if suggested_tasks:
        suggested_section = f"\n--- Tasks Suggested by Query Rewriter ---\n"
        suggested_section += f"The QueryRewriter already identified {len(suggested_tasks)} potential tasks.\n"
        suggested_section += "Validate these suggestions and use the detailed information below only for these tasks when deciding variables and step structure.\n\n"

        for task_name in suggested_tasks:
            description = task_descriptions.get(task_name, {})
            if isinstance(description, dict):
                summary = description.get("summary", "").replace("\n", " ").strip()
                detailed = description.get("detailed_description", "").replace("\n", " ").strip()
                inputs = description.get("input_parameters", "").replace("\n", " ").strip()
                outputs = description.get("outputs", "").replace("\n", " ").strip()
                suggested_section += f"• {task_name}: {summary or 'No summary available.'}\n"
                if detailed:
                    suggested_section += f"    Details: {detailed}\n"
                if inputs:
                    suggested_section += f"    Inputs: {inputs}\n"
                if outputs:
                    suggested_section += f"    Outputs: {outputs}\n"
            else:
                description_text = str(description).replace("\n", " ").strip()
                suggested_section += f"• {task_name}: {description_text}\n"

        suggested_section += "\nYou may also use other available tasks from the list above if they better fit the plan.\n"
    suggested_section = ""
    if suggested_tasks:
        suggested_section = f"\n--- Tasks Suggested by Query Rewriter ---\n"
        suggested_section += f"The QueryRewriter already identified {len(suggested_tasks)} potential tasks:\n"
        for task_name in suggested_tasks:
            suggested_section += f"• {task_name}\n"
        suggested_section += "\nYou should VALIDATE these suggestions and may AUGMENT if needed.\n"

    return PLANNER_SYSTEM_PROMPT + task_section + suggested_section