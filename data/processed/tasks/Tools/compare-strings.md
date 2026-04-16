# Compare Strings

## Summary

- **Internal name**: `CompareStrings`
- **Category**: Tools
- **Purpose**: Compare two string values using a configurable comparison operator and return a boolean result.
- **Task type**: Conditional

## Compatibility

- **Minimum AndroMate version**: `{{ ANDROMATE_FIRST_VERSION }}`
- **Maximum AndroMate version**: `{{ ANDROMATE_CURRENT_VERSION }}`
- **Minimum Android**: `{{ ANDROMATE_MIN_APP_SDK }}`
- **Maximum Android tested**: `{{ ANDROID_CURRENT_APP_SDK }}`
- **Supported manufacturers**:
  - ✅ Samsung (One UI 6.x / 7.x / 8.x)
  - ✅ Google Pixel (Android Stock)
  - ⚠️ Other manufacturers — **not tested**
- **Required permissions**:
  - None

## Detailed description

The **Compare Strings** task compares two string values (`var_x` and `var_y`) using a specified comparison operator. It returns `true` or `false` and routes execution to the corresponding branch in the workflow graph.

Both `var_x` and `var_y` support `$workflow_variable` references — they are resolved at runtime before the comparison is performed.

## Comparison operators

The `compare_type` field determines how `var_x` is compared against `var_y`.

- `compare_type` value: `"Equal"` | Operator: `==` | Description: `var_x` is exactly equal to `var_y` (case-sensitive)
- `compare_type` value: `"Equal ignore case"` | Operator: `==` (case-insensitive) | Description: `var_x` equals `var_y`, ignoring letter case
- `compare_type` value: `"Contains"` | Operator: `contains` | Description: `var_x` contains the substring `var_y`
- `compare_type` value: `"Start with"` | Operator: `startsWith` | Description: `var_x` starts with the prefix `var_y`

## Input parameters

- Parameter: `var_x` | Type: String | Required: Yes | Possible values: Any string — supports `$variable` references | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `""`
- Parameter: `var_y` | Type: String | Required: Yes | Possible values: Any string — supports `$variable` references | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `""`
- Parameter: `compare_type` | Type: String | Required: Yes | Possible values: `"Equal"` / `"Equal ignore case"` / `"Contains"` / `"Start with"` | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `""`

## Output parameters

This task is a **conditional task** — it produces no output variables. The boolean result controls the execution branch:

- Result: `true` | Condition: Comparison condition is satisfied | Branch taken: `"true"` link
- Result: `false` | Condition: Comparison condition is not satisfied | Branch taken: `"false"` link

## Exceptions

- Code: `COMPARE-VAR-001` | Exception Name: Unsupported Compare Type | Description: The value provided in `compare_type` does not match any supported operator. Accepted values: `"Equal"`, `"Equal ignore case"`, `"Contains"`, `"Start with"`.

## Execution flowchart

The following diagram illustrates the actual implementation based on the Android code:

Diagram Nodes:
- ResolveX: 🔄 Resolve var_x\nfrom workflow context
- ResolveY: 🔄 Resolve var_y\nfrom workflow context
- EqualOp: var_x.equals(var_y)
- IgnoreCaseOp: var_x.equalsIgnoreCase(var_y)
- ContainsOp: var_x.contains(var_y)
- StartWithOp: var_x.startsWith(var_y)
- E1: ❌ COMPARE-VAR-001

Workflow Flow:
- 🔄 Resolve var_x\nfrom workflow context → 🔄 Resolve var_y\nfrom workflow context
- 🔄 Resolve var_y\nfrom workflow context → ParseType
- var_x.equals(var_y) → Result
- var_x.equalsIgnoreCase(var_y) → Result
- var_x.contains(var_y) → Result
- var_x.startsWith(var_y) → Result
- ❌ COMPARE-VAR-001 → Error

**How it works:**

1. **Resolve operands**: `var_x` and `var_y` are resolved from the workflow context (replacing `$variable` references)
2. **Parse operator**: `compare_type` is matched against the supported string values
3. **Execute comparison**: the appropriate Java String method is called
4. **Return result**: `true` or `false` — the workflow engine routes to the corresponding branch

## Code examples

### Example 1 — Exact equality check

```json
{
  "CompareStrings": [
    {
      "id": "1",
      "title": "Check status",
      "var_x": "$http_status",
      "var_y": "200",
      "compare_type": "Equal"
    }
  ]
}
```

Returns `true` if `$http_status` is exactly `"200"`.

### Example 2 — Case-insensitive check

```json
{
  "CompareStrings": [
    {
      "id": "2",
      "title": "Check keyword (case-insensitive)",
      "var_x": "$response_body",
      "var_y": "success",
      "compare_type": "Equal ignore case"
    }
  ]
}
```

Returns `true` if `$response_body` equals `"success"` regardless of letter case.

### Example 3 — Substring check

```json
{
  "CompareStrings": [
    {
      "id": "3",
      "title": "Check for error keyword",
      "var_x": "$cmd_output",
      "var_y": "unreachable",
      "compare_type": "Contains"
    }
  ]
}
```

Returns `true` if `$cmd_output` contains the word `"unreachable"`.

### Example 4 — Prefix check

```json
{
  "CompareStrings": [
    {
      "id": "4",
      "title": "Check prefix",
      "var_x": "$device_model",
      "var_y": "Samsung",
      "compare_type": "Start with"
    }
  ]
}
```

Returns `true` if `$device_model` starts with `"Samsung"`.

## Input parameter details

### 1. Input parameter: `var_x`

The left-hand string operand of the comparison. Supports `$workflow_variable` references — resolved at runtime before the comparison.

- **Default**: `""` (empty string)
- **Supports variables**: Yes

### 2. Input parameter: `var_y`

The right-hand string operand of the comparison. Supports `$workflow_variable` references — resolved at runtime before the comparison.

- **Default**: `""` (empty string)
- **Supports variables**: Yes

### 3. Input parameter: `compare_type`

Determines which string comparison method is applied. Must match one of the supported string values exactly (case-insensitive).

- Value: `"Equal"` | Java method: `var_x.equals(var_y)` | Behaviour: Exact case-sensitive equality
- Value: `"Equal ignore case"` | Java method: `var_x.equalsIgnoreCase(var_y)` | Behaviour: Case-insensitive equality
- Value: `"Contains"` | Java method: `var_x.contains(var_y)` | Behaviour: `var_x` contains `var_y` as a substring
- Value: `"Start with"` | Java method: `var_x.startsWith(var_y)` | Behaviour: `var_x` starts with `var_y`

- **Default**: `""` — triggers `COMPARE-VAR-001` if not set

## Complete JSON example

```json
{
  "CompareStrings": [
    {
      "id": "1",
      "title": "Check if response contains success",
      "var_x": "$response_body",
      "var_y": "success",
      "compare_type": "Contains"
    }
  ]
}
```