# Tasks Overview

## What is a Task?

A **task** is the fundamental execution unit in a workflow. Each task represents a single action performed on an Android device — executing a shell command, sending an HTTP request, comparing values, detecting errors, and more.

Tasks are the **nodes** of the workflow graph. The execution engine traverses this graph from the **START** node and runs each task in order until it reaches an **END** node.

## Two Types of Tasks

AndroMate distinguishes two categories of tasks, which differ in how they connect to the rest of the workflow.

### 1. Normal Tasks

A **normal task** performs a specific action and has exactly **one outgoing link**. Once it finishes, the engine unconditionally moves to the next task defined by the `"to"` field.

**Examples:** `CmdStage`, `HttpRequest`, `Sleep`, `TextReport`, `GetCurrentLocation`, `DnsLookup`, `SetVariable`, `NtpSync`, `ScreenAutomator`, etc.

**JSON link format:**

```json
{
  "from": "1",
  "to": "2"
}
```

**Execution flow:**

```
[Task 1] ──→ [Task 2] ──→ [Task 3] ──→ ...
```

#### Task Exceptions

Every normal task can raise an **exception** if something goes wrong (network failure, device error, timeout, invalid input, etc.). The runtime engine stores this exception in the execution context and associates it with the task that raised it.

An exception contains:

- Field: **Error code** | Description: A numeric or string identifier for the error type
- Field: **Description** | Description: A human-readable message explaining what went wrong
- Field: **Task ID** | Description: The ID of the task that failed

The workflow does **not** stop automatically on an exception (unless the execution policy is `STOP_ON_ERROR`). You can explicitly inspect the last exception using the dedicated conditional task: **`Exception ?`**.

### 2. Conditional Tasks

A **conditional task** evaluates a condition and returns a **boolean** result (`true` or `false`). Based on this result, the engine routes execution to one of **two different branches**.

**Examples:** `CompareStrings`, `CompareNumber`, `AndromateException`

**JSON link format:**

```json
{
  "from": "2",
  "true": "3",
  "false": "4"
}
```

**Meaning:**

- Condition in task `2` evaluates to `true` → execute task `3`
- Condition in task `2` evaluates to `false` → execute task `4`

**Execution flow:**

```
[Conditional Task]
    ├─→ TRUE  ──→ [Branch A]
    └─→ FALSE ──→ [Branch B]
```

#### Available Conditional Tasks

- JSON Key: `CompareStrings` | Display Name: Compare Strings | Description: Compares two string values
- JSON Key: `CompareNumber` | Display Name: Compare Number | Description: Compares two numeric values
- JSON Key: `AndromateException` | Display Name: Exception ? | Description: Checks if the previous task raised an exception

### The `Exception ?` Task (`AndromateException`)

The `Exception ?` task is a special conditional task dedicated to **error handling**. It inspects the execution context to determine whether the **last executed task** produced an exception.

- Returns **`true`** — the previous task failed (an exception was raised)
- Returns **`false`** — the previous task completed successfully (no exception)

Place it after any task that could fail to detect errors and branch accordingly. It can also **capture the exception details** into workflow variables for reporting or further processing:

- JSON Field: `code_output` | Description: Variable to store the error code
- JSON Field: `description_output` | Description: Variable to store the error description
- JSON Field: `task_id_output` | Description: Variable to store the ID of the failed task

**JSON example:**

```json
{
  "CmdStage": [
    {
      "id": "1",
      "title": "Run Ping",
      "cmd_text": "ping -c 1 8.8.8.8"
    }
  ],

  "AndromateException": [
    {
      "id": "2",
      "title": "Exception ?",
      "code_output": "$error_code",
      "description_output": "$error_desc",
      "task_id_output": "$failed_task_id"
    }
  ],

  "TextReport": [
    {
      "id": "3",
      "title": "Log Error",
      "texte": "Task $failed_task_id failed: [$error_code] $error_desc"
    },
    {
      "id": "4",
      "title": "Log Success",
      "texte": "Ping completed successfully"
    }
  ],

  "End": [{ "id": "100", "title": "End" }],

  "Links": [
    { "from": "0", "to": "1" },
    { "from": "1", "to": "2" },
    { "from": "2", "true": "3", "false": "4" },
    { "from": "3", "to": "100" },
    { "from": "4", "to": "100" }
  ]
}
```

## Workflow Execution as a Graph

Workflows are represented as **directed graphs**. The execution engine traverses them following this algorithm:

1. **Start** at the START node (entry point of the workflow)
2. **Execute** the current task
3. **Determine the next node:**
  - Normal task → follow the `"to"` link
  - Conditional task → evaluate the condition, then follow `"true"` or `"false"`
4. **Repeat** from step 2 with the next node
5. **Stop** when reaching an END node

The graph supports **loops** (a conditional task pointing back to an earlier task), useful for retry logic or polling. A maximum of **5000 iterations** is enforced to prevent infinite loops.

Diagram Nodes:
- T1: Normal Task 1
- T2: Normal Task 2
- T3: Branch A Task
- T4: Branch B Task

Workflow Flow:
- Normal Task 1 → Normal Task 2
- Normal Task 2 → COND
- Branch A Task → END
- Branch B Task → END

## Link Format Summary

- Task Type: **Normal Task** | JSON Fields: `"from"`, `"to"` | Outgoing Paths: 1 | Behaviour: Always continues to `"to"`
- Task Type: **Conditional Task** | JSON Fields: `"from"`, `"true"`, `"false"` | Outgoing Paths: 2 | Behaviour: Routes to `"true"` or `"false"` based on evaluation

### Associated Normal Link

Every **normal task** is connected with a normal link. It has exactly one outgoing path — the workflow always continues to `"to"` regardless of the task result.

```json
{ "from": "1", "to": "2" }
```

- Field: `"from"` | Description: ID of the current normal task
- Field: `"to"` | Description: ID of the next task to execute

### Associated Conditional Link

Every **conditional task** is connected with a conditional link. It has exactly two outgoing paths — the engine evaluates the boolean result and routes accordingly.

```json
{ "from": "2", "true": "3", "false": "4" }
```

- Field: `"from"` | Description: ID of the conditional task
- Field: `"true"` | Description: ID of the task to execute when the condition evaluates to `true`
- Field: `"false"` | Description: ID of the task to execute when the condition evaluates to `false`