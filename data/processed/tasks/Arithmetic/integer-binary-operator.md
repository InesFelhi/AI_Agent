# Integer Binary Operator

## Summary

- **Internal name**: `IntegerBinaryOps`
- **Category**: Arithmetic
- **Purpose**: Apply a binary arithmetic operation on two integer values and store the result in a workflow variable.
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

The **Integer Binary Operator** task applies an arithmetic operation between two integer operands (`var_n1` and `var_n2`) and writes the result to a workflow variable (`ops_output`).

Both `var_n1` and `var_n2` support `$workflow_variable` references — resolved at runtime and parsed as `int` values before the operation is performed. Division (`DIV`) and modulo (`MOD`) perform **integer arithmetic** (fractional part discarded). Both throw `ARITHMETIC-OPS-002` if `var_n2` is `0`.

## Supported operations

The `arithmetic_ops` field is an **integer code** that selects the operation to apply between `var_n1` and `var_n2`.

- `arithmetic_ops` code: `1` | Operation: ADD | Description: `var_n1 + var_n2`
- `arithmetic_ops` code: `2` | Operation: SUB | Description: `var_n1 - var_n2`
- `arithmetic_ops` code: `3` | Operation: MUL | Description: `var_n1 × var_n2`
- `arithmetic_ops` code: `4` | Operation: DIV | Description: `var_n1 ÷ var_n2` (integer division)
- `arithmetic_ops` code: `5` | Operation: MOD | Description: `var_n1 % var_n2` (remainder)
- `arithmetic_ops` code: `6` | Operation: POW | Description: `var_n1 ^ var_n2` (power)

## Input parameters

- Parameter: `var_n1` | Type: Integer | Required: Yes | Possible values: Any integer — supports `$variable` references | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `0`
- Parameter: `var_n2` | Type: Integer | Required: Yes | Possible values: Any integer — supports `$variable` references | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `0`
- Parameter: `arithmetic_ops` | Type: Integer | Required: Yes | Possible values: `1` (ADD), `2` (SUB), `3` (MUL), `4` (DIV), `5` (MOD), `6` (POW) | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: —

## Output parameters

