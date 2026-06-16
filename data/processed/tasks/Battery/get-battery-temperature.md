# Get Battery Temperature

## Summary

- **Internal name**: `GetBatteryTemperature`
- **Category**: Battery
- **Purpose**: Read the current battery temperature in degrees Celsius. Useful for detecting overheating conditions during automated tests.
- **Task type**: Normal

## Compatibility

- **Minimum AndroMate version**: `{{ ANDROMATE_FIRST_VERSION }}`
- **Maximum AndroMate version**: `{{ ANDROMATE_CURRENT_VERSION }}`
- **Minimum Android**: `{{ ANDROMATE_MIN_APP_SDK }}`
- **Maximum Android tested**: `{{ ANDROID_CURRENT_APP_SDK }}`
- **Required permissions**: None

## Detailed description

The **Get Battery Temperature** task reads the battery temperature from the Android battery broadcast (`ACTION_BATTERY_CHANGED`). Android reports temperature in tenths of a degree Celsius (e.g. `365` = 36.5 °C), which this task converts to a decimal string before storing in `value_output`.

No special permissions are required — `ACTION_BATTERY_CHANGED` is a protected system broadcast available to all apps.

## Input parameters

This task has no input parameters.

## Output parameters

- Field: `value_output` | Type: String | Trigger condition: Always on success — battery temperature as a decimal string in °C (e.g. `"36.5"`) | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`

## Exceptions

This task does not throw exceptions. If the temperature cannot be read, Android returns `0`, which is stored as `"0.0"` in `value_output`.

## Execution flowchart

Diagram Nodes:
- Register: 📡 Register ACTION_BATTERY_CHANGED\none-shot receiver
- ReadTemp: 🌡️ Read EXTRA_TEMPERATURE\ndivide by 10.0
- StoreResult: 💾 Set value_output\nStrTaskResult
- LogReport: 📋 Log report

Workflow Flow:
- 📡 Register ACTION_BATTERY_CHANGED\none-shot receiver → 🌡️ Read EXTRA_TEMPERATURE\ndivide by 10.0
- 🌡️ Read EXTRA_TEMPERATURE\ndivide by 10.0 → 💾 Set value_output\nStrTaskResult
- 💾 Set value_output\nStrTaskResult → 📋 Log report
- 📋 Log report → Success

**How it works:**

1. **Register battery receiver**: registers a one-shot receiver for `ACTION_BATTERY_CHANGED`
2. **Read temperature**: extracts `EXTRA_TEMPERATURE` (in tenths of °C) and divides by `10.0`
3. **Store result**: sets `value_output` with the temperature string in °C
4. **Result**: returns `StrTaskResult`

## Code examples

### Example 1 — Read battery temperature

```json
{
  "GetBatteryTemperature": [
    {
      "id": "1",
      "title": "Check battery temperature",
      "value_output": "$battery_temp"
    }
  ]
}
```

## Input parameter details

This task has no input parameters.

## Output parameter details

### `value_output` — Battery temperature in °C

Stores the battery temperature as a decimal string in degrees Celsius.

- Example: `"36.5"` means 36.5 °C
- Typical range: `20.0` to `45.0` under normal conditions
- Android provides the value in tenths of a degree — this task divides by `10.0` automatically

## Complete JSON example

```json
{
  "GetBatteryTemperature": [
    {
      "id": "1",
      "title": "Get Battery Temperature",
      "value_output": "$BATTERY_TEMP"
    }
  ]
}
```