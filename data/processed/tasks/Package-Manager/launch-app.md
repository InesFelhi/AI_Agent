# Launch App

## Summary

- **Internal name**: `LaunchApp`
- **Category**: Package Manager
- **Purpose**: Launch an installed application on the device by its package name, using its default launcher activity.
- **Task type**: Normal

## Compatibility

- **Minimum AndroMate version**: `{{ ANDROMATE_FIRST_VERSION }}`
- **Maximum AndroMate version**: `{{ ANDROMATE_CURRENT_VERSION }}`
- **Minimum Android**: `{{ ANDROMATE_MIN_APP_SDK }}`
- **Maximum Android tested**: `{{ ANDROID_CURRENT_APP_SDK }}`
- **Required permissions**: `QUERY_ALL_PACKAGES`, `SYSTEM_ALERT_WINDOW` (recommended)

## Detailed description

The **Launch App** task starts an application by resolving its default launcher activity via `PackageManager.getLaunchIntentForPackage()` and calling `startActivity()` with the `FLAG_ACTIVITY_NEW_TASK` flag (required when launching from a service context).

**Background launch note**: Since Android 10 (API 29), an app in the background cannot start activities (*Background Activity Launch* restrictions). AndroMate runs as a foreground service, so to launch other apps reliably it relies on the **Accessibility Service** and the **Display over other apps** permission (`SYSTEM_ALERT_WINDOW`), both of which exempt it from BAL restrictions.

If the package is not installed or has no launchable activity, the task throws `PACKAGE-MANAGER-ERROR-001`.

## Input parameters

- Parameter: `package_name` | Type: String | Required: Yes | Possible values / Rules: Valid Android package name (`com.example.app`) | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `""`

## Output parameters

The Launch App task **does not return** any data. Its purpose is to perform a system action.

## Exceptions

- Code: `PACKAGE-MANAGER-ERROR-001` | Trigger condition: The package is not installed, or has no launchable (MAIN/LAUNCHER) activity

## Execution flowchart

Diagram Nodes:
- Resolve: 🔧 Resolve package_name
- GetIntent: 📦 getLaunchIntentForPackage
- AddFlag: 🚩 Add FLAG_ACTIVITY_NEW_TASK
- StartActivity: ▶ startActivity

Workflow Flow:
- 🔧 Resolve package_name → 📦 getLaunchIntentForPackage
- 📦 getLaunchIntentForPackage → HasIntent
- 🚩 Add FLAG_ACTIVITY_NEW_TASK → ▶ startActivity
- ▶ startActivity → Success

**How it works:**

1. **Resolve**: the `package_name` is resolved against the AndroMate context
2. **Get intent**: `getLaunchIntentForPackage()` resolves the app's default launcher activity
3. **Check**: if no intent is returned, the task throws `PACKAGE-MANAGER-ERROR-001`
4. **Launch**: `FLAG_ACTIVITY_NEW_TASK` is added and `startActivity()` is called
5. **Result**: returns `VoidResult`

## Code examples

### Example 1 — Launch WhatsApp

```json
{
  "LaunchApp": [
    {
      "id": "1",
      "title": "Open WhatsApp",
      "package_name": "com.whatsapp"
    }
  ]
}
```

## Input parameter details

### `package_name` — Target package

The Android package identifier of the app to launch.

- Must be a valid, installed package name (e.g. `com.whatsapp`)
- Supports variable interpolation (e.g. `$target_pkg`, `${PKG}`)
- The app must expose a launchable activity (category `LAUNCHER`, action `MAIN`)
- If no launch intent can be resolved, the task throws `PACKAGE-MANAGER-ERROR-001`

## Output parameter details

This task produces no output variable. It performs a system action (starting the target app) and returns a `VoidResult` on success.

## Complete JSON example

```json
{
  "LaunchApp": [
    {
      "id": "1",
      "title": "Launch App",
      "package_name": "com.instagram.android"
    }
  ]
}
```