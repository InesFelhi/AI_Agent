# List Clear

## Summary

- **Internal name**: `ListClear`
- **Category**: Collections
- **Purpose**: Remove all elements from a list variable, resetting it to `[]`.
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

The **List Clear** task empties a list variable by replacing its content with `[]`. It is semantically equivalent to calling **Init List** on an existing variable, but expresses a **clearing** intent rather than an initialization.

Use it to reuse the same list variable across multiple iterations of a loop without re-declaring it in the Start node.

## Input parameters

- Parameter: `list_variable_input` | Type: Variable reference | Required: Yes | Possible values: Declared variable starting with `$`, holding a valid list | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: —

## Output parameters

None. The variable referenced by `list_variable_input` is reset to `[]`.

## Exceptions

- Code: `COLLECTION-TASK-002` | Exception Name: List Variable Name Invalid | Description: `list_variable_input` is empty or does not start with `$`.
- Code: `RESOLVE-VAR-005` | Exception Name: Resolve ArrayList Error | Description: The variable does not contain a valid JSON array string.

## Execution flowchart

Diagram Nodes:
- ResolveList: 🔄 Resolve list_variable_input
- E1: ❌ RESOLVE-VAR-005
- Store: 💾 setVariableValue\nvar ← [

Workflow Flow:
- 🔄 Resolve list_variable_input → CheckList
- 💾 setVariableValue\nvar ← [ → Success
- ❌ RESOLVE-VAR-005 → Error

**How it works:**

1. **Resolve list**: Fetches and parses the JSON array string from the execution context
2. **Clear**: Stores an empty `ArrayList<String>` serialized as `[]` back into the context
3. **Result**: Returns `VoidResult`

## Complete JSON example

```json
{
  "ListClear": [
    {
      "id": "8",
      "title": "Clear list",
      "list_variable_input": "$myList"
    }
  ]
}
```