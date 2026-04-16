# Screen Automator — ClickInText

## Summary

- **Internal name**: `SCREEN_AUTOMATOR`
- **Category**: Screen Automation / Accessibility
- **Purpose**: Perform a click on a UI element detected by its visible or accessible text.
- **Task type**: Normal

This task allows an AndroMate workflow to interact with UI components based on **text**, **contentDescription**, or **tooltipText**.  
It is essential for automating dialogs, buttons, menus, settings screens, permissions, and any UI exposing readable information through Accessibility.

⚠️ **Important limitation:**  
Some OEM firmwares or system dialogs may hide or block accessibility events. Examples:

- **System-level permission dialogs**
- **Install/Update security dialogs on Android 16+**
- **OEM-protected UI layers (Samsung Knox, MIUI, etc.)**

If text is not detectable by Accessibility, the ClickInText action cannot work.

## Compatibility

- **Minimum AndroMate version**: `{{ ANDROMATE_FIRST_VERSION }}`
- **Maximum AndroMate version**: `{{ ANDROMATE_CURRENT_VERSION }}`
- **Minimum Android version**: `{{ ANDROMATE_MIN_APP_SDK }}`
- **Maximum Android tested**: `{{ ANDROID_CURRENT_APP_SDK }}`

### Supported manufacturers

- ✅ Samsung (One UI 6.x / 7.x / 8.x)

### Required permissions

- `ACCESSIBILITY_SERVICE`
- (Optional) `SYSTEM_ALERT_WINDOW` if overlays are used

## Detailed description

The **ClickInText** mode of ScreenAutomator searches visible elements using:

- `Text` (visible label)
- `contentDescription`
- `tooltipText`

Then it performs a click when a matching element is found according to the chosen comparison rule.

It is essential when:

- UI elements have text or accessibility labels
- Action buttons must be automated reliably
- Resolution‑independent interaction is required
- Structured UI hierarchy is available

Examples include:

- Clicking dialogs like **“OK”**, **“Allow”**, **“Retry”**
- Clicking setup wizard buttons
- Navigating menus in Settings
- Selecting labeled items in apps

## Input parameters

- Parameter: `Action_type` | Type: Enum | Required: Yes | Possible values: Must be `"ClickInText"` | Android Compatibility: All supported versions | AndroMate Compatibility: All supported versions | Default: —
- Parameter: `TextSelector` | Type: Enum | Required: Yes | Possible values: `Text`, `contentDescription`, `tooltipText` | Android Compatibility: All supported versions | AndroMate Compatibility: All supported versions | Default: —
- Parameter: `CompareType` | Type: Enum | Required: Yes | Possible values: `exactText`, `startWith`, `Contain` | Android Compatibility: All supported versions | AndroMate Compatibility: All supported versions | Default: —
- Parameter: `index` | Type: String | Required: No | Possible values: `"0"`, `"1"`, `"2"`, ... | Android Compatibility: All supported versions | AndroMate Compatibility: All supported versions | Default: `"0"`
- Parameter: `enterText` | Type: String | Required: No | Possible values: Any text to input after clicking | Android Compatibility: Requires keyboard | AndroMate Compatibility: All supported versions | Default: `""`

## Output parameters

ClickInText does **not return any output**.  
Its purpose is interaction, not data extraction.

# Parameter details

## 1. `Action_type`

Must be exactly:

```json
"Action_type": "ClickInText"
```

## 2. `TextSelector`

Defines **where** the text is taken from.

- Enum name: `TEXT_SELECTOR` | Angular value: `"Text"` | Description: Matches the visible text on a UI element.
- Enum name: `CONTENT_DESCRIPTION` | Angular value: `"contentDescription"` | Description: Matches accessibility descriptions (often hidden visually).
- Enum name: `TOOL_TIP_TEXT` | Angular value: `"tooltipText"` | Description: Matches tooltip text if provided by the app.

### Example

```json
"TextSelector": "Text"
```

## 3. `CompareType`

Defines **how** the text comparison is done.

- Enum name: `EXACT_TEXT` | Angular text value: `"exactText"` | Description: Match only if text is exactly equal.
- Enum name: `START_WITH` | Angular text value: `"startWith"` | Description: Match if element begins with the provided text.
- Enum name: `CONTAIN` | Angular text value: `"Contain"` | Description: Match if the text contains the provided value.

### Example

```json
"CompareType": "Contain"
```

## 4. `index`

If multiple elements match, this selects the nth one.

### Example

```json
"index": "1"
```

## 5. `enterText`

Optional text to enter after clicking, if the target is editable.

### Example

```json
"enterText": "username123"
```

## Exceptions

- Code: SCREEN-AUTOMATOR-ERROR-003 | Exception Name: INVALID_ACTION_TYPE | Description: Invalid action type (must be `ClickInText`)
- Code: SCREEN-AUTOMATOR-ERROR-006 | Exception Name: UNSUPPORTED_TEXT_SELECTOR | Description: The provided text selector is not supported
- Code: SCREEN-AUTOMATOR-ERROR-007 | Exception Name: INVALID_JSON_ARRAY | Description: Invalid or malformed JSON array was provided as input
- Code: SCREEN-AUTOMATOR-ERROR-008 | Exception Name: TIME_OUT | Description: Execution of the text-based click exceeded the allowed timeout

# Complete JSON example

```json
{
  "ScreenAutomator": [
    {
      "id": "31",
      "title": "Click Allow",
      "Action_type": "ClickInText",
      "TextSelector": "Text",
      "CompareType": "exactText",
      "index": "0",
      "enterText": "Allow"
    },
    {
      "id": "32",
      "title": "Click OK Button",
      "Action_type": "ClickInText",
      "TextSelector": "contentDescription",
      "CompareType": "Contain",
      "index": "0",
      "enterText": "OK"
    },
    {
      "id": "33",
      "title": "Input Username",
      "Action_type": "ClickInText",
      "TextSelector": "Text",
      "CompareType": "startWith",
      "index": "0",
      "enterText": "andromate_user"
    }
  ]
}
```