- Field: `ops_output` | Type: Integer (as String) | Trigger condition: Always — on successful operation | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`

## Exceptions

- Code: `ARITHMETIC-OPS-001` | Trigger: The `arithmetic_ops` code does not match any supported operation
- Code: `ARITHMETIC-OPS-002` | Trigger: `var_n2` is `0` and the operation is `DIV` (code 4) or `MOD` (code 5) — division by zero

## Execution flowchart

Diagram Nodes:
- ResolveAll: 🔄 Resolve var_n1 and var_n2\nfrom workflow context
- E1: ❌ ARITHMETIC-OPS-001\nUnknown operator
- AddOp: var_n1 + var_n2
- SubOp: var_n1 - var_n2
- MulOp: var_n1 × var_n2
- E2: ❌ ARITHMETIC-OPS-002\nDivision by zero
- DivOp: var_n1 ÷ var_n2
- ModOp: var_n1 % var_n2
- PowOp: var_n1 ^ var_n2
- WriteOutput: 💾 Write result to ops_output

Workflow Flow:
- 🔄 Resolve var_n1 and var_n2\nfrom workflow context → ValidateOps
- var_n1 + var_n2 → 💾 Write result to ops_output
- var_n1 - var_n2 → 💾 Write result to ops_output
- var_n1 × var_n2 → 💾 Write result to ops_output
- var_n1 ÷ var_n2 → 💾 Write result to ops_output
- var_n1 % var_n2 → 💾 Write result to ops_output
- var_n1 ^ var_n2 → 💾 Write result to ops_output
- 💾 Write result to ops_output → Success
- ❌ ARITHMETIC-OPS-001\nUnknown operator → Error
- ❌ ARITHMETIC-OPS-002\nDivision by zero → Error

**How it works:**

1. **Resolve operands**: `var_n1` and `var_n2` are resolved from the workflow context and parsed as `int`
2. **Validate operator**: if `arithmetic_ops` is unknown, throws `ARITHMETIC-OPS-001`
3. **Check for division by zero**: for DIV and MOD, if `var_n2` is `0`, throws `ARITHMETIC-OPS-002`
4. **Execute operation**: the corresponding arithmetic operation is applied
5. **Store result**: the result is written to `ops_output`
6. **Result**: returns `TaskIntegerResult` on success

## Code examples

### Example 1 — Add two values

```json
{
  "IntegerBinaryOps": [
    {
      "id": "1",
      "title": "Total latency",
      "var_n1": "$dns_rtt",
      "var_n2": "$http_rtt",
      "arithmetic_ops": 1,
      "ops_output": "$total_rtt"
    }
  ]
}
```

Stores `$dns_rtt + $http_rtt` in `$total_rtt`.

### Example 2 — Compute difference

```json
{
  "IntegerBinaryOps": [
    {
      "id": "2",
      "title": "RTT delta",
      "var_n1": "$current_rtt",
      "var_n2": "$baseline_rtt",
      "arithmetic_ops": 2,
      "ops_output": "$rtt_delta"
    }
  ]
}
```

Stores `$current_rtt - $baseline_rtt` in `$rtt_delta`.

### Example 3 — Integer division

```json
{
  "IntegerBinaryOps": [
    {
      "id": "3",
      "title": "Average RTT",
      "var_n1": "$total_rtt",
      "var_n2": "$sample_count",
      "arithmetic_ops": 4,
      "ops_output": "$avg_rtt"
    }
  ]
}
```

Stores `$total_rtt ÷ $sample_count` (integer division) in `$avg_rtt`.

### Example 4 — Power

```json
{
  "IntegerBinaryOps": [
    {
      "id": "4",
      "title": "Power of two",
      "var_n1": "2",
      "var_n2": "$exponent",
      "arithmetic_ops": 6,
      "ops_output": "$result"
    }
  ]
}
```

Stores `2 ^ $exponent` in `$result`.

## Input parameter details

### 1. Input parameter: `var_n1` — Left operand

The left-hand integer operand. Supports `$workflow_variable` references — resolved at runtime and parsed as an `int`.

- **Default**: `0`
- **Supports variables**: Yes

### 2. Input parameter: `var_n2` — Right operand

The right-hand integer operand. Supports `$workflow_variable` references — resolved at runtime and parsed as an `int`.

**Warning**: must not be `0` when using DIV (code 4) or MOD (code 5) — throws `ARITHMETIC-OPS-002`.

- **Default**: `0`
- **Supports variables**: Yes

### 3. Input parameter: `arithmetic_ops` — Operation code

Integer code selecting the binary operation to apply between `var_n1` and `var_n2`.

- Code: `1` | Name: ADD | Operation: `var_n1 + var_n2` | Notes: —
- Code: `2` | Name: SUB | Operation: `var_n1 - var_n2` | Notes: —
- Code: `3` | Name: MUL | Operation: `var_n1 × var_n2` | Notes: —
- Code: `4` | Name: DIV | Operation: `var_n1 ÷ var_n2` | Notes: Integer division — fractional part discarded
- Code: `5` | Name: MOD | Operation: `var_n1 % var_n2` | Notes: Remainder of integer division
- Code: `6` | Name: POW | Operation: `var_n1 ^ var_n2` | Notes: Power (exponentiation)

- **Default**: — (required, no default — triggers `ARITHMETIC-OPS-001` if unknown)

## Output parameter details

### `ops_output` — Operation result

Workflow variable name to store the integer result. Must be declared in the **Start** task.

- Operation: ADD | Value written: `var_n1 + var_n2`
- Operation: SUB | Value written: `var_n1 - var_n2`
- Operation: MUL | Value written: `var_n1 × var_n2`
- Operation: DIV | Value written: `var_n1 ÷ var_n2` (integer)
- Operation: MOD | Value written: `var_n1 % var_n2`
- Operation: POW | Value written: `var_n1 ^ var_n2`

- **Default**: `""` (result not stored if empty)

## Complete JSON example

```json
{
  "IntegerBinaryOps": [
    {
      "id": "1",
      "title": "Compute average RTT",
      "var_n1": "$total_rtt",
      "var_n2": "$sample_count",
      "arithmetic_ops": 4,
      "ops_output": "$avg_rtt"
    }
  ]
}
```