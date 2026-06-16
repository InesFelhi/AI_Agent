# File Exists

## Summary

- **Internal name**: `FileExists`
- **Category**: File System
- **Purpose**: Check whether a file or a directory exists at the given path. Branches the workflow: `true` if it exists, `false` otherwise.
- **Task type**: Condition

## Compatibility

- **Minimum AndroMate version**: `{{ ANDROMATE_FIRST_VERSION }}`
- **Maximum AndroMate version**: `{{ ANDROMATE_CURRENT_VERSION }}`
- **Minimum Android**: `{{ ANDROMATE_MIN_APP_SDK }}`
- **Maximum Android tested**: `{{ ANDROID_CURRENT_APP_SDK }}`
- **Required permissions**: `MANAGE_EXTERNAL_STORAGE`

## Detailed description

The **File Exists** task checks the presence of a path on the device file system using `File.exists()`. It acts as a condition node: the workflow branches to the `true` path if the file or directory exists, and to the `false` path otherwise.

The check returns `true` for **both files and directories** — it only tells you whether the path is present, not its type.

## Input parameters

- Parameter: `file_path` | Type: String | Required: Yes | Possible values / Rules: Path to a file or directory (supports interpolation) | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `""`

## Output parameters

This is a **Condition** task — it does not store a value. Instead, it directs workflow execution:

- Condition: The path exists (file or directory) | Next step: `true` branch
- Condition: The path does not exist | Next step: `false` branch

## Exceptions

This task does not throw exceptions. A missing path routes to the `false` branch.

## Execution flowchart

Diagram Nodes:
- Resolve: 🔧 Resolve file_path
- Check: 📁 File.exists

Workflow Flow:
- 🔧 Resolve file_path → 📁 File.exists
- 📁 File.exists → Exists

**How it works:**

1. **Resolve**: the `file_path` is resolved against the AndroMate context
2. **Check**: `File.exists()` is evaluated
3. **Branch**: exists → `true` branch; otherwise → `false` branch

## Code examples

### Example 1 — Branch on a config file presence

```json
{
  "FileExists": [
    {
      "id": "1",
      "title": "Config exists ?",
      "file_path": "/sdcard/AndromateFileTask/config.json"
    }
  ]
}
```

## Input parameter details

### `file_path` — Path to check

Absolute path to a file or directory. Supports `$variable` and `${SPECIAL_VAR}` interpolation. The check succeeds for both files and directories.

## Output parameter details

This is a **Condition** task — it stores no output variable. The result drives the workflow branching (`true` / `false`).

## Complete JSON example

```json
{
  "FileExists": [
    {
      "id": "1",
      "title": "File Exists",
      "file_path": "/sdcard/AndromateFileTask/logs/result.log"
    }
  ]
}
```