# Get Battery Voltage

## Summary

- **Internal name**: `GetBatteryVoltage`
- **Category**: Battery
- **Purpose**: Read the current battery voltage in millivolts (mV). Useful for hardware diagnostics and battery health monitoring.
- **Task type**: Normal

## Compatibility

- **Minimum AndroMate version**: `{{ ANDROMATE_FIRST_VERSION }}`
- **Maximum AndroMate version**: `{{ ANDROMATE_CURRENT_VERSION }}`
- **Minimum Android**: `{{ ANDROMATE_MIN_APP_SDK }}`
- **Maximum Android tested**: `{{ ANDROID_CURRENT_APP_SDK }}`
- **Required permissions**: None

## Detailed description

The **Get Battery Voltage** task reads the current battery voltage from the Android battery broadcast (`ACTION_BATTERY_CHANGED`). The voltage is returned in millivolts as a numeric string (e.g. `"4200"` for 4.2 V) and stored in `value_output`.

No special permissions are required — `ACTION_BATTERY_CHANGED` is a protected system broadcast available to all apps.

## Input parameters

This task has no input parameters.

## Output parameters

- Field: `value_output` | Type: String | Trigger condition: Always on success — battery voltage in millivolts as a numeric string (e.g. `"4200"`) | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`

## Exceptions

This task does not throw exceptions. If the voltage cannot be read, Android returns `0`, which is stored as `"0"` in `value_output`.

## Execution flowchart

Diagram Nodes:
- Register: 📡 Register ACTION_BATTERY_CHANGED\none-shot receiver
- ReadVoltage: ⚡ Read EXTRA_VOLTAGE\nin millivolts
- StoreResult: 💾 Set value_output\nStrTaskResult
- LogReport: 📋 Log report

Workflow Flow:
- 📡 Register ACTION_BATTERY_CHANGED\none-shot receiver → ⚡ Read EXTRA_VOLTAGE\nin millivolts
- ⚡ Read EXTRA_VOLTAGE\nin millivolts → 💾 Set value_output\nStrTaskResult
- 💾 Set value_output\nStrTaskResult → 📋 Log report
- 📋 Log report → Success

**How it works:**

1. **Register battery receiver**: registers a one-shot receiver for `ACTION_BATTERY_CHANGED`
2. **Read voltage**: extracts `EXTRA_VOLTAGE` in millivolts
3. **Store result**: sets `value_output` with the voltage string in mV
4. **Result**: returns `StrTaskResult`

## Code examples

### Example 1 — Read battery voltage

```json
{
  "GetBatteryVoltage": [
    {
      "id": "1",
      "title": "Read battery voltage",
      "value_output": "$battery_voltage"
    }
  ]
}
```

## Input parameter details

This task has no input parameters.

## Output parameter details

### `value_output` — Battery voltage in mV

Stores the battery voltage as a numeric string in millivolts.

- Example: `"4200"` means 4.2 V (4200 mV)
- Typical range: `3200` mV (nearly empty) to `4350` mV (fully charged), varies by battery chemistry
- Divide by `1000` in a workflow to convert to volts

## Complete JSON example

```json
{
  "GetBatteryVoltage": [
    {
      "id": "1",
      "title": "Get Battery Voltage",
      "value_output": "$BATTERY_VOLTAGE"
    }
  ]
}
```