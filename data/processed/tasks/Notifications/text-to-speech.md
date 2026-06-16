# Text To Speech

## Summary

- **Internal name**: `TextToSpeech`
- **Category**: Notifications
- **Purpose**: Read a text out loud using the device text-to-speech engine. The task waits until playback ends.
- **Task type**: Normal

## Compatibility

- **Minimum AndroMate version**: `{{ ANDROMATE_FIRST_VERSION }}`
- **Maximum AndroMate version**: `{{ ANDROMATE_CURRENT_VERSION }}`
- **Minimum Android**: `{{ ANDROMATE_MIN_APP_SDK }}`
- **Maximum Android tested**: `{{ ANDROID_CURRENT_APP_SDK }}`
- **Required permissions**: None

## Detailed description

The **Text To Speech** task speaks a text aloud through the Android `TextToSpeech` engine. It works from the background (foreground service) — it is audio output, not UI, and needs no special runtime permission.

The TTS engine has an asynchronous lifecycle (init → speak → done). The task handles this internally and **blocks until playback finishes** (or the timeout expires), then releases the engine. Waiting is mandatory: releasing the engine too early would cut off the speech.

If the engine fails to initialize, the chosen language data is missing, or the timeout expires, the task throws `TTS-TASK-001`.

## Input parameters

- Parameter: `tts_text` | Type: String | Required: Yes | Possible values / Rules: Text to read (supports interpolation) | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `""`
- Parameter: `language` | Type: Enum / String | Required: No | Possible values / Rules: BCP-47 tag (`en`, `fr`, `ar`, …); empty → device default | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `""`
- Parameter: `timeout_s` | Type: Integer | Required: No | Possible values / Rules: Safety timeout for init + playback (seconds) | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `30`

## Output parameters

This task produces no output variable. It returns a `VoidResult` on success.

## Exceptions

- Code: `TTS-TASK-001` | Trigger condition: TTS engine init failed, language unavailable, or timeout expired

## Execution flowchart

Diagram Nodes:
- Resolve: 🔧 Resolve text & language
- Init: ⚙️ Init TTS engine\nwait for onInit
- Lang: 🌐 Set language\nfallback to default
- Speak: 🗣️ speak QUEUE_FLUSH
- Wait: ⏳ Wait for onDone / timeout
- Shutdown: 🧹 shutdown engine

Workflow Flow:
- 🔧 Resolve text & language → ⚙️ Init TTS engine\nwait for onInit
- ⚙️ Init TTS engine\nwait for onInit → Ok
- 🌐 Set language\nfallback to default → 🗣️ speak QUEUE_FLUSH
- 🗣️ speak QUEUE_FLUSH → ⏳ Wait for onDone / timeout
- ⏳ Wait for onDone / timeout → 🧹 shutdown engine
- 🧹 shutdown engine → Success

**How it works:**

1. **Resolve**: `tts_text` and `language` are resolved against the AndroMate context
2. **Init**: the TTS engine is initialized; the task waits for the `onInit` callback (up to `timeout_s`)
3. **Language**: the requested language is set; if unsupported, it falls back to the device default
4. **Speak**: the text is spoken with `QUEUE_FLUSH`
5. **Wait**: the task blocks until the `onDone` callback fires (or the timeout)
6. **Shutdown**: the engine is released
7. **Result**: returns `VoidResult`, or throws `TTS-TASK-001` on failure

## Code examples

### Example 1 — Speak a message in English

```json
{
  "TextToSpeech": [
    {
      "id": "1",
      "title": "Speak",
      "tts_text": "Test completed successfully",
      "language": "en",
      "timeout_s": 30
    }
  ]
}
```

### Example 2 — Speak a variable in the device language

```json
{
  "TextToSpeech": [
    {
      "id": "2",
      "title": "Announce result",
      "tts_text": "Speed is $speed_kmh kilometers per hour",
      "language": ""
    }
  ]
}
```

## Input parameter details

### `tts_text` — Text to speak

The text read aloud. Supports `$variable` and `${SPECIAL_VAR}` interpolation.

### `language` — Language

A BCP-47 language tag selecting the voice language:

- Value: `""` | Language: Device default
- Value: `en` | Language: English
- Value: `fr` | Language: French
- Value: `ar` | Language: Arabic
- Value: `es` | Language: Spanish
- Value: `de` | Language: German
- Value: `it` | Language: Italian

If the chosen language is not available on the device, the engine falls back to the device default.

### `timeout_s` — Safety timeout

Maximum time (in seconds) to wait for both engine initialization and playback. Prevents the workflow from blocking forever if the engine hangs. Default `30`.

## Output parameter details

This task produces no output variable.

## Complete JSON example

```json
{
  "TextToSpeech": [
    {
      "id": "1",
      "title": "Text To Speech",
      "tts_text": "Workflow finished",
      "language": "en",
      "timeout_s": 30
    }
  ]
}
```