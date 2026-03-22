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
"Action_type : GlobalAction"
```

## 2. `GlobalAction_type`

Defines **which** Android global action will be performed.

This value is stored as an **internal integer / enum** and mapped to Android’s Accessibility global actions.

### Action list (based on enum)

- Logical name: SHOW_LAUNCHERS_ALL_APPS | Description: Show the launcher's “all apps” list | Android Global Action constant: GLOBAL_ACTION_ACCESSIBILITY_ALL_APPS | Min SDK: 31
- Logical name: SHOW_SCREEN_AUTOMATOR_BUTTON | Description: Trigger the Accessibility button | Android Global Action constant: GLOBAL_ACTION_ACCESSIBILITY_BUTTON | Min SDK: 31
- Logical name: SCREEN_AUTOMATOR_BUTTON_CHOOSER | Description: Open the Accessibility button chooser menu | Android Global Action constant: GLOBAL_ACTION_ACCESSIBILITY_BUTTON_CHOOSER | Min SDK: 31
- Logical name: SCREEN_AUTOMATOR_SHORT_CUT | Description: Trigger the Accessibility shortcut | Android Global Action constant: GLOBAL_ACTION_ACCESSIBILITY_SHORTCUT | Min SDK: 31
- Logical name: ACTION_BACK | Description: Navigate back | Android Global Action constant: GLOBAL_ACTION_BACK | Min SDK: 16
- Logical name: DISMISS_NOTIFICATION_SHADE | Description: Dismiss notification shade | Android Global Action constant: GLOBAL_ACTION_DISMISS_NOTIFICATION_SHADE | Min SDK: 31
- Logical name: GLOBAL_ACTION_DPAD_CENTER | Description: D-Pad center event | Android Global Action constant: GLOBAL_ACTION_DPAD_CENTER | Min SDK: 33
- Logical name: GLOBAL_ACTION_DPAD_DOWN | Description: D-Pad down event | Android Global Action constant: GLOBAL_ACTION_DPAD_LEFT | Min SDK: 33
- Logical name: GLOBAL_ACTION_DPAD_RIGHT | Description: D-Pad right event | Android Global Action constant: GLOBAL_ACTION_DPAD_RIGHT | Min SDK: 33
- Logical name: GLOBAL_ACTION_DPAD_UP | Description: D-Pad up event | Android Global Action constant: GLOBAL_ACTION_DPAD_UP | Min SDK: 33
- Logical name: GLOBAL_ACTION_HOME | Description: Go to Home | Android Global Action constant: GLOBAL_ACTION_HOME | Min SDK: 16
- Logical name: GLOBAL_ACTION_KEYCODE_HEADSETHOOK | Description: Headset hook key event | Android Global Action constant: GLOBAL_ACTION_KEYCODE_HEADSETHOOK | Min SDK: 31
- Logical name: GLOBAL_ACTION_LOCK_SCREEN | Description: Lock the screen | Android Global Action constant: GLOBAL_ACTION_LOCK_SCREEN | Min SDK: 28
- Logical name: GLOBAL_ACTION_MEDIA_PLAY_PAUSE | Description: Play/pause media | Android Global Action constant: *(SDK 36 pending)* | Min SDK: 22–36
- Logical name: GLOBAL_ACTION_MENU | Description: Trigger Menu key | Android Global Action constant: *(SDK 36 pending)* | Min SDK: 21–36
- Logical name: GLOBAL_ACTION_NOTIFICATIONS | Description: Open notifications | Android Global Action constant: GLOBAL_ACTION_NOTIFICATIONS | Min SDK: 16
- Logical name: GLOBAL_ACTION_POWER_DIALOG | Description: Open power dialog | Android Global Action constant: GLOBAL_ACTION_POWER_DIALOG | Min SDK: 21
- Logical name: GLOBAL_ACTION_QUICK_SETTINGS | Description: Open quick settings | Android Global Action constant: GLOBAL_ACTION_QUICK_SETTINGS | Min SDK: 17
- Logical name: GLOBAL_ACTION_RECENTS | Description: Open recent apps | Android Global Action constant: GLOBAL_ACTION_RECENTS | Min SDK: 16
- Logical name: GLOBAL_ACTION_TAKE_SCREENSHOT | Description: Take screenshot | Android Global Action constant: GLOBAL_ACTION_TAKE_SCREENSHOT | Min SDK: 28
- Logical name: GLOBAL_ACTION_TOGGLE_SPLIT_SCREEN | Description: Toggle split-screen mode | Android Global Action constant: GLOBAL_ACTION_TOGGLE_SPLIT_SCREEN | Min SDK: 24

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