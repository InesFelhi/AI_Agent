# Get Battery Status

## Summary

- **Internal name**: `GetBatteryStatus`
- **Category**: Battery
- **Purpose**: Read the current battery charging status. Returns a human-readable string such as `Charging`, `Discharging`, `Full`, or `Not Charging`.
- **Task type**: Normal

## Compatibility

- **Minimum AndroMate version**: `{{ ANDROMATE_FIRST_VERSION }}`
- **Maximum AndroMate version**: `{{ ANDROMATE_CURRENT_VERSION }}`
- **Minimum Android**: `{{ ANDROMATE_MIN_APP_SDK }}`
- **Maximum Android tested**: `{{ ANDROID_CURRENT_APP_SDK }}`
- **Required permissions**: None

## Detailed description

The **Get Battery Status** task reads the current charging status from the Android battery broadcast (`ACTION_BATTERY_CHANGED`). The result is a descriptive string stored in `value_output`.

No special permissions are required — `ACTION_BATTERY_CHANGED` is a protected system broadcast available to all apps.

## Input parameters

This task has no input parameters.

## Output parameters

- Field: `value_output` | Type: String | Trigger condition: Always on success — one of `Charging`, `Discharging`, `Full`, `Not Charging`, `Unknown` | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`

### Possible output values

- Value: `Charging` | Description: The device is currently charging
- Value: `Discharging` | Description: The battery is draining — not connected to a charger
- Value: `Full` | Description: The battery is fully charged
- Value: `Not Charging` | Description: Connected to a charger but not charging (e.g. damaged battery)
- Value: `Unknown` | Description: The status could not be determined

## Special variables

When comparing the output of this task in a condition (e.g. **Compare Strings**), you can use the built-in AndroMate special variables instead of hardcoded strings. This avoids typos and keeps your workflow readable.

- Special variable: `${BATTERY_STATUS_CHARGING}` | Resolved value: `"Charging"`
- Special variable: `${BATTERY_STATUS_DISCHARGING}` | Resolved value: `"Discharging"`
- Special variable: `${BATTERY_STATUS_FULL}` | Resolved value: `"Full"`
- Special variable: `${BATTERY_STATUS_NOT_CHARGING}` | Resolved value: `"Not Charging"`
- Special variable: `${BATTERY_STATUS_UNKNOWN}` | Resolved value: `"Unknown"`

**Example** — compare `$battery_status` against `${BATTERY_STATUS_CHARGING}` in a Compare Strings task instead of typing `"Charging"` manually.

## Exceptions

This task does not throw exceptions. If the status cannot be read, `"Unknown"` is stored in `value_output`.

## Execution flowchart

Diagram Nodes:
- Register: 📡 Register ACTION_BATTERY_CHANGED\none-shot receiver
- ReadStatus: 🔋 Read EXTRA_STATUS\nmap to string
- StoreResult: 💾 Set value_output\nStrTaskResult
- LogReport: 📋 Log report

Workflow Flow:
- 📡 Register ACTION_BATTERY_CHANGED\none-shot receiver → 🔋 Read EXTRA_STATUS\nmap to string
- 🔋 Read EXTRA_STATUS\nmap to string → 💾 Set value_output\nStrTaskResult
- 💾 Set value_output\nStrTaskResult → 📋 Log report
- 📋 Log report → Success

**How it works:**

1. **Register battery receiver**: registers a one-shot receiver for `ACTION_BATTERY_CHANGED`
2. **Read status**: extracts `EXTRA_STATUS` and maps it to a descriptive string
3. **Store result**: sets `value_output` with the status string
4. **Result**: returns `StrTaskResult`

## Code examples

### Example 1 — Read battery status

```json
{
  "GetBatteryStatus": [
    {
      "id": "1",
      "title": "Check battery status",
      "value_output": "$battery_status"
    }
  ]
}
```

## Input parameter details

This task has no input parameters.

## Output parameter details

### `value_output` — Battery charging status

Stores the charging status as a descriptive string in the specified workflow variable.

- One of `Charging`, `Discharging`, `Full`, `Not Charging`, `Unknown`
- If the status cannot be determined, `"Unknown"` is stored
- Tip: compare against the `${BATTERY_STATUS_*}` special variables instead of hardcoded strings

## Complete JSON example

```json
{
  "GetBatteryStatus": [
    {
      "id": "1",
      "title": "Get Battery Status",
      "value_output": "$BATTERY_STATUS"
    }
  ]
}
```