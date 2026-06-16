# Is App Installed

## Summary

- **Internal name**: `IsAppInstalled`
- **Category**: Package Manager
- **Purpose**: Check whether an application is installed on the device. Branches the workflow: `true` if the package exists, `false` otherwise.
- **Task type**: Condition

## Compatibility

- **Minimum AndroMate version**: `{{ ANDROMATE_FIRST_VERSION }}`
- **Maximum AndroMate version**: `{{ ANDROMATE_CURRENT_VERSION }}`
- **Minimum Android**: `{{ ANDROMATE_MIN_APP_SDK }}`
- **Maximum Android tested**: `{{ ANDROID_CURRENT_APP_SDK }}`
- **Required permissions**: `QUERY_ALL_PACKAGES`

## Detailed description

The **Is App Installed** task checks the presence of a package on the device using the Android `PackageManager`. It acts as a condition node: the workflow branches to the `true` path if the package is installed, and to the `false` path otherwise.

Since Android 11 (API 30), apps cannot see other installed packages by default (*package visibility filtering*). AndroMate declares the `QUERY_ALL_PACKAGES` permission so it can detect any installed package by name.

This task never throws — a missing package simply routes to the `false` branch.

## Input parameters

- Parameter: `package_name` | Type: String | Required: Yes | Possible values / Rules: Valid Android package name (`com.example.app`) | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `""`

## Output parameters

This is a **Condition** task — it does not store a value. Instead, it directs workflow execution:

- Condition: Package is installed | Next step: `true` branch
- Condition: Package is not installed | Next step: `false` branch

## Exceptions

This task does not throw exceptions. A missing package routes to the `false` branch.

## Execution flowchart

Diagram Nodes:
- Resolve: 🔧 Resolve package_name
- Query: 📦 PackageManager.getPackageInfo

Workflow Flow:
- 🔧 Resolve package_name → 📦 PackageManager.getPackageInfo
- 📦 PackageManager.getPackageInfo → Installed

**How it works:**

1. **Resolve**: the `package_name` is resolved against the AndroMate context
2. **Query**: `PackageManager.getPackageInfo()` is called
3. **Branch**: if the call succeeds → `true` branch; if it throws `NameNotFoundException` → `false` branch

## Code examples

### Example 1 — Branch on WhatsApp presence

```json
{
  "IsAppInstalled": [
    {
      "id": "1",
      "title": "WhatsApp installed ?",
      "package_name": "com.whatsapp"
    }
  ]
}
```

## Input parameter details

### `package_name` — Target package

The Android package identifier to check for.

- Must be a valid package name (e.g. `com.whatsapp`)
- Supports variable interpolation (e.g. `$target_pkg`, `${PKG}`)
- The package does **not** need to be installed — that is exactly what this task tests

## Output parameter details

This is a **Condition** task — it stores no output variable. The result drives the workflow branching:

### `true` branch

Taken when `PackageManager.getPackageInfo()` succeeds (the package is installed).

### `false` branch

Taken when the package is absent (`NameNotFoundException`).

## Complete JSON example

```json
{
  "IsAppInstalled": [
    {
      "id": "1",
      "title": "Is App Installed",
      "package_name": "com.instagram.android"
    }
  ]
}
```