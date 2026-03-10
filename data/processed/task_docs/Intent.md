# Intent — Android Intent Launcher

## Summary

- **Internal name**: `INTENT`
- **Category**: Android system interaction
- **Purpose**: Build and execute an Android `Intent` to **start an Activity** or **send a Broadcast**.

This task allows an AndroMate workflow to interact with the Android system and installed applications:  
open screens (Settings, specific apps, etc.) or send custom broadcast events.

## Compatibility

- **Minimum AndroMate version**: `{{ ANDROMATE_FIRST_VERSION }}`
- **Maximum AndroMate version**: `{{ ANDROMATE_CURRENT_VERSION }}`
- **Minimum Android**: `{{ ANDROMATE_MIN_APP_SDK }}`
- **Maximum Android tested**: `{{ ANDROID_CURRENT_APP_SDK }}`

### Supported manufacturers

- ✅ All manufacturers supported by AndroMate (behavior may vary by firmware)

### Required permissions

Depending on the target `Intent`, Android may require specific permissions:

- Starting some system or OEM Activities may require special permissions
- Sending some Broadcasts is restricted or blocked on recent Android versions

## Detailed description

The **Intent** task builds an Android `Intent` from the provided parameters, dynamically resolved using the **AndroMate context** (`AndroMateContext`).

Two execution modes are supported:

- ActionType: `Start Activity` | Description: Starts an Activity using `Context.startActivity()`
- ActionType: `Send Broadcast` | Description: Sends a broadcast using `Context.sendBroadcast()`

Parameters may contain variables (e.g. `${PKG_NAME}`) that are resolved before execution.

## Input parameters

- Parameter: `Action` | Type: String | Required: No | Possible values / Rules: Any valid Intent action (`android.intent.action.*` or custom) | Android compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `""`
- Parameter: `PackageName` | Type: String | Required: No | Possible values / Rules: Valid Android package name (`com.example.app`) | Android compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `""`
- Parameter: `ClassName` | Type: String | Required: No | Possible values / Rules: Fully qualified class name (`com.example.app.MainActivity`) | Android compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `""`
- Parameter: `Data` | Type: String | Required: No | Possible values / Rules: Data URI (`tel:`, `geo:`, `package:`, etc.) | Android compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `""`
- Parameter: `ActionType` | Type: Enum / String | Required: Yes | Possible values / Rules: `Start Activity` or `Send Broadcast` | Android compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: —

## Output parameters

The Intent task **does not return** any data (no stdout/stderr, no output variables).  
Its purpose is to **perform a system action**, not to produce content.

# Parameter details

## 1. `ActionType`

Defines the **execution mode** of the task.

- `Start Activity`: starts a target Activity using `context.startActivity(intent)` with flags:
  - `FLAG_ACTIVITY_NEW_TASK`
  - `FLAG_ACTIVITY_CLEAR_TASK`
- `Send Broadcast`: sends a broadcast using `context.sendBroadcast(intent)`.

### Example

```json
"ActionType": "Start Activity"
```

or

```json
"ActionType": "Send Broadcast"
```

## 2. `Action`

Represents the **Intent action string**.

Common examples:

- `android.settings.SETTINGS`
- `android.intent.action.VIEW`
- `com.example.CUSTOM_EVENT`

If **no action** is provided, the Intent can still be valid if a `PackageName` + `ClassName` pair is provided (explicit Intent).

### Example

```json
"Action": "android.settings.SETTINGS"
```

## 3. `PackageName`

Specifies the **target Android package**.  
Used to build an **explicit** Intent together with `(PackageName, ClassName)`.

### Example

```json
"PackageName": "com.android.settings"
```

## 4. `ClassName`

Fully qualified **Activity class name**.

### Example

```json
"ClassName": "com.android.settings.Settings"
```

## 5. `Data`

String representing a **data URI**.

Typical examples:

- `tel:+21690000000`
- `package:com.example.app`
- `geo:36.8065,10.1815`

### Example

```json
"Data": "tel:+21690000000"
```

## Execution behavior

1. The Intent is constructed using the provided parameters
2. If construction fails → an error is logged
3. If valid:
  - `Start Activity` → `context.startActivity(intent)`
  - `Send Broadcast` → `context.sendBroadcast(intent)`

## Exceptions

- Code: Intent-ERROR-001 | Exception Name: INTENT_START_ACTIVITY_ERROR | Description: Unable to start Activity
- Code: Intent-ERROR-002 | Exception Name: INTENT_SEND_BROADCAST_ERROR | Description: Unable to send broadcast

## Complete JSON example

```json
{
  "Intent": [
    {
      "id": "50",
      "title": "Open Android Settings",
      "Action": "android.settings.SETTINGS",
      "PackageName": "com.android.settings",
      "ClassName": "com.android.settings.Settings",
      "Data": "",
      "ActionType": "Start Activity"
    },
    {
      "id": "51",
      "title": "Send custom broadcast",
      "Action": "com.example.CUSTOM_EVENT",
      "PackageName": "com.example.app",
      "ClassName": "",
      "Data": "",
      "ActionType": "Send Broadcast"
    }
  ]
}
```