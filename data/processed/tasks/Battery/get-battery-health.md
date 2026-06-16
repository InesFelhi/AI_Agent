# Get Battery Health

## Summary

- **Internal name**: `GetBatteryHealth`
- **Category**: Battery
- **Purpose**: Read the current battery health status. Returns a descriptive string such as `Good`, `Overheat`, `Dead`, `Over Voltage`, or `Cold`.
- **Task type**: Normal

## Compatibility

- **Minimum AndroMate version**: `{{ ANDROMATE_FIRST_VERSION }}`
- **Maximum AndroMate version**: `{{ ANDROMATE_CURRENT_VERSION }}`
- **Minimum Android**: `{{ ANDROMATE_MIN_APP_SDK }}`
- **Maximum Android tested**: `{{ ANDROID_CURRENT_APP_SDK }}`
- **Required permissions**: None

## Detailed description

The **Get Battery Health** task reads the battery health indicator from the Android battery broadcast (`ACTION_BATTERY_CHANGED`). The result is a human-readable string stored in `value_output`, making it easy to detect degraded or unsafe battery conditions during automated monitoring workflows.

No special permissions are required — `ACTION_BATTERY_CHANGED` is a protected system broadcast available to all apps.

## Input parameters

This task has no input parameters.

## Output parameters

- Field: `value_output` | Type: String | Trigger condition: Always on success — one of `Good`, `Overheat`, `Dead`, `Over Voltage`, `Cold`, `Unknown` | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`

### Possible output values

- Value: `Good` | Description: Battery is functioning normally
- Value: `Overheat` | Description: Battery temperature is too high
- Value: `Dead` | Description: Battery is dead and cannot be used
- Value: `Over Voltage` | Description: Battery voltage is above safe limits
- Value: `Cold` | Description: Battery temperature is too low
- Value: `Unknown` | Description: Health status cannot be determined

## Special variables

When comparing the output of this task in a condition (e.g. **Compare Strings**), you can use the built-in AndroMate special variables instead of hardcoded strings. This avoids typos and keeps your workflow readable.

- Special variable: `${BATTERY_HEALTH_GOOD}` | Resolved value: `"Good"`
- Special variable: `${BATTERY_HEALTH_OVERHEAT}` | Resolved value: `"Overheat"`
- Special variable: `${BATTERY_HEALTH_DEAD}` | Resolved value: `"Dead"`
- Special variable: `${BATTERY_HEALTH_OVER_VOLTAGE}` | Resolved value: `"Over Voltage"`
- Special variable: `${BATTERY_HEALTH_COLD}` | Resolved value: `"Cold"`
- Special variable: `${BATTERY_HEALTH_UNKNOWN}` | Resolved value: `"Unknown"`

**Example** — compare `$battery_health` against `${BATTERY_HEALTH_GOOD}` in a Compare Strings task instead of typing `"Good"` manually.

## Exceptions

This task does not throw exceptions. If the health status cannot be read, `"Unknown"` is stored in `value_output`.

## Execution flowchart

Diagram Nodes:
- Register: 📡 Register ACTION_BATTERY_CHANGED\none-shot receiver
- ReadHealth: 🔋 Read EXTRA_HEALTH\nmap to string
- StoreResult: 💾 Set value_output\nStrTaskResult
- LogReport: 📋 Log report

Workflow Flow:
- 📡 Register ACTION_BATTERY_CHANGED\none-shot receiver → 🔋 Read EXTRA_HEALTH\nmap to string
- 🔋 Read EXTRA_HEALTH\nmap to string → 💾 Set value_output\nStrTaskResult
- 💾 Set value_output\nStrTaskResult → 📋 Log report
- 📋 Log report → Success

**How it works:**

1. **Register battery receiver**: registers a one-shot receiver for `ACTION_BATTERY_CHANGED`
2. **Read health**: extracts `EXTRA_HEALTH` and maps the integer constant to a descriptive string
3. **Store result**: sets `value_output` with the health string
4. **Result**: returns `StrTaskResult`

## Code examples

### Example 1 — Read battery health

```json
{
  "GetBatteryHealth": [
    {
      "id": "1",
      "title": "Check battery health",
      "value_output": "$battery_health"
    }
  ]
}
```

## Input parameter details

This task has no input parameters.

## Output parameter details

### `value_output` — Battery health

Stores the battery health as a descriptive string in the specified workflow variable.

- One of `Good`, `Overheat`, `Dead`, `Over Voltage`, `Cold`, `Unknown`
- If the health cannot be determined, `"Unknown"` is stored
- Tip: compare against the `${BATTERY_HEALTH_*}` special variables instead of hardcoded strings

## Complete JSON example

```json
{
  "GetBatteryHealth": [
    {
      "id": "1",
      "title": "Get Battery Health",
      "value_output": "$BATTERY_HEALTH"
    }
  ]
}
```