# Init List

## Summary

- **Internal name**: `InitList`
- **Category**: Collections
- **Purpose**: Initialize a workflow variable to an empty list (`[]`).
- **Task type**: Normal

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

The **Init List** task resets a workflow variable to an empty `ArrayList<String>`, stored as `[]` in the execution context.

The variable **must be declared** in the **Start** node's variables list before using `InitList`. The task does not create a new variable — it resets the value of an existing one.

This is typically the first step in a Collections workflow: declare the variable in Start, call `InitList` to clear it, then use `ListAdd`, `ListGet`, etc.

## Input parameters

- Parameter: `list_variable_input` | Type: Variable reference | Required: Yes | Possible values: Declared variable starting with `$` | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: —

## Output parameters

None. The variable referenced by `list_variable_input` is set to `[]` in the execution context.

## Exceptions

- Code: `COLLECTION-TASK-002` | Exception Name: List Variable Name Invalid | Description: `list_variable_input` is empty or does not start with `$`. A valid variable reference is required.
- Code: `WORKFLOW-RUNTIME-002` | Exception Name: Variable Not Defined in Runtime | Description: The variable was not declared in the Start node. Declare it first.

## Execution flowchart

Diagram Nodes:
- ReadInput: 📋 Read list_variable_input\nno resolution applied
- E1: ❌ COLLECTION-TASK-002
- E2: ❌ WORKFLOW-RUNTIME-002
- Store: 💾 setVariableValue\nvar ← [

Workflow Flow:
- 📋 Read list_variable_input\nno resolution applied → CheckEmpty
- 💾 setVariableValue\nvar ← [ → Success
- ❌ COLLECTION-TASK-002 → Error
- ❌ WORKFLOW-RUNTIME-002 → Error

**How it works:**

1. **Read `list_variable_input`**: Loads the variable name as a literal string — no resolution applied
2. **Validation**: Raises `COLLECTION-TASK-002` if empty or not a `$`-prefixed reference
3. **Declaration check**: Raises `WORKFLOW-RUNTIME-002` if the variable was not declared in Start
4. **Store**: Writes an empty `ArrayList<String>` serialized as `[]` into the execution context
5. **Result**: Returns `VoidResult`

## Input parameter details

### 1. Input parameter: `list_variable_input`

The name of the list variable to initialize. Must be declared in the **Start** node.

#### Example

```json
"list_variable_input": "$myList"
```

#### Details

- Must start with `$`.
- The value is read **as-is** — no variable resolution is applied to this field.
- The variable must have been declared in the `variables` array of the Start node.

## Complete JSON example

```json
{
  "Start": [{ "id": "0", "title": "Start", "variables": [
    { "variableName": "$myList", "variableValue": "" }
  ]}],

  "InitList": [
    { "id": "1", "title": "Init List", "list_variable_input": "$myList" }
  ],

  "End": [{ "id": "99", "title": "End" }],

  "Links": [
    { "from": "0", "to": "1" },
    { "from": "1", "to": "99" }
  ]
}
```