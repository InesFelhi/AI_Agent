# Wait SMS

## Summary

- **Internal name**: `WaitSms`
- **Category**: SMS
- **Purpose**: Block workflow execution and wait for an incoming SMS matching optional sender and body filters, then capture the message content into workflow variables.
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
  - `RECEIVE_SMS`

## Detailed description

The **Wait SMS** task blocks execution and listens for an incoming SMS on the device. It subscribes to the internal AndroMate SMS event bus and waits until a matching SMS is received or the timeout expires.

When a matching SMS arrives, the task captures:

- The **message body** of the received SMS
- The **sender's phone number** (MSISDN)
- The **timestamp** (in milliseconds) at which the SMS was received

**Matching rules:**

- If `expected_msisdn` is empty → accept SMS from **any sender**
- If `expected_msisdn` is set → the sender must match exactly
- If `expected_message` is empty → accept **any message body**
- If `expected_message` is set and `use_regex` is `false` → the body must match exactly
- If `expected_message` is set and `use_regex` is `true` → the body is tested against the value as a **Java regular expression**

## Input parameters

- Parameter: `expected_msisdn` | Type: String | Required: No | Possible values: E.164 phone number or `""` to accept any sender — supports `$variable` | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `""`
- Parameter: `expected_message` | Type: String | Required: No | Possible values: Any string or regex pattern — `""` to accept any message — supports `$variable` | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `""`
- Parameter: `use_regex` | Type: Boolean | Required: No | Possible values: `true` / `false` | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `false`
- Parameter: `wait_sms_timeout_s` | Type: Integer | Required: No | Possible values: Integer ≥ 0 (seconds) | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `10`

## Output parameters

