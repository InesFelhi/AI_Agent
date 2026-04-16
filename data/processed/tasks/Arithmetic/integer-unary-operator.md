# Integer Unary Operator

## Summary

- **Internal name**: `IntegerSingleOps`
- **Category**: Arithmetic
- **Purpose**: Apply a unary arithmetic operation on a single integer value and store the result in a workflow variable.
- **Task type**: Normal

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

The **Integer Unary Operator** task applies a single arithmetic operation to one integer operand (`var_n1`) and writes the result to a workflow variable (`ops_output`).

`var_n1` supports `$workflow_variable` references — resolved at runtime and parsed as an `int` before the operation is applied.

## Supported operations

The `arithmetic_ops` field is an **integer code** that selects the operation to apply.

- `arithmetic_ops` code: `1` | Operation: INCREMENT | Description: `var_n1 + 1`
- `arithmetic_ops` code: `2` | Operation: DECREMENT | Description: `var_n1 - 1`
- `arithmetic_ops` code: `3` | Operation: NEGATE | Description: `-var_n1`
- `arithmetic_ops` code: `4` | Operation: ABS | Description: `Math.abs(var_n1)` — absolute value

## Input parameters

- Parameter: `var_n1` | Type: Integer | Required: Yes | Possible values: Any integer — supports `$variable` references | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `0`
- Parameter: `arithmetic_ops` | Type: Integer | Required: Yes | Possible values: `1` (INC), `2` (DEC), `3` (NEG), `4` (ABS) | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: —

## Output parameters

- Field: `ops_output` | Type: Integer (as String) | Trigger condition: Always — on successful operation | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`

## Exceptions

- Code: `ARITHMETIC-OPS-001` | Trigger: The `arithmetic_ops` code does not match any supported operation

## Execution flowchart

Diagram Nodes:
- ResolveX: 🔄 Resolve var_n1\nfrom workflow context
- E1: ❌ ARITHMETIC-OPS-001\nUnknown operator
- IncrOp: var_n1 + 1
- DecrOp: var_n1 - 1
- NegOp: -var_n1
- AbsOp: Math.abs(var_n1)
- WriteOutput: 💾 Write result to ops_output

Workflow Flow:
- 🔄 Resolve var_n1\nfrom workflow context → ValidateOps
- var_n1 + 1 → 💾 Write result to ops_output
- var_n1 - 1 → 💾 Write result to ops_output
- -var_n1 → 💾 Write result to ops_output
- Math.abs(var_n1) → 💾 Write result to ops_output
- 💾 Write result to ops_output → Success
- ❌ ARITHMETIC-OPS-001\nUnknown operator → Error

**How it works:**

1. **Resolve operand**: `var_n1` is resolved from the workflow context and parsed as an `int`
2. **Validate operator**: if `arithmetic_ops` is unknown, throws `ARITHMETIC-OPS-001`
3. **Execute operation**: the corresponding arithmetic operation is applied
4. **Store result**: the result is written to `ops_output`
5. **Result**: returns `TaskIntegerResult` on success

## Code examples

### Example 1 — Increment a counter

```json
{
  "IntegerSingleOps": [
    {
      "id": "1",
      "title": "Increment counter",
      "var_n1": "$counter",
      "arithmetic_ops": 1,
      "ops_output": "$counter"
    }
  ]
}
```

Adds 1 to `$counter` and stores the result back in `$counter`.

### Example 2 — Get absolute value

```json
{
  "IntegerSingleOps": [
    {
      "id": "2",
      "title": "Absolute RTT",
      "var_n1": "$delta_ms",
      "arithmetic_ops": 4,
      "ops_output": "$abs_delta"
    }
  ]
}
```

Stores the absolute value of `$delta_ms` in `$abs_delta`.

### Example 3 — Negate a value

```json
{
  "IntegerSingleOps": [
    {
      "id": "3",
      "title": "Negate offset",
      "var_n1": "$offset",
      "arithmetic_ops": 3,
      "ops_output": "$neg_offset"
    }
  ]
}
```

## Input parameter details

### 1. Input parameter: `var_n1` — Operand

The integer value to operate on. Supports `$workflow_variable` references — resolved at runtime and parsed as an `int`.

- **Default**: `0`
- **Supports variables**: Yes

### 2. Input parameter: `arithmetic_ops` — Operation code

Integer code selecting the unary operation to apply to `var_n1`.

- Code: `1` | Name: INC | Operation: `var_n1 + 1`
- Code: `2` | Name: DEC | Operation: `var_n1 - 1`
- Code: `3` | Name: NEG | Operation: `-var_n1`
- Code: `4` | Name: ABS | Operation: `Math.abs(var_n1)`

- **Default**: — (required, no default — triggers `ARITHMETIC-OPS-001` if unknown)

## Output parameter details

### `ops_output` — Operation result

Workflow variable name to store the integer result. Must be declared in the **Start** task.

- Operation: INC | Value written: `var_n1 + 1`
- Operation: DEC | Value written: `var_n1 - 1`
- Operation: NEG | Value written: `-var_n1`
- Operation: ABS | Value written: `Math.abs(var_n1)`

- **Default**: `""` (result not stored if empty)

## Complete JSON example

```json
{
  "IntegerSingleOps": [
    {
      "id": "1",
      "title": "Increment iteration counter",
      "var_n1": "$counter",
      "arithmetic_ops": 1,
      "ops_output": "$counter"
    }
  ]
}
```