# Get Battery Level

## Summary

- **Internal name**: `GetBatteryLevel`
- **Category**: Battery
- **Purpose**: Read the current battery charge level as a percentage. Returns a value between 0 and 100.
- **Task type**: Normal

## Compatibility

- **Minimum AndroMate version**: `{{ ANDROMATE_FIRST_VERSION }}`
- **Maximum AndroMate version**: `{{ ANDROMATE_CURRENT_VERSION }}`
- **Minimum Android**: `{{ ANDROMATE_MIN_APP_SDK }}`
- **Maximum Android tested**: `{{ ANDROID_CURRENT_APP_SDK }}`
- **Required permissions**: None

## Detailed description

The **Get Battery Level** task reads the current battery charge level from the Android battery broadcast (`ACTION_BATTERY_CHANGED`). The level is expressed as a percentage from `0` (empty) to `100` (full) and is stored as a string in `value_output`.

No special permissions are required — `ACTION_BATTERY_CHANGED` is a protected system broadcast that any app can receive without declaring permissions.

## Input parameters

This task has no input parameters.

## Output parameters

- Field: `value_output` | Type: String | Trigger condition: Always on success — battery percentage as a numeric string (e.g. `"85"`) | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`

## Exceptions

This task does not throw exceptions. If the battery level cannot be read, Android returns `-1`, which is stored as `"-1"` in `value_output`.

## Execution flowchart

Diagram Nodes:
- Register: 📡 Register ACTION_BATTERY_CHANGED\none-shot receiver
- ReadLevel: 🔋 Read EXTRA_LEVEL / EXTRA_SCALE\ncompute percentage
- StoreResult: 💾 Set value_output\nStrTaskResult
- LogReport: 📋 Log report

Workflow Flow:
- 📡 Register ACTION_BATTERY_CHANGED\none-shot receiver → 🔋 Read EXTRA_LEVEL / EXTRA_SCALE\ncompute percentage
- 🔋 Read EXTRA_LEVEL / EXTRA_SCALE\ncompute percentage → 💾 Set value_output\nStrTaskResult
- 💾 Set value_output\nStrTaskResult → 📋 Log report
- 📋 Log report → Success

**How it works:**

1. **Register battery receiver**: registers a one-shot receiver for `ACTION_BATTERY_CHANGED` — no permission required
2. **Read level**: extracts `EXTRA_LEVEL` and `EXTRA_SCALE` from the battery intent and computes `(level * 100) / scale`
3. **Store result**: sets `value_output` with the percentage string
4. **Result**: returns `StrTaskResult`

## Code examples

### Example 1 — Read battery level into a variable

```json
{
  "GetBatteryLevel": [
    {
      "id": "1",
      "title": "Read battery percentage",
      "value_output": "$battery_level"
    }
  ]
}
```

### Example 2 — Read battery level without storing

```json
{
  "GetBatteryLevel": [
    {
      "id": "2",
      "title": "Read battery level"
    }
  ]
}
```

## Input parameter details

This task has no input parameters.

## Output parameter details

### `value_output` — Battery level percentage

Stores the battery level as a numeric string in the specified workflow variable.

- Range: `"0"` (empty) to `"100"` (full)
- Example: `"85"` means 85 % battery remaining
- If the level cannot be determined, Android returns `-1`

## Complete JSON example

```json
{
  "GetBatteryLevel": [
    {
      "id": "1",
      "title": "Get Battery Level",
      "value_output": "$BATTERY_LEVEL"
    }
  ]
}
```