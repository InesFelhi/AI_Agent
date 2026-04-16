# JSON Object Operation

## Summary

- **Internal name**: `JsonObjectOperation`
- **Category**: Tools
- **Purpose**: Perform read or write operations (GET, SIZE, PUT\_SET, REMOVE, CLEAR) on a JSON object stored in a workflow variable.
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

The **JSON Object Operation** task operates on a JSON object (`jo_input`) stored as a workflow variable. It supports five operations selected by an integer code (`jo_ops`):

- `jo_ops` code: `1` | Operation: `SIZE` | Description: Returns the number of keys in the JSON object
- `jo_ops` code: `2` | Operation: `GET` | Description: Returns the value of the key specified in `jo_param`
- `jo_ops` code: `3` | Operation: `PUT_SET` | Description: Sets or updates the key `jo_param` with the value `jo_value`
- `jo_ops` code: `4` | Operation: `REMOVE` | Description: Removes the key `jo_param` and returns the removed value
- `jo_ops` code: `5` | Operation: `CLEAR` | Description: Replaces the JSON object with an empty `{}`

**Mutation operations** (`PUT_SET`, `REMOVE`, `CLEAR`) modify the JSON object in-place and write the updated object back to the workflow context — the original variable is updated.

**Read operations** (`GET`, `SIZE`) do not modify the object.

## Input parameters

- Parameter: `jo_input` | Type: JSONObject | Required: Yes | Possible values: JSONObject workflow variable reference (e.g. `$my_json`) | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `{}`
- Parameter: `jo_ops` | Type: Integer | Required: Yes | Possible values: `1` (SIZE) / `2` (GET) / `3` (PUT_SET) / `4` (REMOVE) / `5` (CLEAR) | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: —
- Parameter: `jo_param` | Type: String | Required: No | Possible values: Any string key — required for GET, PUT_SET, REMOVE — supports `$variable` | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `""`
- Parameter: `jo_value` | Type: String | Required: No | Possible values: Any string — required for PUT_SET — supports `$variable` references | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `""`

## Output parameters

