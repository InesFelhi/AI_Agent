# Create File / Dir

## Summary

- **Internal name**: `CreateDir`
- **Category**: File System
- **Purpose**: Create a file or a directory (recursively) inside the AndroMate file sandbox.
- **Task type**: Normal

## Compatibility

- **Minimum AndroMate version**: `{{ ANDROMATE_FIRST_VERSION }}`
- **Maximum AndroMate version**: `{{ ANDROMATE_CURRENT_VERSION }}`
- **Minimum Android**: `{{ ANDROMATE_MIN_APP_SDK }}`
- **Maximum Android tested**: `{{ ANDROID_CURRENT_APP_SDK }}`
- **Required permissions**: `MANAGE_EXTERNAL_STORAGE`

## Detailed description

The **Create File / Dir** task creates either a file or a directory, depending on the selected type. Parent directories are created recursively if needed.

All File System tasks are confined to the **AndroMate sandbox**: `/sdcard/AndromateFileTask`. A relative path is resolved inside the sandbox; an absolute path must stay within it. Any attempt to escape the sandbox (e.g. with `../`) is rejected with `FILE-TASK-001`. The sandbox directory is created automatically on first use.

## Input parameters

- Parameter: `create_type` | Type: Enum / String | Required: No | Possible values / Rules: `Directory` or `File` | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `Directory`
- Parameter: `file_path` | Type: String | Required: Yes | Possible values / Rules: Path inside the sandbox (supports interpolation) | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `""`

## Output parameters

This task produces no output variable. It returns a `VoidResult` on success.

## Exceptions

- Code: `FILE-TASK-001` | Trigger condition: Path is outside the AndroMate sandbox
- Code: `FILE-TASK-002` | Trigger condition: File system operation failed (I/O error)

## Execution flowchart

Diagram Nodes:
- Jail: 📂 Ensure sandbox exists
- MkFile: 📄 createFile
- MkDir: 📁 createDir

Workflow Flow:
- 📂 Ensure sandbox exists → Validate
- 📄 createFile → Success
- 📁 createDir → Success

**How it works:**

1. **Sandbox**: the sandbox directory is created if missing
2. **Validate**: the resolved path is checked to be inside the sandbox (anti path-traversal)
3. **Create**: a file (`createFile`) or directory (`createDir`) is created, parents included
4. **Result**: returns `VoidResult`

## Code examples

### Example 1 — Create a directory

```json
{
  "CreateDir": [
    {
      "id": "1",
      "title": "Create reports folder",
      "create_type": "Directory",
      "file_path": "reports/2026"
    }
  ]
}
```

### Example 2 — Create an empty file

```json
{
  "CreateDir": [
    {
      "id": "2",
      "title": "Create log file",
      "create_type": "File",
      "file_path": "logs/result.log"
    }
  ]
}
```

## Input parameter details

### `create_type` — What to create

- `Directory` → creates a folder (recursively)
- `File` → creates an empty file (parent folders created if needed)

### `file_path` — Target path

Path inside the sandbox. A relative path (`reports/2026`) is resolved under `/sdcard/AndromateFileTask`. Supports `$variable` interpolation.

## Output parameter details

This task produces no output variable.

## Complete JSON example

```json
{
  "CreateDir": [
    {
      "id": "1",
      "title": "Create File / Dir",
      "create_type": "Directory",
      "file_path": "reports/2026"
    }
  ]
}
```