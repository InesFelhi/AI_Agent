# Start

## Summary

- **Internal name**: `Start`
- **Category**: Workflow Control
- **Purpose**: Mark the beginning of a workflow execution, initialize the execution context (variables, timeout, execution policy).
- **Task type**: Workflow Control

## Compatibility

- **Minimum AndroMate version**: `{{ ANDROMATE_FIRST_VERSION }}`
- **Maximum AndroMate version**: `{{ ANDROMATE_CURRENT_VERSION }}`
- **Minimum Android**: `{{ ANDROMATE_MIN_APP_SDK }}`
- **Maximum Android tested**: `{{ ANDROID_CURRENT_APP_SDK }}`
- **Supported manufacturers**:
  - ✅ All manufacturers
- **Required permissions**:
  - None

## Detailed description

The **Start** task is the mandatory entry point of every workflow. There is always exactly **one Start node** per workflow, and graph traversal begins from it.

It is used to:

- Define the **initial variables** available throughout the entire workflow
- Configure the **global timeout** for the workflow execution
- Set the **execution policy** — whether the workflow stops or continues when a task raises an exception

The Start task itself performs no action during execution (it returns immediately). Its role is purely **declarative**: it configures the runtime context (`AndroMateContext`) that all subsequent tasks will share.

## Input parameters

- Parameter: `Time_out` | Type: Long | Required: No | Possible values: Duration in milliseconds, `0` = no timeout | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `0`
- Parameter: `exec_policy` | Type: Integer | Required: No | Possible values: `1` = Continue on error, `2` = Stop on error | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `1` (Continue)
- Parameter: `variables` | Type: Array | Required: No | Possible values: List of variable objects (see below) | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `[]`

### Variable object structure

Each entry in the `variables` array defines one workflow variable:

- Field: `variableName` | Type: String | Required: Yes | Description: Name of the variable — must start with `$` (e.g. `$my_var`)
- Field: `variableValue` | Type: String | Required: No | Description: Initial value of the variable
- Field: `is_kpi` | Type: Boolean | Required: No | Description: If `true`, this variable is tracked as a KPI and included in the job result

## Output parameters

The Start task produces no outputs. It returns immediately with no result value.

## Exceptions

The Start task does not raise any exceptions.

## Execution flowchart

Diagram Nodes:
- B: 📋 Read Time_out\ndefault: 0
- C: 📋 Read exec_policy\n1=CONTINUE / 2=STOP
- D: 📋 Read variables array
- E: 🔧 Initialize AndroMateContext\nvariables · timeout · policy
- F: 📌 Set graph entry point\nstartId = node id

Workflow Flow:
- 📋 Read Time_out\ndefault: 0 → 📋 Read exec_policy\n1=CONTINUE / 2=STOP
- 📋 Read exec_policy\n1=CONTINUE / 2=STOP → 📋 Read variables array
- 📋 Read variables array → 🔧 Initialize AndroMateContext\nvariables · timeout · policy
- 🔧 Initialize AndroMateContext\nvariables · timeout · policy → 📌 Set graph entry point\nstartId = node id
- 📌 Set graph entry point\nstartId = node id → G

**How it works:**

1. **Read `Time_out`**: Loads the global workflow timeout in milliseconds (`0` = no limit)
2. **Read `exec_policy`**: Loads the execution policy — `CONTINUE_ON_ERROR` (default) or `STOP_ON_ERROR`
3. **Read `variables`**: Loads the variable list with their initial values and KPI flags
4. **Initialize context**: Creates the `AndroMateContext` shared by all tasks in the workflow
5. **Set entry point**: Registers this node's `id` as the graph traversal starting point
6. **Workflow begins**: The engine starts executing the next connected task

## Parameter details

### 1. Parameter: `Time_out`

Defines the maximum execution time allowed for the entire workflow, in milliseconds.

#### Example

```json
"Time_out": 60000
```

#### Details

- A value of `0` means **no timeout** — the workflow runs until it reaches an END node or an unrecoverable error.
- If the workflow exceeds this duration, execution is interrupted.
- Recommended for long-running workflows to prevent infinite loops or blocking tasks.

### 2. Parameter: `exec_policy`

Defines the behaviour of the engine when a task raises an exception.

- Value: `1` | Constant: `CONTINUE_ON_ERROR` | Behaviour: The workflow continues to the next task even if the current one failed. The exception is stored in context and can be inspected with the `Exception ?` task.
- Value: `2` | Constant: `STOP_ON_ERROR` | Behaviour: The workflow stops immediately when any task raises an exception.

#### Example

```json
"exec_policy": 2
```

#### Details

- Default value is `1` (`CONTINUE_ON_ERROR`) when the field is absent or set to an unknown value.
- With `CONTINUE_ON_ERROR`, you can use `Exception ?` nodes after critical tasks to handle errors explicitly.
- With `STOP_ON_ERROR`, any task failure terminates the workflow immediately — no branching needed.

### 3. Parameter: `variables`

Declares the list of variables available for the entire workflow. Each variable can be read or written by any task.

#### Variable fields

- Field: `variableName` | Description: Unique name starting with `$`. Used as a placeholder in task parameters (e.g. `$url`, `$result`).
- Field: `variableValue` | Description: Initial value as a string. Can be empty `""`.
- Field: `is_kpi` | Description: If `true`, this variable's final value is exported in the job report as a KPI metric.

#### Example

```json
"variables": [
  {
    "variableName": "$server_url",
    "variableValue": "https://example.com",
    "is_kpi": false
  },
  {
    "variableName": "$ping_result",
    "variableValue": "",
    "is_kpi": true
  }
]
```

#### Details

- Variables are resolved at runtime — any task parameter containing `$variable_name` is automatically replaced with the current value.
- A variable not declared in the Start node cannot be used in other tasks.
- KPI variables (`is_kpi: true`) are collected at the end of the job and sent to the backend as performance indicators.

## Complete JSON example

```json
{
  "Start": [
    {
      "id": "0",
      "title": "Initialize Workflow",
      "Time_out": 120000,
      "exec_policy": 1,
      "variables": [
        {
          "variableName": "$server_url",
          "variableValue": "https://example.com/api",
          "is_kpi": false
        },
        {
          "variableName": "$http_status",
          "variableValue": "",
          "is_kpi": true
        },
        {
          "variableName": "$error_code",
          "variableValue": "",
          "is_kpi": false
        }
      ]
    }
  ]
}
```