# Sleep

## Summary

- **Internal name**: `Sleep`
- **Category**: Time
- **Purpose**: Pause the workflow execution for a specified duration.
- **Task type**: Normal

## Compatibility

- **Minimum AndroMate version**: `{{ ANDROMATE_FIRST_VERSION }}`
- **Maximum AndroMate version**: `{{ ANDROMATE_CURRENT_VERSION }}`
- **Minimum Android version**: `{{ ANDROMATE_MIN_APP_SDK }}`
- **Maximum Android version tested**: `{{ ANDROID_CURRENT_APP_SDK }}`
- **Supported manufacturers**:
  - ✅ All manufacturers (tested on Samsung One UI 6.x / 7.x / 8.x and Google Pixel Android Stock)
- **Required permissions**:
  - None

## Detailed description

The **Sleep** task temporarily pauses the workflow execution.
It is used to:

- Add delays between two automated actions.
- Wait for a screen to stabilize before performing the next action (click, swipe...).
- Synchronize network or system actions (e.g., wait for SIM, Wi-Fi, or network state change).
- Create controlled pauses in benchmarking, QoS, or TV scenarios.

### Known limitations

- Very long durations may unnecessarily extend the total workflow execution time.
- Does not guarantee that the system state is stable when the pause ends; it is only a fixed delay.

## Input parameters

- Parameter: `Time_sleep` | Type: Long | Required: Yes | Possible values: >= 0 (milliseconds) | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `0`

## Output parameters

This task produces no output. It returns `VoidResult`.

## Exceptions

This task does not throw any exceptions.

## Execution flowchart

Diagram Nodes:
- ReadParam: 🔄 Read Time_sleep\nfrom JSON config
- DoSleep: ⏸️ deepSleep\nTime_sleep ms

Workflow Flow:
- 🔄 Read Time_sleep\nfrom JSON config → ⏸️ deepSleep\nTime_sleep ms
- ⏸️ deepSleep\nTime_sleep ms → Success

**How it works:**

1. **Read parameter**: `Time_sleep` is read from the JSON configuration (default `0`)
2. **Execute sleep**: The thread is paused for the specified duration using `ThreadHelper.deepSleep()`
3. **Result**: Returns `VoidResult` — no output, no exceptions

## Input parameter details

### 1. Input parameter: `Time_sleep`

Duration of the pause in milliseconds.

#### Example

```json
"Time_sleep": 5000
```

#### Details

- **Type**: Long
- **Default**: `0`
- Value `0` means no pause.
- Very long values extend total workflow execution time without benefit.
- Recommended values: 500–30000 ms depending on use case.

## Complete JSON example

```json
{
  "Sleep": [
    {
      "id": "-1",
      "title": "Sleep",
      "Time_sleep": 5000
    }
  ]
}
```