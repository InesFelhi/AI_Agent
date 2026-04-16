# Screen Automator — ClickInXY

## Summary

- **Internal name**: `SCREEN_AUTOMATOR`
- **Category**: Screen Automation / Accessibility
- **Purpose**: Perform a tap at specific screen coordinates (X, Y) on the device.

This task allows an AndroMate workflow to simulate precise touch input regardless of UI text or structure.  
Useful for automating clicks on custom UI components, games, images, dynamic layouts, and elements without accessibility labels.

⚠️ **Important limitation:** Some Android firmwares ignore ClickInXY events on certain system-protected areas.  
Examples include:

- **System update dialogs**
- **APK install/update confirmation buttons on Android 16+**
- **Secure or restricted UI overlays (OEM-level protections)**

This is enforced by the Android security model and **cannot be bypassed**.

## Compatibility

- **Minimum AndroMate version**: `{{ ANDROMATE_FIRST_VERSION }}`
- **Maximum AndroMate version**: `{{ ANDROMATE_CURRENT_VERSION }}`
- **Minimum Android**: `{{ ANDROMATE_MIN_APP_SDK }}`
- **Maximum Android tested**: `{{ ANDROID_CURRENT_APP_SDK }}`

### Supported manufacturers

- ✅ Samsung (One UI 6.x / 7.x / 8.x)

### Required permissions

- `ACCESSIBILITY_SERVICE`
- (Optional) `SYSTEM_ALERT_WINDOW` for overlay interactions

## Detailed description

The **ClickInXY** mode of ScreenAutomator triggers a physical-style **tap** at a specific coordinate `(x, y)`.

It is essential when:

- UI elements do **not** expose any accessibility text
- The interface is custom-rendered (Canvas, OpenGL, Unity, game UIs)
- A workflow must press an exact pixel location
- Buttons are graphical only (icons, images, etc.)

⚠️ **Coordinates are absolute** and require calibration per device.  
They do **not** scale automatically with:

- resolution
- screen density
- rotation

## Input parameters

- Parameter: `Action_type` | Type: Enum | Required: Yes | Possible values: Must be `"ClickInXY"` | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: —
- Parameter: `ClickInXY_X` | Type: Integer | Required: Yes | Possible values: X ≥ 0 | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: —
- Parameter: `ClickInXY_Y` | Type: Integer | Required: Yes | Possible values: Y ≥ 0 | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: —

## Output parameters

The ClickInXY mode does **not** produce outputs.  
It simply performs the system interaction.

# Parameter details

## 1. `Action_type`

Must be exactly `"ClickInXY"`.

### Example

```json
"Action_type": "ClickInXY"
```

## 2. `ClickInXY_X`

The **horizontal coordinate** of the tap.

### Example

```json
"ClickInXY_X": 540
```

## 3. `ClickInXY_Y`

The **vertical coordinate** of the tap.

### Example

```json
"ClickInXY_Y": 1250
```

## Exceptions

- Code: SCREEN-AUTOMATOR-ERROR-003 | Exception Name: INVALID_ACTION_TYPE | Description: Invalid action type (must be `ClickInXY`)
- Code: SCREEN-AUTOMATOR-ERROR-004 | Exception Name: INVALID_X_Y_INPUT | Description: Invalid X / Y coordinates (values must be ≥ 0 and within the screen bounds)
- Code: SCREEN-AUTOMATOR-ERROR-007 | Exception Name: INVALID_JSON_ARRAY | Description: Invalid or malformed JSON array received for input parameters
- Code: SCREEN-AUTOMATOR-ERROR-008 | Exception Name: TIME_OUT | Description: Execution of the click action exceeded the allowed timeout

# Complete JSON example

```json
{
  "ScreenAutomator": [
    {
      "id": "20",
      "title": "Tap Center Screen",
      "Action_type": "ClickInXY",
      "ClickInXY_X": 540,
      "ClickInXY_Y": 1200
    },
    {
      "id": "21",
      "title": "Tap Top Right Corner",
      "Action_type": "ClickInXY",
      "ClickInXY_X": 1000,
      "ClickInXY_Y": 200
    },
    {
      "id": "22",
      "title": "Tap Bottom Menu Region",
      "Action_type": "ClickInXY",
      "ClickInXY_X": 540,
      "ClickInXY_Y": 2000
    }
  ]
}
```