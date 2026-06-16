# List Add

## Summary

- **Internal name**: `ListAdd`
- **Category**: Collections
- **Purpose**: Append a string value to the end of a list variable.
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

The **List Add** task appends a string value to the end of an existing list variable. The list grows by one element on each call.

Both `list_variable_input` and `value_input` support `$variable` interpolation — `value_input` can be a literal string, a variable reference, or a mixed expression such as `"item_$index"`.

The list variable must have been previously initialized with **Init List**.

## Input parameters

- Parameter: `list_variable_input` | Type: Variable reference | Required: Yes | Possible values: Declared variable starting with `$`, holding a valid list | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: —
- Parameter: `value_input` | Type: String / Variable | Required: Yes | Possible values: Literal string or `$variable` reference | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `""`

## Output parameters

None. The variable referenced by `list_variable_input` is updated with the new element appended.

## Exceptions

- Code: `COLLECTION-TASK-002` | Exception Name: List Variable Name Invalid | Description: `list_variable_input` is empty or does not start with `$`.
- Code: `RESOLVE-VAR-005` | Exception Name: Resolve ArrayList Error | Description: The variable does not contain a valid JSON array string.

## Execution flowchart

Diagram Nodes:
- ResolveList: 🔄 Resolve list_variable_input\nfetch ArrayList from context
- E1: ❌ RESOLVE-VAR-005
- ResolveValue: 🔄 Resolve value_input\nreplace $refs
- Add: list.add value
- Store: 💾 setVariableValue\nvar ← updated list

Workflow Flow:
- 🔄 Resolve list_variable_input\nfetch ArrayList from context → CheckList
- 🔄 Resolve value_input\nreplace $refs → list.add value
- list.add value → 💾 setVariableValue\nvar ← updated list
- 💾 setVariableValue\nvar ← updated list → Success
- ❌ RESOLVE-VAR-005 → Error

**How it works:**

1. **Resolve list**: Fetches and parses the JSON array string from the execution context
2. **Resolve value**: Evaluates `value_input` — `$variable` references are replaced with their current values
3. **Append**: Calls `list.add(resolvedValue)`
4. **Store**: Serializes the updated list back as a JSON array string and writes it to the context
5. **Result**: Returns `VoidResult`

## Complete JSON example

```json
{
  "InitList": [{ "id": "1", "title": "Init", "list_variable_input": "$myList" }],
  "ListAdd": [
    { "id": "2", "title": "Add hello", "list_variable_input": "$myList", "value_input": "hello" },
    { "id": "3", "title": "Add from var", "list_variable_input": "$myList", "value_input": "$item" }
  ]
}
```