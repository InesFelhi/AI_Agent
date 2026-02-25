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
"Action_type : GlobalAction"
```

---

## 2. `GlobalAction_type`

Defines **which** Android global action will be performed.

This value is stored as an **internal integer / enum** and mapped to Android’s Accessibility global actions.

### Action list (based on enum)

| Logical name                       | Description                                           | Android Global Action constant                          | Min SDK |
|------------------------------------|-------------------------------------------------------|---------------------------------------------------------|---------|
| SHOW_LAUNCHERS_ALL_APPS         | Show the launcher's “all apps” list                   | GLOBAL_ACTION_ACCESSIBILITY_ALL_APPS                  | 31      |
| SHOW_SCREEN_AUTOMATOR_BUTTON    | Trigger the Accessibility button                      | GLOBAL_ACTION_ACCESSIBILITY_BUTTON                    | 31      |
| SCREEN_AUTOMATOR_BUTTON_CHOOSER | Open the Accessibility button chooser menu            | GLOBAL_ACTION_ACCESSIBILITY_BUTTON_CHOOSER            | 31      |
| SCREEN_AUTOMATOR_SHORT_CUT      | Trigger the Accessibility shortcut                    | GLOBAL_ACTION_ACCESSIBILITY_SHORTCUT                  | 31      |
| ACTION_BACK                     | Navigate back                                          | GLOBAL_ACTION_BACK                                    | 16      |
| DISMISS_NOTIFICATION_SHADE      | Dismiss notification shade                            | GLOBAL_ACTION_DISMISS_NOTIFICATION_SHADE              | 31      |
| GLOBAL_ACTION_DPAD_CENTER       | D-Pad center event                                    | GLOBAL_ACTION_DPAD_CENTER                             | 33      |
| GLOBAL_ACTION_DPAD_DOWN         | D-Pad down event                                      | GLOBAL_ACTION_DPAD_LEFT                               | 33      |
| GLOBAL_ACTION_DPAD_RIGHT        | D-Pad right event                                     | GLOBAL_ACTION_DPAD_RIGHT                              | 33      |
| GLOBAL_ACTION_DPAD_UP           | D-Pad up event                                        | GLOBAL_ACTION_DPAD_UP                                 | 33      |
| GLOBAL_ACTION_HOME              | Go to Home                                             | GLOBAL_ACTION_HOME                                    | 16      |
| GLOBAL_ACTION_KEYCODE_HEADSETHOOK | Headset hook key event                               | GLOBAL_ACTION_KEYCODE_HEADSETHOOK                     | 31      |
| GLOBAL_ACTION_LOCK_SCREEN       | Lock the screen                                        | GLOBAL_ACTION_LOCK_SCREEN                             | 28      |
| GLOBAL_ACTION_MEDIA_PLAY_PAUSE  | Play/pause media                                       | *(SDK 36 pending)*                                     | 22–36   |
| GLOBAL_ACTION_MENU              | Trigger Menu key                                       | *(SDK 36 pending)*                                     | 21–36   |
| GLOBAL_ACTION_NOTIFICATIONS     | Open notifications                                     | GLOBAL_ACTION_NOTIFICATIONS                           | 16      |
| GLOBAL_ACTION_POWER_DIALOG      | Open power dialog                                      | GLOBAL_ACTION_POWER_DIALOG                            | 21      |
| GLOBAL_ACTION_QUICK_SETTINGS    | Open quick settings                                    | GLOBAL_ACTION_QUICK_SETTINGS                          | 17      |
| GLOBAL_ACTION_RECENTS           | Open recent apps                                       | GLOBAL_ACTION_RECENTS                                 | 16      |
| GLOBAL_ACTION_TAKE_SCREENSHOT   | Take screenshot                                        | GLOBAL_ACTION_TAKE_SCREENSHOT                         | 28      |
| GLOBAL_ACTION_TOGGLE_SPLIT_SCREEN | Toggle split-screen mode                             | GLOBAL_ACTION_TOGGLE_SPLIT_SCREEN                     | 24      |

---

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

