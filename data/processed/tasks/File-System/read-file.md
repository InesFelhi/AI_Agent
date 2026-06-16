# Read File

## Summary

- **Internal name**: `ReadFile`
- **Category**: File System
- **Purpose**: Read the text content of a file (up to 1 MB) into a workflow variable.
- **Task type**: Normal

## Compatibility

- **Minimum AndroMate version**: `{{ ANDROMATE_FIRST_VERSION }}`
- **Maximum AndroMate version**: `{{ ANDROMATE_CURRENT_VERSION }}`
- **Minimum Android**: `{{ ANDROMATE_MIN_APP_SDK }}`
- **Maximum Android tested**: `{{ ANDROID_CURRENT_APP_SDK }}`
- **Required permissions**: `MANAGE_EXTERNAL_STORAGE`

## Detailed description

The **Read File** task reads the UTF-8 text content of a file and stores it in the `value_output` variable.

To protect device memory and avoid huge workflow variables, the file size is **capped at 1 MB**. A larger file is rejected with `FILE-TASK-003` instead of being loaded. A workflow variable is meant for exploitable text (config, small JSON, results), not large files.

All File System tasks are confined to the **AndroMate sandbox**: `/sdcard/AndromateFileTask`. A path escaping the sandbox is rejected with `FILE-TASK-001`.

The content is returned as **raw text**, not parsed. To work with JSON afterwards, chain a **JSON Object Operation** task.

## Input parameters

- Parameter: `file_path` | Type: String | Required: Yes | Possible values / Rules: File path inside the sandbox — **max 1 MB** | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `""`

## Output parameters

- Field: `value_output` | Type: String | Trigger condition: On success — the file text content | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`

## Exceptions

- Code: `FILE-TASK-001` | Trigger condition: Path is outside the AndroMate sandbox
- Code: `FILE-TASK-002` | Trigger condition: File system operation failed (e.g. file not found)
- Code: `FILE-TASK-003` | Trigger condition: File too large to read (over 1 MB)

## Execution flowchart

Diagram Nodes:
- Jail: 📂 Ensure sandbox exists
- Read: 📖 readText UTF-8
- Store: 💾 Set value_output

Workflow Flow:
- 📂 Ensure sandbox exists → Validate
- 📖 readText UTF-8 → 💾 Set value_output
- 💾 Set value_output → Success

**How it works:**

1. **Sandbox**: the sandbox directory is created if missing
2. **Validate**: the resolved path is checked to be inside the sandbox
3. **Size guard**: if the file is larger than 1 MB, throws `FILE-TASK-003`
4. **Read**: the file is read as UTF-8 text
5. **Store**: the content is written to `value_output`
6. **Result**: returns `StrTaskResult`

## Code examples

### Example 1 — Read a config file into a variable

```json
{
  "ReadFile": [
    {
      "id": "1",
      "title": "Read config",
      "file_path": "config.json",
      "value_output": "$config"
    }
  ]
}
```

### Example 2 — Read then parse JSON

```json
{
  "ReadFile": [
    {
      "id": "1",
      "title": "Read data",
      "file_path": "data.json",
      "value_output": "$raw_json"
    }
  ]
}
```

*(then use a JSON Object Operation task on `$raw_json`)*

## Input parameter details

### `file_path` — File to read

Path inside the sandbox. The file must not exceed **1 MB** or the task throws `FILE-TASK-003`. Supports `$variable` interpolation.

## Output parameter details

### `value_output` — File content

Stores the raw UTF-8 text content of the file in the specified workflow variable. The content is **not** parsed — use a JSON Object Operation task to process structured data.

## Complete JSON example

```json
{
  "ReadFile": [
    {
      "id": "1",
      "title": "Read File",
      "file_path": "logs/result.log",
      "value_output": "$FILE_CONTENT"
    }
  ]
}
```