# Vibrate

## Summary

- **Internal name**: `Vibrate`
- **Category**: Notifications
- **Purpose**: Vibrate the device for a given duration. The task waits until the vibration finishes before continuing.
- **Task type**: Normal

## Compatibility

- **Minimum AndroMate version**: `{{ ANDROMATE_FIRST_VERSION }}`
- **Maximum AndroMate version**: `{{ ANDROMATE_CURRENT_VERSION }}`
- **Minimum Android**: `{{ ANDROMATE_MIN_APP_SDK }}`
- **Maximum Android tested**: `{{ ANDROID_CURRENT_APP_SDK }}`
- **Required permissions**: `VIBRATE`

## Detailed description

The **Vibrate** task triggers a one-shot vibration using the device `VibratorManager`. It works from the background (foreground service) without any extra restriction.

Two safety behaviors are built in:

- **Capped duration**: the duration is clamped to a maximum of **10 000 ms (10 s)** — a request of one hour will only vibrate for 10 seconds.
- **Waits for the end**: the task blocks for the (capped) duration so that workflow timing stays deterministic and the vibration is guaranteed to complete before the next task runs.

## Input parameters

- Parameter: `duration_ms` | Type: Integer | Required: No | Possible values / Rules: Vibration duration in ms — capped at `10000` | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `500`

## Output parameters

This task produces no output variable. It returns a `VoidResult`.

## Exceptions

This task does not throw exceptions.

## Execution flowchart

Diagram Nodes:
- Cap: ⛔ Clamp duration to max 10000 ms
- Vibrate: 📳 VibratorManager.vibrate
- Wait: ⏳ Wait for the duration

Workflow Flow:
- ⛔ Clamp duration to max 10000 ms → 📳 VibratorManager.vibrate
- 📳 VibratorManager.vibrate → ⏳ Wait for the duration
- ⏳ Wait for the duration → Success

**How it works:**

1. **Clamp**: `duration_ms` is capped to `10000` ms
2. **Vibrate**: a one-shot vibration is triggered with the default amplitude
3. **Wait**: the task blocks for the effective (capped) duration
4. **Result**: returns `VoidResult`

## Code examples

### Example 1 — Short buzz

```json
{
  "Vibrate": [
    {
      "id": "1",
      "title": "Buzz",
      "duration_ms": 500
    }
  ]
}
```

### Example 2 — Longer vibration (still capped at 10s)

```json
{
  "Vibrate": [
    {
      "id": "2",
      "title": "Long buzz",
      "duration_ms": 3000
    }
  ]
}
```

## Input parameter details

### `duration_ms` — Vibration duration

Duration of the vibration in milliseconds.

- Default: `500`
- **Maximum: `10000` ms (10 s)** — any larger value is silently clamped
- The task waits for this (capped) duration before moving on

## Output parameter details

This task produces no output variable.

## Complete JSON example

```json
{
  "Vibrate": [
    {
      "id": "1",
      "title": "Vibrate",
      "duration_ms": 800
    }
  ]
}
```