# List Size

## Summary

- **Internal name**: `ListSize`
- **Category**: Collections
- **Purpose**: Get the number of elements in a list variable and store it in an output variable.
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

The **List Size** task reads the number of elements in a list variable and stores the integer result in the variable specified by `ops_output`. The list itself is **not modified**.

Typical usage: retrieve the size, then use it as the upper bound in an **Iterate** task or compare it with **Compare Number**.

## Input parameters

- Parameter: `list_variable_input` | Type: Variable reference | Required: Yes | Possible values: Declared variable starting with `$`, holding a valid list | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: —

## Output parameters

- Field: `ops_output` | Type: Integer | Condition: On success — number of elements in the list | Default: `0`

## Exceptions

- Code: `COLLECTION-TASK-002` | Exception Name: List Variable Name Invalid | Description: `list_variable_input` is empty or does not start with `$`.
- Code: `RESOLVE-VAR-005` | Exception Name: Resolve ArrayList Error | Description: The variable does not contain a valid JSON array string.

## Execution flowchart

Diagram Nodes:
- ResolveList: 🔄 Resolve list_variable_input
- E1: ❌ RESOLVE-VAR-005
- Size: size = list.size
- SetOutput: 💾 result.setVariable size\nstored via ops_output

Workflow Flow:
- 🔄 Resolve list_variable_input → CheckList
- size = list.size → 💾 result.setVariable size\nstored via ops_output
- 💾 result.setVariable size\nstored via ops_output → Success
- ❌ RESOLVE-VAR-005 → Error

**How it works:**

1. **Resolve list**: Fetches and parses the JSON array string from the execution context
2. **Get size**: Calls `list.size()`
3. **Store output**: Writes the integer size into the variable specified by `ops_output`
4. **Result**: Returns `TaskIntegerResult`

## Complete JSON example

```json
{
  "ListSize": [
    {
      "id": "7",
      "title": "Get list size",
      "list_variable_input": "$myList",
      "ops_output": "$listSize"
    }
  ]
}
```