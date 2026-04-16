# Compare Number

## Summary

- **Internal name**: `CompareNumber`
- **Category**: Tools
- **Purpose**: Compare two numeric values using a configurable comparison operator and return a boolean result.
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

The **Compare Number** task compares two numeric values (`num_x` and `num_y`) using a specified comparison operator. It returns `true` or `false` and routes execution to the corresponding branch in the workflow graph.

Both `num_x` and `num_y` support `$workflow_variable` references — they are resolved at runtime and parsed as `double` values before the comparison is performed. Default value for both is `0`.

## Comparison operators

The `compare_type` field is an **integer code** that determines how `num_x` is compared against `num_y`.

- `compare_type` code: `1` | Operator: `==` | Condition: `num_x` is equal to `num_y`
- `compare_type` code: `2` | Operator: `>` | Condition: `num_x` is strictly greater than `num_y`
- `compare_type` code: `3` | Operator: `<` | Condition: `num_x` is strictly less than `num_y`
- `compare_type` code: `4` | Operator: `>=` | Condition: `num_x` is greater than or equal to `num_y`
- `compare_type` code: `5` | Operator: `<=` | Condition: `num_x` is less than or equal to `num_y`

## Input parameters

- Parameter: `num_x` | Type: Double | Required: Yes | Possible values: Any numeric value — supports `$variable` references | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `0`
- Parameter: `num_y` | Type: Double | Required: Yes | Possible values: Any numeric value — supports `$variable` references | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `0`
- Parameter: `compare_type` | Type: Integer | Required: Yes | Possible values: `1` (==) / `2` (>) / `3` (<) / `4` (>=) / `5` (<=) | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: —

## Output parameters

This task is a **conditional task** — it produces no output variables. The boolean result controls the execution branch:

- Result: `true` | Condition: Comparison condition is satisfied | Branch taken: `"true"` link
- Result: `false` | Condition: Comparison condition is not satisfied | Branch taken: `"false"` link

## Exceptions

- Code: `COMPARE-VAR-001` | Exception Name: Unsupported Compare Type | Description: The value provided in `compare_type` does not match any supported operator code. Accepted codes: `1` (==), `2` (>), `3` (<), `4` (>=), `5` (<=).

## Execution flowchart

The following diagram illustrates the actual implementation based on the Android code:

Diagram Nodes:
- ReadType: 📋 Read compare_type integer code
- E1: ❌ COMPARE-VAR-001
- ResolveX: 🔄 Resolve num_x\nfrom workflow context
- ResolveY: 🔄 Resolve num_y\nfrom workflow context
- EqualOp: num_x == num_y
- SupOp: num_x > num_y
- InfOp: num_x < num_y
- EqualSupOp: num_x >= num_y
- EqualInfOp: num_x <= num_y

Workflow Flow:
- 📋 Read compare_type integer code → ValidateType
- 🔄 Resolve num_x\nfrom workflow context → 🔄 Resolve num_y\nfrom workflow context
- 🔄 Resolve num_y\nfrom workflow context → Eval
- num_x == num_y → Result
- num_x > num_y → Result
- num_x < num_y → Result
- num_x >= num_y → Result
- num_x <= num_y → Result
- ❌ COMPARE-VAR-001 → Error

**How it works:**

1. **Read operator**: `compare_type` integer code is read from the task JSON
2. **Validate**: if the code is unknown, throws `COMPARE-VAR-001`
3. **Resolve operands**: `num_x` and `num_y` are resolved from the workflow context and parsed as `double`
4. **Execute comparison**: the corresponding numeric comparison is applied
5. **Return result**: `true` or `false` — the workflow engine routes to the corresponding branch

## Code examples

### Example 1 — Equality check

```json
{
  "CompareNumber": [
    {
      "id": "1",
      "title": "HTTP 200?",
      "num_x": "$http_status",
      "num_y": "200",
      "compare_type": 1
    }
  ]
}
```

Returns `true` if `$http_status` equals `200`.

### Example 2 — Less than

```json
{
  "CompareNumber": [
    {
      "id": "2",
      "title": "RTT acceptable?",
      "num_x": "$rtt_ms",
      "num_y": "500",
      "compare_type": 3
    }
  ]
}
```

Returns `true` if `$rtt_ms` is strictly less than `500`.

### Example 3 — Greater than or equal

```json
{
  "CompareNumber": [
    {
      "id": "3",
      "title": "Signal strong enough?",
      "num_x": "$signal_dbm",
      "num_y": "-80",
      "compare_type": 4
    }
  ]
}
```

Returns `true` if `$signal_dbm` is greater than or equal to `-80`.

## Input parameter details

### 1. Input parameter: `num_x`

The left-hand numeric operand. Supports `$workflow_variable` references — resolved at runtime and parsed as a `double` before comparison.

- **Default**: `0`
- **Supports variables**: Yes

### 2. Input parameter: `num_y`

The right-hand numeric operand. Supports `$workflow_variable` references — resolved at runtime and parsed as a `double` before comparison.

- **Default**: `0`
- **Supports variables**: Yes

### 3. Input parameter: `compare_type`

An integer code that selects the numeric comparison to apply between `num_x` and `num_y`.

- Code: `1` | Operator: `==` | Condition: `num_x` equals `num_y`
- Code: `2` | Operator: `>` | Condition: `num_x` strictly greater than `num_y`
- Code: `3` | Operator: `<` | Condition: `num_x` strictly less than `num_y`
- Code: `4` | Operator: `>=` | Condition: `num_x` greater than or equal to `num_y`
- Code: `5` | Operator: `<=` | Condition: `num_x` less than or equal to `num_y`

- **Default**: — (required, no default — triggers `COMPARE-VAR-001` if unknown code)

## Complete JSON example

```json
{
  "CompareNumber": [
    {
      "id": "1",
      "title": "Check RTT below threshold",
      "num_x": "$rtt_ms",
      "num_y": "100",
      "compare_type": 3
    }
  ]
}
```