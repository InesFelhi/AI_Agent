# Screen Automator — GlobalAction

## Summary

- **Internal name**: `SCREEN_AUTOMATOR`
- **Category**: Screen Automation / Accessibility  
- **Purpose**: Execute predefined Android system actions (Home, Back, Recents, Notifications, Screenshot, etc.) using the Android AccessibilityService.

This task allows an AndroMate workflow to control system navigation and system UI without relying on text detection or coordinates.

---

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

---

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

---

## Input parameters

| Parameter           | Type            | Required | Possible values                                      | Android Compatibility                                  | AndroMate Compatibility                                         | Default |
|---------------------|-----------------|----------|------------------------------------------------------|--------------------------------------------------------|------------------------------------------------------------------|---------|
| `Action_type`       | Enum / String   | Yes      | Must be `"GlobalAction"`                             | {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | —       |
| `GlobalAction_type` | Enum / Integer  | Yes      | Any supported global action                          | Depends on each action’s **min SDK** (16 → 33+)       | {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | —       |

---

## Output parameters

This GlobalAction mode:

- does **not** return stdout/stderr  
- does **not** define specific output variables  

Its purpose is to **perform** an action (side-effect on UI), not to produce content.

---

# Parameter details

## 1. `Action_type`

Indicates the ScreenAutomator mode to use.

- For this README: it must be set to `"GlobalAction"`.

### Example

```json
"Action_type": "GlobalAction"
```

---

## 2. `GlobalAction_type`

Defines **which** Android global action will be performed.

This value is stored as an **internal integer / enum** and mapped to Android’s Accessibility global actions.

### Action list (based on enum)
| Logical name                         | Description                               | Hex value    | Min SDK |
|--------------------------------------|-------------------------------------------|--------------|---------|
| SHOW_LAUNCHERS_ALL_APPS             | Show the launcher's “all apps” list       | `0x0000000B` | 31      |
| SHOW_SCREEN_AUTOMATOR_BUTTON        | Trigger the Accessibility button          | `0x0000000A` | 31      |
| SCREEN_AUTOMATOR_BUTTON_CHOOSER     | Open Accessibility button chooser         | `0x0000000C` | 31      |
| SCREEN_AUTOMATOR_SHORT_CUT          | Trigger the Accessibility shortcut        | `0x0000000D` | 31      |
| ACTION_BACK                         | Navigate back                             | `0x00000001` | 16      |
| DISMISS_NOTIFICATION_SHADE          | Dismiss notification shade                | `0x0000000E` | 31      |
| GLOBAL_ACTION_DPAD_CENTER           | D-Pad center event                        | `0x00000014` | 33      |
| GLOBAL_ACTION_DPAD_DOWN             | D-Pad down event                          | `0x00000011` | 33      |
| GLOBAL_ACTION_DPAD_RIGHT            | D-Pad right event                         | `0x00000013` | 33      |
| GLOBAL_ACTION_DPAD_UP               | D-Pad up event                            | `0x00000010` | 33      |
| GLOBAL_ACTION_HOME                  | Go to Home                                | `0x00000002` | 16      |
| GLOBAL_ACTION_KEYCODE_HEADSETHOOK   | Headset hook key event                    | `0x0000000F` | 31      |
| GLOBAL_ACTION_LOCK_SCREEN           | Lock the screen                           | `0x00000008` | 28      |
| GLOBAL_ACTION_MEDIA_PLAY_PAUSE      | Play/pause media                          | —            | 22–36   |
| GLOBAL_ACTION_MENU                  | Trigger Menu key                          | —            | 21–36   |
| GLOBAL_ACTION_NOTIFICATIONS         | Open notifications                        | `0x00000004` | 16      |
| GLOBAL_ACTION_POWER_DIALOG          | Open power dialog                         | `0x00000006` | 21      |
| GLOBAL_ACTION_QUICK_SETTINGS        | Open quick settings                       | `0x00000005` | 17      |
| GLOBAL_ACTION_RECENTS               | Open recent apps                          | `0x00000003` | 16      |
| GLOBAL_ACTION_TAKE_SCREENSHOT       | Take screenshot                           | `0x00000009` | 28      |
| GLOBAL_ACTION_TOGGLE_SPLIT_SCREEN   | Toggle split-screen mode                  | `0x00000007` | 24      |


---

## Exceptions
| Code                          | Exception Name                           | Description                                                                 |
|------------------------------|-------------------------------------------|-----------------------------------------------------------------------------|
| SCREEN-AUTOMATOR-ERROR-001  | INVALID_CONTROL_SERVICE_GLOBAL_ACTION     | The provided global action is invalid or unknown                            |
| SCREEN-AUTOMATOR-ERROR-002  | UNSUPPORTED_CONTROL_SERVICE_GLOBAL_ACTION | The requested global action is not supported on this device / Android OS    |
| SCREEN-AUTOMATOR-ERROR-003  | INVALID_ACTION_TYPE                       | Invalid action type (must be `GlobalAction`)                                |
| SCREEN-AUTOMATOR-ERROR-008  | TIME_OUT                                  | Execution of the global action exceeded the allowed timeout                 |

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

---

