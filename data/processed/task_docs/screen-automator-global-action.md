# Screen Automator — GlobalAction

## Summary

- **Internal name**: `SCREEN_AUTOMATOR`
- **Category**: Screen Automation / Accessibility
- **Purpose**: Execute predefined Android system actions (Home, Back, Recents, Notifications, Screenshot, etc.) using the Android AccessibilityService.

This task allows an AndroMate workflow to control system navigation and system UI without relying on text detection or coordinates.

## Compatibility

- **Minimum AndroMate version**: `{{ ANDROMATE_FIRST_VERSION }}`
- **Maximum AndroMate version**: `{{ ANDROMATE_CURRENT_VERSION }}`
- **Minimum Android**: `{{ ANDROMATE_MIN_APP_SDK }}`
- **Maximum Android tested**: `{{ ANDROID_CURRENT_APP_SDK }}`

### Supported manufacturers

- ✅ Samsung (One UI 6.x / 7.x / 8.x)

### Required permissions

- `ACCESSIBILITY_SERVICE`
- (Optionally) `WRITE_SECURE_SETTINGS` depending on OEM/system behavior

## Detailed description

The **GlobalAction** mode of ScreenAutomator executes **high-level Android system actions** exposed by the Accessibility framework.

Typical use cases:

- Navigate in the system:
  - HOME, BACK, RECENTS
- Open or dismiss system panels:
  - Notifications panel
  - Quick settings
  - Power dialog
  - All apps / launcher app list
- Perform device operations:
  - Lock the screen
  - Take a screenshot
  - Toggle split-screen
- Simulate specific keys / D-Pad / media control:
  - D-Pad (up, down, left, right, center)
  - Media play/pause
  - Headset hook key

The exact list of supported actions depends on the **Android version** (min SDK per action) and the device manufacturer.

## Input parameters

- Parameter: `Action_type` | Type: Enum / String | Required: Yes | Possible values: Must be `"GlobalAction"` | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: —
- Parameter: `GlobalAction_type` | Type: Enum / Integer | Required: Yes | Possible values: Any supported global action | Android Compatibility: Depends on each action’s **min SDK** (16 → 33+) | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: —

## Output parameters

This GlobalAction mode:

- does **not** return stdout/stderr
- does **not** define specific output variables

Its purpose is to **perform** an action (side-effect on UI), not to produce content.

# Parameter details

## 1. `Action_type`

Indicates the ScreenAutomator mode to use.

- For this README: it must be set to `"GlobalAction"`.

### Example

```json
"Action_type": "GlobalAction"
```

## 2. `GlobalAction_type`

Defines **which** Android global action will be performed.

This value is stored as an **internal integer / enum** and mapped to Android’s Accessibility global actions.

### Action list (based on enum)

- Logical name: SHOW_LAUNCHERS_ALL_APPS | Description: Show the launcher's “all apps” list | Hex value: `0x0000000B` | Min SDK: 31
- Logical name: SHOW_SCREEN_AUTOMATOR_BUTTON | Description: Trigger the Accessibility button | Hex value: `0x0000000A` | Min SDK: 31
- Logical name: SCREEN_AUTOMATOR_BUTTON_CHOOSER | Description: Open Accessibility button chooser | Hex value: `0x0000000C` | Min SDK: 31
- Logical name: SCREEN_AUTOMATOR_SHORT_CUT | Description: Trigger the Accessibility shortcut | Hex value: `0x0000000D` | Min SDK: 31
- Logical name: ACTION_BACK | Description: Navigate back | Hex value: `0x00000001` | Min SDK: 16
- Logical name: DISMISS_NOTIFICATION_SHADE | Description: Dismiss notification shade | Hex value: `0x0000000E` | Min SDK: 31
- Logical name: GLOBAL_ACTION_DPAD_CENTER | Description: D-Pad center event | Hex value: `0x00000014` | Min SDK: 33
- Logical name: GLOBAL_ACTION_DPAD_DOWN | Description: D-Pad down event | Hex value: `0x00000011` | Min SDK: 33
- Logical name: GLOBAL_ACTION_DPAD_RIGHT | Description: D-Pad right event | Hex value: `0x00000013` | Min SDK: 33
- Logical name: GLOBAL_ACTION_DPAD_UP | Description: D-Pad up event | Hex value: `0x00000010` | Min SDK: 33
- Logical name: GLOBAL_ACTION_HOME | Description: Go to Home | Hex value: `0x00000002` | Min SDK: 16
- Logical name: GLOBAL_ACTION_KEYCODE_HEADSETHOOK | Description: Headset hook key event | Hex value: `0x0000000F` | Min SDK: 31
- Logical name: GLOBAL_ACTION_LOCK_SCREEN | Description: Lock the screen | Hex value: `0x00000008` | Min SDK: 28
- Logical name: GLOBAL_ACTION_MEDIA_PLAY_PAUSE | Description: Play/pause media | Hex value: — | Min SDK: 22–36
- Logical name: GLOBAL_ACTION_MENU | Description: Trigger Menu key | Hex value: — | Min SDK: 21–36
- Logical name: GLOBAL_ACTION_NOTIFICATIONS | Description: Open notifications | Hex value: `0x00000004` | Min SDK: 16
- Logical name: GLOBAL_ACTION_POWER_DIALOG | Description: Open power dialog | Hex value: `0x00000006` | Min SDK: 21
- Logical name: GLOBAL_ACTION_QUICK_SETTINGS | Description: Open quick settings | Hex value: `0x00000005` | Min SDK: 17
- Logical name: GLOBAL_ACTION_RECENTS | Description: Open recent apps | Hex value: `0x00000003` | Min SDK: 16
- Logical name: GLOBAL_ACTION_TAKE_SCREENSHOT | Description: Take screenshot | Hex value: `0x00000009` | Min SDK: 28
- Logical name: GLOBAL_ACTION_TOGGLE_SPLIT_SCREEN | Description: Toggle split-screen mode | Hex value: `0x00000007` | Min SDK: 24

## Exceptions

- Code: SCREEN-AUTOMATOR-ERROR-001 | Exception Name: INVALID_CONTROL_SERVICE_GLOBAL_ACTION | Description: The provided global action is invalid or unknown
- Code: SCREEN-AUTOMATOR-ERROR-002 | Exception Name: UNSUPPORTED_CONTROL_SERVICE_GLOBAL_ACTION | Description: The requested global action is not supported on this device / Android OS
- Code: SCREEN-AUTOMATOR-ERROR-003 | Exception Name: INVALID_ACTION_TYPE | Description: Invalid action type (must be `GlobalAction`)
- Code: SCREEN-AUTOMATOR-ERROR-008 | Exception Name: TIME_OUT | Description: Execution of the global action exceeded the allowed timeout

# Complete JSON example

```json
{
  "ScreenAutomator": [
    {
      "id": "1",
      "title": "Go Home",
      "Action_type": "GlobalAction",
      "GlobalAction_type": 10
    },
    {
      "id": "2",
      "title": "Open Notifications",
      "Action_type": "GlobalAction",
      "GlobalAction_type": 7
    },
    {
      "id": "3",
      "title": "Open Recents",
      "Action_type": "GlobalAction",
      "GlobalAction_type": 12
    },
    {
      "id": "4",
      "title": "Take Screenshot",
      "Action_type": "GlobalAction",
      "GlobalAction_type": 18
    }
  ]
}
```