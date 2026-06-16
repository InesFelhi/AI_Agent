# Get App Info

## Summary

- **Internal name**: `GetAppInfo`
- **Category**: Package Manager
- **Purpose**: Retrieve detailed information about an installed application from its package name: version, label, install dates, target SDK, APK size, and system/enabled flags.
- **Task type**: Normal

## Compatibility

- **Minimum AndroMate version**: `{{ ANDROMATE_FIRST_VERSION }}`
- **Maximum AndroMate version**: `{{ ANDROMATE_CURRENT_VERSION }}`
- **Minimum Android**: `{{ ANDROMATE_MIN_APP_SDK }}`
- **Maximum Android tested**: `{{ ANDROID_CURRENT_APP_SDK }}`
- **Required permissions**: `QUERY_ALL_PACKAGES`

## Detailed description

The **Get App Info** task queries the Android `PackageManager` for a single package and returns all available metadata. Each piece of information is written to its own optional output variable — only the outputs you fill in are stored, the rest are ignored.

Since Android 11 (API 30), apps cannot see other installed packages by default (*package visibility filtering*). AndroMate declares the `QUERY_ALL_PACKAGES` permission so it can query any installed package by name.

If the package is not installed, the task throws `PACKAGE-MANAGER-ERROR-001`.

## Input parameters

- Parameter: `package_name` | Type: String | Required: Yes | Possible values / Rules: Valid Android package name (`com.example.app`) | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `""`

## Output parameters

All outputs are **optional** — leave a field empty to skip it.

- Field: `version_name_output` | Type: String | Trigger condition: App version name (e.g. `"2.5.1"`) | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`
- Field: `version_code_output` | Type: Long | Trigger condition: Integer version code (e.g. `150`) | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`
- Field: `app_name_output` | Type: String | Trigger condition: App display label (e.g. `"WhatsApp"`) | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`
- Field: `first_install_output` | Type: Long | Trigger condition: First install timestamp (ms) | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`
- Field: `last_update_output` | Type: Long | Trigger condition: Last update timestamp (ms) | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`
- Field: `target_sdk_output` | Type: Long | Trigger condition: Target SDK API level (e.g. `34`) | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`
- Field: `apk_size_output` | Type: Long | Trigger condition: APK file size in bytes | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`
- Field: `is_system_output` | Type: String | Trigger condition: `"true"` if system app, else `"false"` | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`
- Field: `is_enabled_output` | Type: String | Trigger condition: `"true"` if enabled, else `"false"` | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`

## Exceptions

- Code: `PACKAGE-MANAGER-ERROR-001` | Trigger condition: The package is not installed on the device

## Execution flowchart

Diagram Nodes:
- Resolve: 🔧 Resolve package_name
- Query: 📦 PackageManager.getPackageInfo
- Read: 📖 Read version, label, dates,\ntarget SDK, APK size, flags
- Store: 💾 Set output variables\nAppInfoTaskResult

Workflow Flow:
- 🔧 Resolve package_name → 📦 PackageManager.getPackageInfo
- 📦 PackageManager.getPackageInfo → Found
- 📖 Read version, label, dates,\ntarget SDK, APK size, flags → 💾 Set output variables\nAppInfoTaskResult
- 💾 Set output variables\nAppInfoTaskResult → Success

**How it works:**

1. **Resolve**: the `package_name` is resolved against the AndroMate context
2. **Query**: `PackageManager.getPackageInfo()` is called with the package name
3. **Check**: if the package is not found, the task throws `PACKAGE-MANAGER-ERROR-001`
4. **Read**: version, label, install/update timestamps, target SDK, APK size, and flags are read
5. **Store**: each requested output variable is filled
6. **Result**: returns `AppInfoTaskResult`

## Code examples

### Example 1 — Read the version of WhatsApp

```json
{
  "GetAppInfo": [
    {
      "id": "1",
      "title": "WhatsApp version",
      "package_name": "com.whatsapp",
      "version_name_output": "$wa_version",
      "version_code_output": "$wa_code"
    }
  ]
}
```

### Example 2 — Full metadata dump

```json
{
  "GetAppInfo": [
    {
      "id": "2",
      "title": "App full info",
      "package_name": "com.instagram.android",
      "app_name_output": "$name",
      "version_name_output": "$ver",
      "target_sdk_output": "$sdk",
      "apk_size_output": "$size",
      "is_system_output": "$is_sys",
      "is_enabled_output": "$is_on"
    }
  ]
}
```

## Input parameter details

### `package_name` — Target package

The Android package identifier of the app to inspect.

- Must be a valid, installed package name (e.g. `com.whatsapp`)
- Supports variable interpolation (e.g. `$target_pkg`, `${PKG}`)
- If the package is not installed, the task throws `PACKAGE-MANAGER-ERROR-001`

## Output parameter details

All output variables are optional. Leave a field empty to skip writing that value.

### `version_name_output` — Version name

Human-readable version string as displayed to users (e.g. `"2.5.1"`).

### `version_code_output` — Version code

Monotonic integer used internally for update comparison (e.g. `150`). Read via `getLongVersionCode()`.

### `app_name_output` — Application label

The display name of the app as shown in the launcher (e.g. `"WhatsApp"`).

### `first_install_output` — First install time

Timestamp in milliseconds since epoch when the app was first installed.

### `last_update_output` — Last update time

Timestamp in milliseconds since epoch of the most recent update. Equals `first_install_output` if never updated.

### `target_sdk_output` — Target SDK version

The API level the app targets (e.g. `34` for Android 14).

### `apk_size_output` — APK size

Size of the base APK file in bytes.

### `is_system_output` — System app flag

`"true"` if the app is a pre-installed system app (`FLAG_SYSTEM`), `"false"` otherwise.

### `is_enabled_output` — Enabled flag

`"true"` if the app is currently enabled, `"false"` if disabled.

## Complete JSON example

```json
{
  "GetAppInfo": [
    {
      "id": "1",
      "title": "Get App Info",
      "package_name": "com.whatsapp",
      "version_name_output": "$APP_VERSION",
      "app_name_output": "$APP_NAME"
    }
  ]
}
```