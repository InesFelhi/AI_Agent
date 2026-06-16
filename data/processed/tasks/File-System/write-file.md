# Write File

## Summary

- **Internal name**: `WriteFile`
- **Category**: File System
- **Purpose**: Write or append text content to a file inside the AndroMate file sandbox.
- **Task type**: Normal

## Compatibility

- **Minimum AndroMate version**: `{{ ANDROMATE_FIRST_VERSION }}`
- **Maximum AndroMate version**: `{{ ANDROMATE_CURRENT_VERSION }}`
- **Minimum Android**: `{{ ANDROMATE_MIN_APP_SDK }}`
- **Maximum Android tested**: `{{ ANDROID_CURRENT_APP_SDK }}`
- **Required permissions**: `MANAGE_EXTERNAL_STORAGE`

## Detailed description

The **Write File** task writes text to a file. The file (and its parent directories) is created automatically if it does not exist. Three write modes are available: overwrite, append, or append with a trailing newline.

All File System tasks are confined to the **AndroMate sandbox**: `/sdcard/AndromateFileTask`. A path escaping the sandbox is rejected with `FILE-TASK-001`. The sandbox directory is created automatically on first use.

## Input parameters

- Parameter: `file_path` | Type: String | Required: Yes | Possible values / Rules: File path inside the sandbox (supports interpolation) | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `""`
- Parameter: `content` | Type: String | Required: Yes | Possible values / Rules: Text to write (supports interpolation) | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `""`
- Parameter: `mode` | Type: Enum / String | Required: No | Possible values / Rules: `Overwrite`, `Append`, `Append Line` | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `Overwrite`

## Output parameters

This task produces no output variable. It returns a `VoidResult` on success.

## Exceptions

- Code: `FILE-TASK-001` | Trigger condition: Path is outside the AndroMate sandbox
- Code: `FILE-TASK-002` | Trigger condition: File system operation failed (I/O error)

## Execution flowchart

Diagram Nodes:
- Jail: 📂 Ensure sandbox exists
- W1: ✍️ writeText replace
- W2: ➕ writeText append
- W3: ↵ writeLine append + newline

Workflow Flow:
- 📂 Ensure sandbox exists → Validate
- ✍️ writeText replace → Success
- ➕ writeText append → Success
- ↵ writeLine append + newline → Success

**How it works:**

1. **Sandbox**: the sandbox directory is created if missing
2. **Validate**: the resolved path is checked to be inside the sandbox
3. **Write**: the content is written according to the selected mode (the file is created if missing)
4. **Result**: returns `VoidResult`

## Code examples

### Example 1 — Overwrite a file

```json
{
  "WriteFile": [
    {
      "id": "1",
      "title": "Save config",
      "file_path": "config.json",
      "content": "{ \"enabled\": true }",
      "mode": "Overwrite"
    }
  ]
}
```

### Example 2 — Append a log line

```json
{
  "WriteFile": [
    {
      "id": "2",
      "title": "Log step",
      "file_path": "logs/run.log",
      "content": "Step $i done",
      "mode": "Append Line"
    }
  ]
}
```

## Input parameter details

### `file_path` — Target file

Path inside the sandbox. Created automatically (with parents) if missing. Supports interpolation.

### `content` — Text to write

The text written to the file. Supports `$variable` and `${SPECIAL_VAR}` interpolation.

### `mode` — Write mode

- `Overwrite` → replaces the whole file content
- `Append` → adds the content at the end (no newline)
- `Append Line` → adds the content at the end **plus a trailing newline** (ideal for logs)

## Output parameter details

This task produces no output variable.

## Complete JSON example

```json
{
  "WriteFile": [
    {
      "id": "1",
      "title": "Write File",
      "file_path": "logs/result.log",
      "content": "Job $job_name finished",
      "mode": "Append Line"
    }
  ]
}
```