# List Remove At

## Summary

- **Internal name**: `ListRemoveAt`
- **Category**: Collections
- **Purpose**: Remove the element at a given index from a list variable.
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

The **List Remove At** task removes the element at position `index_input` (zero-based) from a list variable. All elements after the removed one are shifted one position to the left.

If the index is out of bounds (negative or ≥ list size), the task throws `COLLECTION-TASK-001`.

## Input parameters

- Parameter: `list_variable_input` | Type: Variable reference | Required: Yes | Possible values: Declared variable starting with `$`, holding a valid list | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: —
- Parameter: `index_input` | Type: Integer / Variable | Required: Yes | Possible values: Zero-based index; must be `0 ≤ index < size` | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `0`

## Output parameters

None. The variable referenced by `list_variable_input` is updated with the element removed.

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
- Remove: list.remove index
- Store: 💾 setVariableValue\nvar ← updated list

Workflow Flow:
- 🔄 Resolve list_variable_input → CheckList
- 🔄 Resolve index_input → CheckBounds
- list.remove index → 💾 setVariableValue\nvar ← updated list
- 💾 setVariableValue\nvar ← updated list → Success
- ❌ RESOLVE-VAR-005 → Error
- ❌ COLLECTION-TASK-001 → Error

## Complete JSON example

```json
{
  "ListRemoveAt": [
    {
      "id": "5",
      "title": "Remove first element",
      "list_variable_input": "$myList",
      "index_input": "0"
    }
  ]
}
```