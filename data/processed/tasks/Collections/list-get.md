# List Get

## Summary

- **Internal name**: `ListGet`
- **Category**: Collections
- **Purpose**: Read the element at a given index from a list variable and store it in an output variable.
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

The **List Get** task reads the string element at position `index_input` (zero-based) and stores it in the variable `value_output`. The list itself is **not modified**.

## Input parameters

- Parameter: `list_variable_input` | Type: Variable reference | Required: Yes | Possible values: Declared variable starting with `$`, holding a valid list | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: —
- Parameter: `index_input` | Type: Integer / Variable | Required: Yes | Possible values: Zero-based index; must be `0 ≤ index < size` | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `0`

## Output parameters

- Field: `value_output` | Type: String | Condition: On success — the element at `index_input` | Default: `<ANDROMATE_NULL_VALUE>`

## Exceptions

- Code: `COLLECTION-TASK-001` | Exception Name: List Variable Not a List | Description: Index is out of bounds — negative or ≥ list size.
- Code: `COLLECTION-TASK-002` | Exception Name: List Variable Name Invalid | Description: `list_variable_input` is empty or does not start with `$`.
- Code: `RESOLVE-VAR-005` | Exception Name: Resolve ArrayList Error | Description: The variable does not contain a valid JSON array string.

## Execution flowchart

Diagram Nodes:
- ResolveList: 🔄 Resolve list_variable_input
- E1: ❌ RESOLVE-VAR-005
- ResolveIndex: 🔄 Resolve index_input
- E2: ❌ COLLECTION-TASK-001
- Get: element = list.get index
- SetOutput: 💾 result.setOutputStr element\nstored via value_output

Workflow Flow:
- 🔄 Resolve list_variable_input → CheckList
- 🔄 Resolve index_input → CheckBounds
- element = list.get index → 💾 result.setOutputStr element\nstored via value_output
- 💾 result.setOutputStr element\nstored via value_output → Success
- ❌ RESOLVE-VAR-005 → Error
- ❌ COLLECTION-TASK-001 → Error

**How it works:**

1. **Resolve list**: Fetches and parses the JSON array string from the execution context
2. **Resolve index**: Evaluates `index_input` — supports `$variable` references
3. **Bounds check**: Raises `COLLECTION-TASK-001` if out of bounds
4. **Get element**: Reads `list.get(index)`
5. **Store output**: Writes the element into the variable specified by `value_output`
6. **Result**: Returns `StrTaskResult`

## Complete JSON example

```json
{
  "ListGet": [
    {
      "id": "6",
      "title": "Read first element",
      "list_variable_input": "$myList",
      "index_input": "0",
      "value_output": "$firstElement"
    }
  ]
}
```