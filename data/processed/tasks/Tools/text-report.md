# Text Report

## Summary

- **Internal name**: `TextReport`
- **Category**: Tools
- **Purpose**: Write a labelled text message to the AndroMate execution report with a specified display type (Info, Title, or Error).
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

The **Text Report** task writes a message to the AndroMate execution report during workflow execution. The message is resolved from the `texte` field (supports `$workflow_variable` references) and rendered according to the display type set in `texte_type`.

Three display types are available:

- `texte_type` value: `"Info Text"` | Display type: Informational | Effect: Adds a standard info-level message to the report
- `texte_type` value: `"Title Text"` | Display type: Title / Header | Effect: Adds a title or section header to the report
- `texte_type` value: `"Error Text"` | Display type: Error | Effect: Adds an error-styled message to the report

**Note:** Any value of `texte_type` other than the three listed above triggers a `Text-Report-ERROR-001` exception.

## Input parameters

- Parameter: `texte` | Type: String | Required: Yes | Possible values: Any string — supports `$variable` references | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `""`
- Parameter: `texte_type` | Type: String | Required: Yes | Possible values: `"Info Text"` / `"Title Text"` / `"Error Text"` | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `""`

## Output parameters

This task produces **no output variables**. It returns `VoidResult`.

- Field: — | Type: VoidResult | Trigger condition: Always | Default: —

## Exceptions

- Code: `Text-Report-ERROR-001` | Exception Name: Unsupported Text Type | Description: The value provided in `texte_type` is not one of the supported types: `"Info Text"`, `"Title Text"`, `"Error Text"`.
- Code: `ERROR-000` | Exception Name: Other Error | Description: An unexpected runtime error occurred during execution.

## Execution flowchart

The following diagram illustrates the actual implementation based on the Android code:

Diagram Nodes:
- ResolveText: 🔄 Resolve texte\nfrom workflow context
- InfoOp: 📋 rs.info\nWrite info message to report
- TitleOp: 📋 rs.appendTitle\nWrite title to report
- ErrorOp: 📋 rs.errorMsg\nWrite error message to report
- E1: ❌ Text-Report-ERROR-001

Workflow Flow:
- 🔄 Resolve texte\nfrom workflow context → ParseType
- 📋 rs.info\nWrite info message to report → Success
- 📋 rs.appendTitle\nWrite title to report → Success
- 📋 rs.errorMsg\nWrite error message to report → Success
- ❌ Text-Report-ERROR-001 → Error

**How it works:**

1. **Resolve text**: `texte` is resolved from the workflow context (replacing `$variable` references)
2. **Parse type**: `texte_type` is matched against the three supported string values (case-insensitive)
3. **Write to report**: the appropriate report method is called
4. **Result**: returns `VoidResult` on success

## Code examples

### Example 1 — Info message

```json
{
  "TextReport": [
    {
      "id": "1",
      "title": "Log step",
      "texte": "Ping started toward 8.8.8.8",
      "texte_type": "Info Text"
    }
  ]
}
```

### Example 2 — Section title

```json
{
  "TextReport": [
    {
      "id": "2",
      "title": "Section header",
      "texte": "Network Measurements",
      "texte_type": "Title Text"
    }
  ]
}
```

### Example 3 — Error message with variable

```json
{
  "TextReport": [
    {
      "id": "3",
      "title": "Log failure",
      "texte": "Task $failed_task_id failed: [$error_code] $error_desc",
      "texte_type": "Error Text"
    }
  ]
}
```

## Input parameter details

### 1. Input parameter: `texte`

The text content to write to the execution report. Supports `$workflow_variable` references — resolved at runtime before writing.

- **Default**: `""` (empty string)
- **Supports variables**: Yes

### 2. Input parameter: `texte_type`

Controls how the message is rendered in the AndroMate execution report.

- Value: `"Info Text"` | Report method: `rs.info()` | Rendering: Standard informational message
- Value: `"Title Text"` | Report method: `rs.appendTitle()` | Rendering: Section header / title
- Value: `"Error Text"` | Report method: `rs.errorMsg()` | Rendering: Error-styled message

- **Default**: `""` — triggers `Text-Report-ERROR-001` if not set to a valid value

## Complete JSON example

```json
{
  "TextReport": [
    {
      "id": "1",
      "title": "Log download result",
      "texte": "Downloaded $file_size bytes in $dl_time_ms ms",
      "texte_type": "Info Text"
    }
  ]
}
```