- Field: `value_output` | Type: String | Trigger condition: Written when the operation produces a result (SIZE, GET, PUT_SET, REMOVE) — not written for CLEAR | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`

**What is written to `value_output` per operation:**

- Operation: `SIZE` | Value written: Number of keys in the JSON object (as a string)
- Operation: `GET` | Value written: The value of the requested key (as a string)
- Operation: `PUT_SET` | Value written: The new value that was set
- Operation: `REMOVE` | Value written: The value that was removed
- Operation: `CLEAR` | Value written: Nothing written

**Note:** `value_output` is only written if the workflow variable already exists in the execution context (declared in the **Start** task).

## Exceptions

- Code: `JO-OPERATION-001` | Exception Name: Unknown Operation | Description: The `jo_ops` code does not match any supported operation. Accepted codes: `1`, `2`, `3`, `4`, `5`.
- Code: `JO-OPERATION-002` | Exception Name: JSON Object Exception | Description: A JSON error occurred — key not found (for GET or REMOVE), or another JSON parsing error.
- Code: `ERROR-000` | Exception Name: Other Error | Description: An unexpected runtime error occurred during execution.

## Execution flowchart

The following diagram illustrates the actual implementation based on the Android code:

Diagram Nodes:
- ResolveAll: 🔄 Resolve jo_input, jo_param, jo_value\nfrom workflow context
- E1: ❌ JO-OPERATION-001
- SizeOp: 📐 count keys\nreturn length
- E2: ❌ JO-OPERATION-002\nKey not found
- GetOp: 📖 read value\nreturn value
- PutOp: ✏️ set key = jo_value\nupdate object in context\nreturn new value
- RemoveOp: 🗑️ remove key\nupdate object in context\nreturn removed value
- ClearOp: 🧹 replace with empty object\nupdate object in context
- WriteOutput: 💾 Write result to value_output

Workflow Flow:
- 🔄 Resolve jo_input, jo_param, jo_value\nfrom workflow context → ValidateOps
- 📐 count keys\nreturn length → 💾 Write result to value_output
- 📖 read value\nreturn value → 💾 Write result to value_output
- ✏️ set key = jo_value\nupdate object in context\nreturn new value → 💾 Write result to value_output
- 🗑️ remove key\nupdate object in context\nreturn removed value → 💾 Write result to value_output
- 🧹 replace with empty object\nupdate object in context → Success
- 💾 Write result to value_output → Success
- ❌ JO-OPERATION-001 → Error
- ❌ JO-OPERATION-002\nKey not found → Error

**How it works:**

1. **Resolve parameters**: `jo_input`, `jo_param`, and `jo_value` are resolved from the workflow context
2. **Validate operation**: if `jo_ops` code is unknown, throws `JO-OPERATION-001`
3. **Execute operation**:
  - `SIZE`: counts the keys, writes count to `value_output`
  - `GET`: reads the value of `jo_param`, throws `JO-OPERATION-002` if key absent
  - `PUT_SET`: sets `jo_param = jo_value`, updates object in workflow context
  - `REMOVE`: removes `jo_param`, updates object in workflow context, throws `JO-OPERATION-002` if key absent
  - `CLEAR`: replaces object with `{}`, updates in workflow context
4. **Result**: writes output to `value_output` and returns `StrTaskResult`

## Code examples

### Example 1 — GET a value from a JSON object

```json
{
  "JsonObjectOperation": [
    {
      "id": "1",
      "title": "Read status field",
      "jo_input": "$response_json",
      "jo_ops": 2,
      "jo_param": "status",
      "value_output": "$status_value"
    }
  ]
}
```

Reads the `"status"` key from `$response_json` and stores its value in `$status_value`.

### Example 2 — SIZE of a JSON object

```json
{
  "JsonObjectOperation": [
    {
      "id": "2",
      "title": "Count fields",
      "jo_input": "$my_json",
      "jo_ops": 1,
      "value_output": "$field_count"
    }
  ]
}
```

Counts the number of top-level keys in `$my_json` and stores it in `$field_count`.

### Example 3 — PUT\_SET a key

```json
{
  "JsonObjectOperation": [
    {
      "id": "3",
      "title": "Set result field",
      "jo_input": "$report_json",
      "jo_ops": 3,
      "jo_param": "ping_result",
      "jo_value": "$ping_output",
      "value_output": "$set_result"
    }
  ]
}
```

Sets `"ping_result"` to the value of `$ping_output` in `$report_json`. Updates `$report_json` in the workflow context.

### Example 4 — REMOVE a key

```json
{
  "JsonObjectOperation": [
    {
      "id": "4",
      "title": "Remove temp field",
      "jo_input": "$my_json",
      "jo_ops": 4,
      "jo_param": "tmp",
      "value_output": "$removed_value"
    }
  ]
}
```

Removes the `"tmp"` key from `$my_json`. Returns the removed value in `$removed_value`.

### Example 5 — CLEAR a JSON object

```json
{
  "JsonObjectOperation": [
    {
      "id": "5",
      "title": "Reset JSON",
      "jo_input": "$my_json",
      "jo_ops": 5
    }
  ]
}
```

Replaces `$my_json` with an empty `{}`.

## Input parameter details

### 1. Input parameter: `jo_input`

Reference to the workflow variable that holds the JSON object to operate on. Must be declared as a JSONObject variable in the **Start** task (e.g. `variableValue: "{}"`). Mutation operations (PUT_SET, REMOVE, CLEAR) write the modified object back to this variable in the workflow context.

- **Default**: `{}` (empty object)
- **Supports variables**: Yes

### 2. Input parameter: `jo_ops`

Integer code selecting the operation to perform on the JSON object.

- Code: `1` | Operation: `SIZE` | Mutates object?: No | Writes to `value_output`?: Yes — number of keys
- Code: `2` | Operation: `GET` | Mutates object?: No | Writes to `value_output`?: Yes — value of `jo_param`
- Code: `3` | Operation: `PUT_SET` | Mutates object?: Yes | Writes to `value_output`?: Yes — the new value set
- Code: `4` | Operation: `REMOVE` | Mutates object?: Yes | Writes to `value_output`?: Yes — the removed value
- Code: `5` | Operation: `CLEAR` | Mutates object?: Yes | Writes to `value_output`?: No

- **Default**: — (required, no default — triggers `JO-OPERATION-001` if unknown)

### 3. Input parameter: `jo_param`

The JSON object key to operate on. Required for GET, PUT_SET, and REMOVE. Ignored for SIZE and CLEAR. Supports `$variable` references.

- **Default**: `""`
- **Supports variables**: Yes

### 4. Input parameter: `jo_value`

The value to assign to `jo_param` when using PUT_SET. Ignored for all other operations. Supports `$variable` references. Always stored as a String.

- **Default**: `""`
- **Supports variables**: Yes

## Output parameter details

### 1. Result variable: `value_output`

Stores the string result of the operation in the specified workflow variable.

- Operation: `SIZE` | Value written: Number of top-level keys (e.g. `"3"`)
- Operation: `GET` | Value written: Value of the key `jo_param` (as string)
- Operation: `PUT_SET` | Value written: The new value that was set
- Operation: `REMOVE` | Value written: The value that was removed
- Operation: `CLEAR` | Value written: *(not written)*

The variable is only updated if it already exists in the workflow context (declared in the Start task).

## Complete JSON example

```json
{
  "JsonObjectOperation": [
    {
      "id": "1",
      "title": "Store ping result in JSON",
      "jo_input": "$report_json",
      "jo_ops": 3,
      "jo_param": "ping_result",
      "jo_value": "$ping_output",
      "value_output": "$set_result"
    }
  ]
}
```