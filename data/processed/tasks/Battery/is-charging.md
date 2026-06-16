# Is Charging

## Summary

- **Internal name**: `IsCharging`
- **Category**: Battery
- **Purpose**: Check whether the device is currently charging. Branches the workflow based on charging state — `true` if any charger is connected, `false` otherwise.
- **Task type**: Condition

## Compatibility

- **Minimum AndroMate version**: `{{ ANDROMATE_FIRST_VERSION }}`
- **Maximum AndroMate version**: `{{ ANDROMATE_CURRENT_VERSION }}`
- **Minimum Android**: `{{ ANDROMATE_MIN_APP_SDK }}`
- **Maximum Android tested**: `{{ ANDROID_CURRENT_APP_SDK }}`
- **Required permissions**: None

## Detailed description

The **Is Charging** task reads the battery charging status from the Android battery broadcast (`ACTION_BATTERY_CHANGED`) and evaluates whether the device is actively charging. It acts as a condition node in the workflow: the workflow branches to the `true` path if charging, and to the `false` path otherwise.

A device is considered charging if `EXTRA_STATUS` equals `BATTERY_STATUS_CHARGING` or `BATTERY_STATUS_FULL`.

No special permissions are required — `ACTION_BATTERY_CHANGED` is a protected system broadcast available to all apps.

## Input parameters

This task has no configurable input parameters.

## Output parameters

This is a **Condition** task — it does not store a value. Instead, it directs workflow execution:

- Condition: Device is charging (status = Charging or Full) | Next step: `true` branch
- Condition: Device is not charging | Next step: `false` branch

## Exceptions

This task does not throw exceptions.

## Execution flowchart

Diagram Nodes:
- Register: 📡 Register ACTION_BATTERY_CHANGED\none-shot receiver
- ReadStatus: 🔋 Read EXTRA_STATUS

Workflow Flow:
- 📡 Register ACTION_BATTERY_CHANGED\none-shot receiver → 🔋 Read EXTRA_STATUS
- 🔋 Read EXTRA_STATUS → CheckCharging

**How it works:**

1. **Register battery receiver**: registers a one-shot receiver for `ACTION_BATTERY_CHANGED`
2. **Read status**: extracts `EXTRA_STATUS` from the battery intent
3. **Evaluate condition**: if status is `BATTERY_STATUS_CHARGING` or `BATTERY_STATUS_FULL`, takes the `true` branch; otherwise takes the `false` branch

## Code examples

### Example 1 — Branch workflow based on charging state

```json
{
  "IsCharging": [
    {
      "id": "1",
      "title": "Is device charging?"
    }
  ]
}
```

## Input parameter details

This task has no configurable input parameters.

## Output parameter details

This is a **Condition** task — it stores no output variable. The result drives the workflow branching:

### `true` branch

Taken when `EXTRA_STATUS` equals `BATTERY_STATUS_CHARGING` or `BATTERY_STATUS_FULL`.

### `false` branch

Taken when the device is not charging.

## Complete JSON example

```json
{
  "IsCharging": [
    {
      "id": "1",
      "title": "Is Charging"
    }
  ]
}
```