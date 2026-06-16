# Show Toast

## Summary

- **Internal name**: `ShowToast`
- **Category**: Notifications
- **Purpose**: Display a short, transient toast message on screen.
- **Task type**: Normal

## Compatibility

- **Minimum AndroMate version**: `{{ ANDROMATE_FIRST_VERSION }}`
- **Maximum AndroMate version**: `{{ ANDROMATE_CURRENT_VERSION }}`
- **Minimum Android**: `{{ ANDROMATE_MIN_APP_SDK }}`
- **Maximum Android tested**: `{{ ANDROID_CURRENT_APP_SDK }}`
- **Required permissions**: None

## Detailed description

The **Show Toast** task displays a short text toast. It uses `Toast.makeText` (a plain text toast), which is allowed from the background on all supported Android versions.

Because workflows run on a background worker thread, the toast is automatically dispatched to the **main thread** internally — otherwise Android would throw *"Can't toast on a thread that has not called Looper.prepare()"*.

## Input parameters

- Parameter: `message` | Type: String | Required: Yes | Possible values / Rules: Toast text (supports interpolation) | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `""`
- Parameter: `duration` | Type: Enum / String | Required: No | Possible values / Rules: `Short` (~2s) or `Long` (~3.5s) | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `Short`

## Output parameters

This task produces no output variable. It returns a `VoidResult`.

## Exceptions

This task does not throw exceptions.

## Execution flowchart

Diagram Nodes:
- Resolve: 🔧 Resolve message
- Length: ⏱️ Map duration\nShort / Long
- Main: 📲 Dispatch to main thread
- Toast: 🍞 Toast.makeText.show

Workflow Flow:
- 🔧 Resolve message → ⏱️ Map duration\nShort / Long
- ⏱️ Map duration\nShort / Long → 📲 Dispatch to main thread
- 📲 Dispatch to main thread → 🍞 Toast.makeText.show
- 🍞 Toast.makeText.show → Success

**How it works:**

1. **Resolve**: `message` is resolved against the AndroMate context
2. **Duration**: `duration` is mapped to `Toast.LENGTH_SHORT` / `LENGTH_LONG`
3. **Main thread**: the toast call is posted to the main thread
4. **Show**: the toast is displayed
5. **Result**: returns `VoidResult`

## Code examples

### Example 1 — Short toast

```json
{
  "ShowToast": [
    {
      "id": "1",
      "title": "Quick toast",
      "message": "Step done",
      "duration": "Short"
    }
  ]
}
```

### Example 2 — Long toast with a variable

```json
{
  "ShowToast": [
    {
      "id": "2",
      "title": "Result toast",
      "message": "Speed = $speed_kmh km/h",
      "duration": "Long"
    }
  ]
}
```

## Input parameter details

### `message` — Toast text

The text shown in the toast. Supports `$variable` and `${SPECIAL_VAR}` interpolation.

### `duration` — Display duration

- `Short` → ~2 seconds (`Toast.LENGTH_SHORT`)
- `Long` → ~3.5 seconds (`Toast.LENGTH_LONG`)

Any unrecognized value falls back to `Short`.

## Output parameter details

This task produces no output variable.

## Complete JSON example

```json
{
  "ShowToast": [
    {
      "id": "1",
      "title": "Show Toast",
      "message": "Hello from AndroMate",
      "duration": "Short"
    }
  ]
}
```