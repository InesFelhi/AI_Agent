# Send SMS

## Summary

- **Internal name**: `SendSMS`
- **Category**: SMS
- **Purpose**: Send a plain-text SMS message to a phone number from the Android device.
- **Task type**: Normal

## Compatibility

- **Minimum AndroMate version**: `{{ ANDROMATE_FIRST_VERSION }}`
- **Maximum AndroMate version**: `{{ ANDROMATE_CURRENT_VERSION }}`
- **Minimum Android**: `{{ ANDROMATE_MIN_APP_SDK }}`
- **Maximum Android tested**: `{{ ANDROID_CURRENT_APP_SDK }}`
- **Supported manufacturers**:
  - ✅ Samsung (One UI 6.x / 7.x / 8.x)
  - ✅ Google Pixel (Android Stock)
  - ⚠️ Other manufacturers — **not tested**
- **Required permissions**:
  - `SEND_SMS`

## Detailed description

The **Send SMS** task sends a plain-text SMS message to a destination phone number using the Android `SmsManager` API. The message is sent from the device's default SIM card.

Before sending, the task validates:

- The destination number (`msisdn`) must follow the **E.164 international format** (e.g. `+33612345678`). Numbers without a `+` country code or in local format are rejected.
- The message body (`message_body`) must not be blank.
- The message body must not exceed **100 characters**.

## Input parameters

- Parameter: `msisdn` | Type: String | Required: Yes | Possible values: E.164 format: `+` followed by 2–15 digits (e.g. `+33612345678`) — supports `$variable` | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `""`
- Parameter: `message_body` | Type: String | Required: Yes | Possible values: Any string ≤ 100 characters — supports `$variable` references | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `""`

### E.164 format

The `msisdn` field must strictly match the E.164 international format:

- Starts with `+` followed by the country code
- Followed by the subscriber number
- Total length: 2 to 15 digits after `+`

**Valid examples:** `+33612345678`, `+12125551234`, `+447911123456`

**Invalid examples:** `0612345678` (no country code), `33612345678` (missing `+`), `+1` (too short)

## Output parameters

This task produces **no output variables**. It returns `VoidResult`.

- Field: — | Type: VoidResult | Trigger condition: Always | Default: —

## Exceptions

- Code: `SMS-TASK-001` | Exception Name: Invalid MSISDN | Description: The `msisdn` value does not match the E.164 format (`+` followed by 2–15 digits).
- Code: `SMS-TASK-002` | Exception Name: Empty Message Body | Description: The `message_body` is blank or empty.
- Code: `SMS-TASK-003` | Exception Name: Message Body Too Long | Description: The `message_body` exceeds the 100-character limit.
- Code: `ERROR-000` | Exception Name: Other Error | Description: An unexpected runtime error occurred during execution.

## Execution flowchart

The following diagram illustrates the actual implementation based on the Android code:

Diagram Nodes:
- ResolveParams: 🔄 Resolve msisdn + message_body\nfrom workflow context
- E1: ❌ SMS-TASK-001\nInvalid MSISDN
- E2: ❌ SMS-TASK-002\nEmpty message body
- E3: ❌ SMS-TASK-003\nMessage too long
- Send: 📤 SmsManager.sendTextMessage\nmsisdn, message_body

Workflow Flow:
- 🔄 Resolve msisdn + message_body\nfrom workflow context → ValidateMsisdn
- 📤 SmsManager.sendTextMessage\nmsisdn, message_body → Success
- ❌ SMS-TASK-001\nInvalid MSISDN → Error
- ❌ SMS-TASK-002\nEmpty message body → Error
- ❌ SMS-TASK-003\nMessage too long → Error

**How it works:**

1. **Resolve parameters**: `msisdn` and `message_body` are resolved from the workflow context
2. **Validate MSISDN**: checks E.164 format — throws `SMS-TASK-001` if invalid
3. **Validate body**: checks the message is not blank — throws `SMS-TASK-002` if empty
4. **Validate length**: checks message does not exceed 100 characters — throws `SMS-TASK-003` if too long
5. **Send**: delegates to `SmsManager.sendTextMessage()` via the Android telephony API
6. **Result**: returns `VoidResult` on success

## Code examples

### Example 1 — Send a static message

```json
{
  "SendSMS": [
    {
      "id": "1",
      "title": "Send test SMS",
      "msisdn": "+33612345678",
      "message_body": "AndroMate test message"
    }
  ]
}
```

### Example 2 — Send using workflow variables

```json
{
  "SendSMS": [
    {
      "id": "2",
      "title": "Report ping result",
      "msisdn": "$target_number",
      "message_body": "Ping result: $ping_output"
    }
  ]
}
```

## Input parameter details

### 1. Input parameter: `msisdn`

The phone number to send the SMS to. Must strictly follow the **E.164 international format**:

- Starts with `+`
- Followed by the country code (1–3 digits)
- Followed by the subscriber number
- Total: 2–15 digits after `+`

Supports `$workflow_variable` references.

- Valid: `+33612345678` | Invalid: `0612345678` (no country code)
- Valid: `+12125551234` | Invalid: `33612345678` (missing `+`)
- Valid: `+447911123456` | Invalid: `+1` (too short)

- **Default**: `""` — triggers `SMS-TASK-001` if not valid E.164

### 2. Input parameter: `message_body`

The content of the SMS to send. Supports `$workflow_variable` references — resolved at runtime.

- **Maximum length**: 100 characters — triggers `SMS-TASK-003` if exceeded
- **Cannot be blank** — triggers `SMS-TASK-002` if empty
- **Supports variables**: Yes

## Complete JSON example

```json
{
  "SendSMS": [
    {
      "id": "1",
      "title": "Send test SMS",
      "msisdn": "+33612345678",
      "message_body": "AndroMate test message"
    }
  ]
}
```