- Field: `message_received_output` | Type: String | Trigger condition: Written when a matching SMS is received — contains the message body | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`
- Field: `msisdn_sender_output` | Type: String | Trigger condition: Written when a matching SMS is received — contains the sender's phone number | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`
- Field: `wait_time_output` | Type: Long | Trigger condition: Written when a matching SMS is received — contains the reception timestamp in milliseconds | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`

**Note:** Output variables are only written if the corresponding workflow variable already exists in the execution context (declared in the **Start** task).

## Exceptions

- Code: `WAIT-SMS-TASK-001` | Exception Name: Wait SMS Timeout | Description: No matching SMS was received within the `wait_sms_timeout_s` deadline.
- Code: `ERROR-000` | Exception Name: Other Error | Description: An unexpected runtime error occurred during execution.

## Execution flowchart

The following diagram illustrates the actual implementation based on the Android code:

Diagram Nodes:
- ResolveParams: 🔄 Resolve expected_msisdn\n+ expected_message
- Subscribe: 📡 Subscribe to\nSmsEventBus
- MsisdnOk: ✅ MSISDN accepted\nany sender
- BodyOk: ✅ Body accepted\nany content
- Capture: 💾 Capture body → message_received_output\nCapture sender → msisdn_sender_output\nCapture timestamp → wait_time_output
- Unsubscribe: 🔕 Unsubscribe from SmsEventBus
- E1: ❌ WAIT-SMS-TASK-001

Workflow Flow:
- 🔄 Resolve expected_msisdn\n+ expected_message → 📡 Subscribe to\nSmsEventBus
- 📡 Subscribe to\nSmsEventBus → WaitLoop
- ✅ MSISDN accepted\nany sender → CheckBody
- ✅ Body accepted\nany content → 💾 Capture body → message_received_output\nCapture sender → msisdn_sender_output\nCapture timestamp → wait_time_output
- 💾 Capture body → message_received_output\nCapture sender → msisdn_sender_output\nCapture timestamp → wait_time_output → 🔕 Unsubscribe from SmsEventBus
- 🔕 Unsubscribe from SmsEventBus → Success
- ❌ WAIT-SMS-TASK-001 → Error

**How it works:**

1. **Resolve parameters**: `expected_msisdn` and `expected_message` are resolved from the workflow context
2. **Subscribe**: registers a listener on the internal AndroMate SMS event bus
3. **Wait loop**: for each incoming SMS event within the timeout window:
  - **MSISDN check**: if `expected_msisdn` is set, compares against the sender — skips if no match
  - **Body check**: if `expected_message` is set, compares using exact match or regex — skips if no match
4. **Match found**: captures body, sender, and timestamp into output variables; unsubscribes from the bus
5. **Timeout**: if no matching SMS arrives within `wait_sms_timeout_s` seconds — throws `WAIT-SMS-TASK-001`

## Code examples

### Example 1 — Wait for any SMS (any sender, any content)

```json
{
  "WaitSms": [
    {
      "id": "1",
      "title": "Wait for any SMS",
      "wait_sms_timeout_s": 30,
      "message_received_output": "$received_body",
      "msisdn_sender_output": "$sender_number"
    }
  ]
}
```

### Example 2 — Wait for SMS from a specific sender

```json
{
  "WaitSms": [
    {
      "id": "2",
      "title": "Wait SMS from server",
      "expected_msisdn": "+33600000000",
      "wait_sms_timeout_s": 60,
      "message_received_output": "$sms_body",
      "msisdn_sender_output": "$sms_sender"
    }
  ]
}
```

### Example 3 — Wait for SMS matching a regex pattern

```json
{
  "WaitSms": [
    {
      "id": "3",
      "title": "Wait for OTP code",
      "expected_msisdn": "+33600000000",
      "expected_message": ".*code[:\\s]+\\d{6}.*",
      "use_regex": true,
      "wait_sms_timeout_s": 120,
      "message_received_output": "$otp_sms",
      "msisdn_sender_output": "$otp_sender",
      "wait_time_output": "$otp_received_at_ms"
    }
  ]
}
```

### Example 4 — Wait for exact message content

```json
{
  "WaitSms": [
    {
      "id": "4",
      "title": "Wait for ACK",
      "expected_message": "ACK",
      "use_regex": false,
      "wait_sms_timeout_s": 30,
      "message_received_output": "$ack_body"
    }
  ]
}
```

## Input parameter details

### 1. Input parameter: `expected_msisdn`

Phone number of the expected SMS sender in E.164 format. If empty, the task accepts SMS from **any sender**.

- **Default**: `""` (accept any sender)
- **Supports variables**: Yes

### 2. Input parameter: `expected_message`

Expected content of the SMS body. If empty, the task accepts **any message content**.

- When `use_regex = false`: the received body must match exactly (content comparison)
- When `use_regex = true`: the received body is tested against this value as a **Java regular expression**
- **Default**: `""` (accept any content)
- **Supports variables**: Yes

### 3. Input parameter: `use_regex`

Controls how `expected_message` is applied when not empty.

- Value: `false` | Matching mode: Exact content comparison
- Value: `true` | Matching mode: Java regex pattern matching (`String.matches()`)

- **Default**: `false`

### 4. Input parameter: `wait_sms_timeout_s`

Maximum time in seconds the task blocks waiting for a matching SMS. If no matching SMS arrives before the timeout, throws `WAIT-SMS-TASK-001`.

- **Default**: `10` seconds
- **Minimum recommended**: `5` seconds

## Output parameter details

### 1. Result variable: `message_received_output`

Stores the body of the received SMS in the specified workflow variable.

### 2. Result variable: `msisdn_sender_output`

Stores the sender's phone number (as reported by the Android telephony API) in the specified workflow variable.

### 3. Result variable: `wait_time_output`

Stores the timestamp (in **milliseconds since epoch**) at which the SMS was received, as reported by the `SmsEvent`. Useful for measuring SMS delivery latency.

## Complete JSON example

```json
{
  "WaitSms": [
    {
      "id": "1",
      "title": "Wait for OTP SMS",
      "expected_msisdn": "+33600000000",
      "expected_message": ".*code[:\\s]+\\d{6}.*",
      "use_regex": true,
      "wait_sms_timeout_s": 60,
      "message_received_output": "$sms_body",
      "msisdn_sender_output": "$sms_sender",
      "wait_time_output": "$sms_received_at"
    }
  ]
}
```