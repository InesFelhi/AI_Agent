# Exception ?

## Summary

- **Internal name**: `AndromateException`
- **Category**: Workflow Runtime
- **Purpose**: Check whether the last executed task raised an exception, and optionally capture its error details into variables.
- **Task type**: Conditional

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

The **Exception ?** task inspects the execution context to determine whether the **last executed task** produced an exception. It is a **conditional task**: it evaluates to `true` or `false` and routes the workflow into one of two branches accordingly.

It is used to:

- Detect failures in the previous task without stopping the workflow
- Branch into an error-handling path or a success path
- Capture the error code, description, and failing task ID for reporting
- Build resilient workflows that recover from task errors

The task handles:

- reading the last exception state from the shared `AndroMateContext`,
- evaluating the boolean result (`true` = error, `false` = no error),
- optionally writing exception details into declared workflow variables.

## Input parameters

This task has no input parameters. It reads the exception state directly from the execution context.

## Output parameters

The output variables are **optional**. If a variable name is provided and the variable was declared in the Start node, its value is updated after execution.

- Field: `code_output` | Type: String | Condition: When the previous task failed | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`
- Field: `description_output` | Type: String | Condition: When the previous task failed | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`
- Field: `task_id_output` | Type: String | Condition: When the previous task failed | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`

## Exceptions

The Exception ? task does not raise any exceptions of its own.

## Execution flowchart

Diagram Nodes:
- ReadCtx: 📋 Read AndroMateContext\ngetLastExceptionDto
- SetTrue: conditionResult = true\nException detected
- SetFalse: conditionResult = false\nNo exception
- UpdateVars: 💾 Update output variables\nif declared in context:\ncode_output\ndescription_output\ntask_id_output

Workflow Flow:
- 📋 Read AndroMateContext\ngetLastExceptionDto → Evaluate
- conditionResult = true\nException detected → 💾 Update output variables\nif declared in context:\ncode_output\ndescription_output\ntask_id_output
- conditionResult = false\nNo exception → ReturnFalse
- 💾 Update output variables\nif declared in context:\ncode_output\ndescription_output\ntask_id_output → ReturnTrue

**How it works:**

1. **Read context**: Retrieves the last exception DTO from `AndroMateContext`
2. **Evaluate**: Calls `lastTaskHasError()` — returns `true` if the previous task failed, `false` otherwise
3. **Update variables** *(only on true)*: If output variable names are provided and declared in Start, writes the error code, description, and failing task ID into them
4. **Route**: The graph engine reads the boolean result and follows the `"true"` or `"false"` link

## Output parameter details

### 1. Output variable: `code_output`

Stores the error code of the exception raised by the previous task.

#### Example

```json
"code_output": "$error_code"
```

#### Details

- Only populated when the condition result is `true` (previous task failed).
- The variable must have been declared in the Start node.

### 2. Output variable: `description_output`

Stores the human-readable description of the exception.

#### Example

```json
"description_output": "$error_desc"
```

### 3. Output variable: `task_id_output`

Stores the ID of the task that raised the exception.

#### Example

```json
"task_id_output": "$failed_task_id"
```

#### Details

- Useful to identify which task failed when multiple tasks precede this check.

## Complete JSON example

```json
{
  "AndromateException": [
    {
      "id": "2",
      "title": "Exception ?",
      "code_output": "$error_code",
      "description_output": "$error_desc",
      "task_id_output": "$failed_task_id"
    }
  ]
}
```