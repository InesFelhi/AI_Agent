# Get Charging Type

## Summary

- **Internal name**: `GetChargingType`
- **Category**: Battery
- **Purpose**: Read the type of charger currently connected to the device. Returns `USB`, `AC`, `Wireless`, or `None`.
- **Task type**: Normal

## Compatibility

- **Minimum AndroMate version**: `{{ ANDROMATE_FIRST_VERSION }}`
- **Maximum AndroMate version**: `{{ ANDROMATE_CURRENT_VERSION }}`
- **Minimum Android**: `{{ ANDROMATE_MIN_APP_SDK }}`
- **Maximum Android tested**: `{{ ANDROID_CURRENT_APP_SDK }}`
- **Required permissions**: None

## Detailed description

The **Get Charging Type** task reads the charger type from the Android battery broadcast (`ACTION_BATTERY_CHANGED`). The result indicates whether the device is connected via USB, an AC wall adapter, wireless charging, or is not connected to any charger. The result is stored as a string in `value_output`.

No special permissions are required — `ACTION_BATTERY_CHANGED` is a protected system broadcast available to all apps.

## Input parameters

This task has no input parameters.

## Output parameters

- Field: `value_output` | Type: String | Trigger condition: Always on success — one of `USB`, `AC`, `Wireless`, `None` | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`

### Possible output values

- Value: `USB` | Description: Device is charging via a USB connection
- Value: `AC` | Description: Device is charging via an AC wall adapter
- Value: `Wireless` | Description: Device is charging wirelessly (Qi or similar)
- Value: `None` | Description: No charger is connected

## Special variables

When comparing the output of this task in a condition (e.g. **Compare Strings**), you can use the built-in AndroMate special variables instead of hardcoded strings. This avoids typos and keeps your workflow readable.

- Special variable: `${CHARGING_TYPE_USB}` | Resolved value: `"USB"`
- Special variable: `${CHARGING_TYPE_AC}` | Resolved value: `"AC"`
- Special variable: `${CHARGING_TYPE_WIRELESS}` | Resolved value: `"Wireless"`
- Special variable: `${CHARGING_TYPE_NONE}` | Resolved value: `"None"`

**Example** — compare `$charging_type` against `${CHARGING_TYPE_AC}` in a Compare Strings task instead of typing `"AC"` manually.

## Exceptions

This task does not throw exceptions. If no charger is connected, `"None"` is stored in `value_output`.

## Execution flowchart

Diagram Nodes:
- Register: 📡 Register ACTION_BATTERY_CHANGED\none-shot receiver
- ReadPlugged: 🔌 Read EXTRA_PLUGGED\nmap to string
- StoreResult: 💾 Set value_output\nStrTaskResult
- LogReport: 📋 Log report

Workflow Flow:
- 📡 Register ACTION_BATTERY_CHANGED\none-shot receiver → 🔌 Read EXTRA_PLUGGED\nmap to string
- 🔌 Read EXTRA_PLUGGED\nmap to string → 💾 Set value_output\nStrTaskResult
- 💾 Set value_output\nStrTaskResult → 📋 Log report
- 📋 Log report → Success

**How it works:**

1. **Register battery receiver**: registers a one-shot receiver for `ACTION_BATTERY_CHANGED`
2. **Read plugged state**: extracts `EXTRA_PLUGGED` and maps the integer constant to a charger type string
3. **Store result**: sets `value_output` with the charger type string
4. **Result**: returns `StrTaskResult`

## Code examples

### Example 1 — Read charging type

```json
{
  "GetChargingType": [
    {
      "id": "1",
      "title": "Check charger type",
      "value_output": "$charging_type"
    }
  ]
}
```

## Input parameter details

This task has no input parameters.

## Output parameter details

### `value_output` — Charger type

Stores the connected charger type as a string in the specified workflow variable.

- One of `USB`, `AC`, `Wireless`, `None`
- `None` means no charger is connected
- Tip: compare against the `${CHARGING_TYPE_*}` special variables instead of hardcoded strings

## Complete JSON example

```json
{
  "GetChargingType": [
    {
      "id": "1",
      "title": "Get Charging Type",
      "value_output": "$CHARGING_TYPE"
    }
  ]
}
```