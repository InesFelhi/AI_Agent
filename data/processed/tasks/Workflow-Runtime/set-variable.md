# Set Variable

## Summary

- **Internal name**: `SetAndromateVariable`
- **Category**: Workflow Runtime
- **Purpose**: Assign a new value to an existing workflow variable at runtime.
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

The **Set Variable** task updates the value of a workflow variable during execution. It allows dynamic modification of any variable that was declared in the **Start** node.

It is used to:

- Reset a variable to a fixed or computed value
- Copy the value of one variable into another
- Update a counter or accumulator between iterations
- Override an initial value based on a condition result

The task handles:

- validation that the target is a properly declared variable,
- resolution of the new value against the current execution context (other `$variables` are replaced with their current values),
- update of the variable in the shared `AndroMateContext`.

## Input parameters

- Parameter: `variable_input` | Type: String | Required: Yes | Possible values: A declared variable name starting with `$` | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: —
- Parameter: `variable_value` | Type: String | Required: Yes | Possible values: Any string value, may contain `$variable` references | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `""`

## Output parameters

The Set Variable task produces no outputs. It modifies the execution context directly and returns immediately.

## Exceptions

- Code: `WORKFLOW-RUNTIME-001` | Exception Name: Empty Variable Input | Description: `variable_input` is empty or null. A valid variable name starting with `$` is required.
- Code: `WORKFLOW-RUNTIME-002` | Exception Name: Non-Variable Input | Description: `variable_input` does not start with `$`. Only declared variables can be targeted.
- Code: `WORKFLOW-RUNTIME-002` | Exception Name: Variable Not Defined in Runtime | Description: The variable referenced in `variable_input` was not declared in the Start node. Declare it first.

## Execution flowchart

Diagram Nodes:
- ReadInput: 📋 Read variable_input\nno resolution applied
- E1: ❌ WORKFLOW-RUNTIME-001\nSET_EMPTY_VARIABLE
- E2: ❌ WORKFLOW-RUNTIME-002\nSET_NON_VARIABLE
- E3: ❌ WORKFLOW-RUNTIME-002\nNO_VARIABLE_DEFINED_IN_RUNTIME
- ResolveValue: 🔄 Resolve variable_value\nreplace $refs with current values
- SetValue: 💾 androMateContext.setVariableValue\nvariable_input ← resolved value

Workflow Flow:
- 📋 Read variable_input\nno resolution applied → CheckEmpty
- 🔄 Resolve variable_value\nreplace $refs with current values → 💾 androMateContext.setVariableValue\nvariable_input ← resolved value
- 💾 androMateContext.setVariableValue\nvariable_input ← resolved value → Success
- ❌ WORKFLOW-RUNTIME-001\nSET_EMPTY_VARIABLE → Error
- ❌ WORKFLOW-RUNTIME-002\nSET_NON_VARIABLE → Error
- ❌ WORKFLOW-RUNTIME-002\nNO_VARIABLE_DEFINED_IN_RUNTIME → Error

**How it works:**

1. **Read `variable_input`**: Loads the target variable name as a literal string — no variable resolution is applied at this stage
2. **Empty check**: Raises `WORKFLOW-RUNTIME-001` if the input is empty or null
3. **Variable format check**: Raises `WORKFLOW-RUNTIME-002` if the input does not start with `$`
4. **Declaration check**: Raises `WORKFLOW-RUNTIME-002` if the variable was not declared in the Start node
5. **Resolve `variable_value`**: Evaluates the new value — any `$variable` references inside are replaced with their current runtime values
6. **Update context**: Writes the resolved value into `AndroMateContext` for the target variable
7. **Result**: Returns `VoidResult` — the variable is now updated for all subsequent tasks

**Legend:**

- 🔵 **Blue**: Start
- 🟢 **Green**: Success
- 🔴 **Red**: Exceptions
- 🟡 **Yellow**: Resolution
- 💾 **Green**: Context update

## Input parameter details

### 1. Input parameter: `variable_input`

The name of the variable to update. Must be a variable declared in the **Start** node.

#### Example

```json
"variable_input": "$my_counter"
```

#### Details

- Must start with `$`.
- The value is read **as-is** — no variable resolution is applied to this field. You must write the literal variable name (e.g. `$result`), not a reference to another variable that holds a name.
- The variable must have been declared in the `variables` array of the Start node.

### 2. Input parameter: `variable_value`

The new value to assign to the variable. Can be a static string or contain references to other `$variables`.

#### Example — static value

```json
"variable_value": "hello world"
```

#### Example — copy from another variable

```json
"variable_value": "$cmd_output"
```

#### Example — mixed

```json
"variable_value": "status: $http_status at $server_url"
```

#### Details

- Variable references (`$name`) inside this field are resolved at runtime before assignment.
- The resolved value is always stored as a **string** in the context.

## Complete JSON example

```json
{
  "SetAndromateVariable": [
    {
      "id": "3",
      "title": "Set Variable",
      "variable_input": "$my_result",
      "variable_value": "$cmd_output"
    }
  ]
}
```