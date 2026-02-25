# Screen Automator — ClickInText Series (State-Machine Mode)

## Summary

- **Internal name**: 'SCREEN_AUTOMATOR_SERIES'
- **JSON tag**: '"ScreenAutomatorSeries"'
- **Category**: Screen Automation / Accessibility
- **Purpose**: Open a target screen (via Intent parameters) and then execute **a fast, state-machine-driven ClickInText sequence** on Samsung devices.

This task allows an AndroMate workflow to automatically click multiple UI elements **based on their text**, such as:

- “Next”
- “Allow”
- “OK”
- “Continue”
- “Finish”

Unlike standard Screen Automator actions, this feature works internally as a **state machine**.  
Each click transitions to the **next step only when the system sends a callback event** confirming UI changes.

➡️ This makes the execution **much faster and more reliable** compared to polling-based automation.

## ⚠ Important Warning

This feature relies on the **Android Accessibility Service**.

- It has been **tested and validated only on Samsung devices** (One UI 6.x / 7.x / 8.x).
- Other manufacturers **may behave differently**
- Some OEMs have **unstable or restricted Accessibility implementations**

🚨 In very rare cases, on non‑Samsung devices:

- the Accessibility service may crash at the system level
- this crash **cannot be handled or recovered by AndroMate**
- the user may need to manually restart the accessiblity permission or reboot the device

For production usage, **Samsung devices are strongly recommended**.

## Compatibility

- **Minimum AndroMate version**: '{{ ANDROMATE_FIRST_VERSION }}'
- **Maximum AndroMate version**: '{{ ANDROMATE_CURRENT_VERSION }}'
- **Minimum Android**: '{{ ANDROMATE_MIN_APP_SDK }}'
- **Maximum Android tested**: '{{ ANDROID_CURRENT_APP_SDK }}'

### Supported manufacturers

- ✅ **Samsung only (fully supported)**
- ⚠ Other manufacturers: **not guaranteed / unstable in some cases**

### Required permissions

- 'ACCESSIBILITY_SERVICE'
- Any permissions required by the target Activity started via Intent

## How it works

  - 'Action'
  - 'PackageName'
  - 'ClassName'
1. The task **optionally launches a target Activity** using Intent parameters:
2. Once the Activity is visible, the **ClickInText sequence executes**
3. Each step waits for a **system-level callback event**
4. When confirmed, the state machine advances to the **next click**
  - all clicks succeed, or
  - a timeout/error occurs
5. Execution ends when:

This design avoids heavy UI scanning loops → **making automation faster and smoother on Samsung devices.**

## Input parameters

- Parameter: `Action` | Type: String | Required: No | Rules / Possible values: Intent action (`android.intent.action.*` or custom) | Android compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `""`
- Parameter: `PackageName` | Type: String | Required: No | Rules / Possible values: Valid package name (`com.example.app`) | Android compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `""`
- Parameter: `ClassName` | Type: String | Required: No | Rules / Possible values: Fully qualified Activity class name | Android compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `""`
- Parameter: `command` | Type: JSON Array | Required: Yes | Rules / Possible values: Array of ClickInText commands (see next section) | Android compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `[]`

If an Activity is supplied, it is started **before** the click sequence begins.

## Output parameters

Returns a **'ScreenAutomatorResult'**:

- 'automatorResult': 'true' if all clicks completed successfully
- 'errorMsg': description in case of error or timeout

No workflow variables are produced.

# Parameter details

## 1. `command` (ClickInText sequence)

The 'command' field contains an ordered list of text-based click actions.

### Command entry format

- Field: `ClickInText_textSelector` | Type: String | Required: Yes | Description: Text source: `Text`, `contentDescription`, `tooltipText` | Default: `""`
- Field: `ClickInText_CompareType` | Type: String | Required: Yes | Description: Comparison mode: `exactText`, `startWith`, `Contain` | Default: `""`
- Field: `ClickInText_Index` | Type: Number | Required: No | Description: Index when multiple matches exist | Default: `0`
- Field: `ClickInText_text` | Type: String | Required: Yes | Description: Target UI text | Default: `""`

Example:

"command": [
  {
    "ClickInText_textSelector": "Text",
    "ClickInText_CompareType": "exactText",
    "ClickInText_Index": 0,
    "ClickInText_text": "Next"
  },
  {
    "ClickInText_textSelector": "Text",
    "ClickInText_CompareType": "exactText",
    "ClickInText_Index": 0,
    "ClickInText_text": "Allow"
  }
]

## Execution model (State Machine)

Start
  ↓
(Optional) Launch Activity via Intent
  ↓
Wait for UI ready callback
  ↓
Click #1 (text match)
  ↓
Wait for system event
  ↓
Click #2
  ↓
…repeat…
  ↓
Success or Timeout

Each transition is **event-driven**, not timer-driven.

## Exceptions

- Code: SCREEN-AUTOMATOR-ERROR-007 | Exception Name: INVALID_JSON_ARRAY | Description: `command` array is missing, null, invalid, or empty
- Code: SCREEN-AUTOMATOR-ERROR-008 | Exception Name: TIME_OUT | Description: Screen Automator series execution timeout expired
- Code: ERROR-000 | Exception Name: OTHER_ERROR | Description: Unexpected runtime or internal error

## Complete JSON example

{
  "ScreenAutomatorSeries": [
    {
      "id": "200",
      "title": "Samsung Setup Wizard Auto-Confirm",
      "Action": "android.settings.SETTINGS",
      "PackageName": "com.android.settings",
      "ClassName": "com.android.settings.Settings",
      "command": [
        {
          "ClickInText_textSelector": "Text",
          "ClickInText_CompareType": "exactText",
          "ClickInText_Index": 0,
          "ClickInText_text": "Next"
        },
        {
          "ClickInText_textSelector": "Text",
          "ClickInText_CompareType": "exactText",
          "ClickInText_Index": 0,
          "ClickInText_text": "Agree"
        },
        {
          "ClickInText_textSelector": "Text",
          "ClickInText_CompareType": "Contain",
          "ClickInText_Index": 0,
          "ClickInText_text": "Finish"
        }
      ]
    }
  ]
}