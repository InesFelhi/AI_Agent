# Get Installed Apps

## Summary

- **Internal name**: `GetInstalledApps`
- **Category**: Package Manager
- **Purpose**: List all applications installed on the device as a JSON array. Each entry contains the package name, label, version, and system/enabled flags.
- **Task type**: Normal

## Compatibility

- **Minimum AndroMate version**: `{{ ANDROMATE_FIRST_VERSION }}`
- **Maximum AndroMate version**: `{{ ANDROMATE_CURRENT_VERSION }}`
- **Minimum Android**: `{{ ANDROMATE_MIN_APP_SDK }}`
- **Maximum Android tested**: `{{ ANDROID_CURRENT_APP_SDK }}`
- **Required permissions**: `QUERY_ALL_PACKAGES`

## Detailed description

The **Get Installed Apps** task enumerates every package on the device via `PackageManager.getInstalledPackages()` and produces a JSON array. System apps are excluded by default; enable `include_system` to include them.

The output is lightweight — it does **not** read the APK size per app (which would require file-system access for every package), keeping the task fast even on devices with hundreds of apps.

Since Android 11 (API 30), apps cannot enumerate other packages by default (*package visibility filtering*). AndroMate declares the `QUERY_ALL_PACKAGES` permission so the full list is visible.

## Input parameters

- Parameter: `include_system` | Type: Boolean | Required: No | Possible values / Rules: `true` to include pre-installed system apps | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `false`

## Output parameters

- Field: `json_array_output` | Type: JSON Array | Trigger condition: Always on success — array of installed app objects | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`

### Array element structure

Each element of `json_array_output` has the following shape:

```json
{
  "packageName": "com.whatsapp",
  "appName": "WhatsApp",
  "versionName": "2.24.1",
  "versionCode": 24001,
  "isSystemApp": false,
  "isEnabled": true
}
```

## Exceptions

This task does not throw exceptions. If no apps match, an empty JSON array is returned.

## Execution flowchart

Diagram Nodes:
- List: 📦 getInstalledPackages
- Loop: 🔁 For each package
- Build: 🧩 Build JSON object\npackage, name, version, flags
- Store: 💾 Set json_array_output\nJsonArrayTaskResult

Workflow Flow:
- 📦 getInstalledPackages → 🔁 For each package
- 🔁 For each package → SystemCheck
- 🧩 Build JSON object\npackage, name, version, flags → 🔁 For each package
- 🔁 For each package → 💾 Set json_array_output\nJsonArrayTaskResult
- 💾 Set json_array_output\nJsonArrayTaskResult → Success

**How it works:**

1. **List**: `getInstalledPackages()` returns all packages
2. **Filter**: system apps are skipped unless `include_system` is `true`
3. **Build**: a JSON object is built for each app (package, label, version, flags)
4. **Store**: the JSON array is written to `json_array_output`
5. **Result**: returns `JsonArrayTaskResult`

## Code examples

### Example 1 — List user apps only

```json
{
  "GetInstalledApps": [
    {
      "id": "1",
      "title": "List user apps",
      "include_system": false,
      "json_array_output": "$apps"
    }
  ]
}
```

### Example 2 — Include system apps

```json
{
  "GetInstalledApps": [
    {
      "id": "2",
      "title": "List all apps",
      "include_system": true,
      "json_array_output": "$all_apps"
    }
  ]
}
```

## Input parameter details

### `include_system` — Include system apps

Controls whether pre-installed system apps appear in the result.

- `false` (default): only user-installed apps are listed
- `true`: system apps (those with `FLAG_SYSTEM`) are also included
- Supports variable interpolation (e.g. `$with_system`)

## Output parameter details

### `json_array_output` — Installed apps list

Stores the full list of installed apps as a JSON array in the specified workflow variable. Each element is an object:

- Key: `packageName` | Type: String | Description: Package identifier (e.g. `com.whatsapp`)
- Key: `appName` | Type: String | Description: Display label (e.g. `"WhatsApp"`)
- Key: `versionName` | Type: String | Description: Human-readable version (e.g. `"2.24.1"`)
- Key: `versionCode` | Type: Number | Description: Integer version code (e.g. `24001`)
- Key: `isSystemApp` | Type: Boolean | Description: `true` if a pre-installed system app
- Key: `isEnabled` | Type: Boolean | Description: `true` if the app is enabled

The array can be further processed with the **JSON Object Operation** task (e.g. read its size, iterate, extract a field).

## Complete JSON example

```json
{
  "GetInstalledApps": [
    {
      "id": "1",
      "title": "Get Installed Apps",
      "include_system": false,
      "json_array_output": "$INSTALLED_APPS"
    }
  ]
}
```