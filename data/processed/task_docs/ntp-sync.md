# NTP Sync Stage

## Summary

- **Internal name**: 'SyncNtp'
- **Category**: Time
- **Purpose**: Synchronize device time with an NTP server to get accurate network time offset and round-trip time (RTT).

## Compatibility

- **Minimum AndroMate version**: '{{ ANDROMATE_FIRST_VERSION }}'
- **Maximum AndroMate version**: '{{ ANDROMATE_CURRENT_VERSION }}'
- **Minimum Android version**: '{{ ANDROMATE_MIN_APP_SDK }}'
- **Maximum Android version tested**: '{{ ANDROID_CURRENT_APP_SDK }}'
  - ✅ All manufacturers (tested on Samsung One UI 6.x / 7.x / 8.x and Google Pixel Android Stock)
- **Supported manufacturers**:
  - 'INTERNET'
- **Required permissions**:

## Detailed description

The **NTP Sync** task synchronizes the device with an NTP (Network Time Protocol) server to retrieve accurate time information.

It is used to:

- Get accurate network time offset
- Measure network round-trip time (RTT)
- Synchronize device time with authoritative time servers
- Validate system clock accuracy

### Implementation details

- **RFC 5905 compliant**: Full SNTP (Simple Network Time Protocol) implementation
- **Monotonic safe**: Uses 'SystemClock.elapsedRealtime()' for accurate timing
- **RTT filtering**: Rejects responses with invalid RTT (> 1000 ms)
- **Timestamp validation**: Validates originate timestamp to ensure response authenticity
- **Timeout handling**: Configurable timeout for the NTP request

## Input parameters

- Parameter: `ntp_server` | Type: String | Required: No | Possible values: Valid NTP server hostname | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: time.google.com

## Output parameters

- Field: `ntp_offset_output` | Type: Long | Trigger condition: When NTP sync succeeds | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`
- Field: `ntp_rtt_output` | Type: Long | Trigger condition: When NTP sync succeeds | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`

## Exceptions

- Code: NTP_CLIENT_ERROR | Exception Name: NTP Client Error | Description: Failed to communicate with NTP server (IOException) or received invalid response.

# Flowchart

flowchart TD
    Start([Start NTP Sync]) --> ResolveParams[🔄 Resolve Parameters<br/>NTP server]
    
    ResolveParams --> SendRequest[📡 Send NTP Request<br/>Timeout: 5000ms]
    
    SendRequest -->|Success| Validate[✓ Validate Response<br/>RFC 5905 checks]
    SendRequest -->|Timeout/Error| E1[❌ NTP_CLIENT_ERROR]
    
    Validate -->|Valid| CalcMetrics[🔢 Calculate Offset & RTT<br/>Validate RTT &lt;= 1000ms]
    Validate -->|Invalid| E1
    
    CalcMetrics -->|RTT Invalid| E1
    CalcMetrics -->|Success| StoreResult[💾 Store Result<br/>NtpTaskResult]
    
    StoreResult --> LogReport[📋 Log Report<br/>Offset + RTT]
    
    LogReport --> Success([✅ Success])
    
    E1 --> Error([❌ Exception])
    
    style Start fill:#e3f2fd
    style Success fill:#c8e6c9
    style Error fill:#ffcdd2
    style SendRequest fill:#f3e5f5
    style Validate fill:#fff9c4
    style CalcMetrics fill:#fff9c4
    style StoreResult fill:#c8e6c9

**How it works:**

1. **Resolve parameters**: Resolves NTP server hostname
2. **Send NTP request**: Sends SNTP request with 5-second timeout
3. **Validate response**: Checks RFC 5905 compliance (LI, version, mode, stratum, timestamps)
4. **Calculate metrics**: Computes time offset and RTT, validates RTT <= 1000ms
5. **Store result**: Saves offset and RTT values
6. **Log report**: Records execution details
7. **Result**: Returns NtpTaskResult or exception

# Parameter details

## 1. Input parameter: `ntp_server`

NTP server hostname to synchronize with.

### Default value

'time.google.com' (Google Public NTP Server)

### Possible values

- 'time.google.com' (Google)
- 'pool.ntp.org' (NTP Pool Project)
- 'time.nist.gov' (NIST)
- Custom NTP server hostname

### Example

"ntp_server": "pool.ntp.org"

# Output details

## 1. Result variable: `ntp_offset_output`

Time offset between device and NTP server in milliseconds.

### Example

"ntp_offset_output": "$NTP_OFFSET"

### Notes

- **Positive value**: Device time is ahead of NTP server
- **Negative value**: Device time is behind NTP server
- Value represents milliseconds

## 2. Result variable: `ntp_rtt_output`

Round-trip time (RTT) for NTP request in milliseconds.

### Example

"ntp_rtt_output": "$NTP_RTT"

### Notes

- Lower values indicate faster network connection
- Maximum accepted value: 1000 ms
- Requests with RTT > 1000 ms are rejected

# Complete JSON example

{
  "SyncNtp": [
    {
      "id": "-1",
      "title": "NTP Sync",
      "ntp_server": "time.google.com",
      "ntp_offset_output": "$OFFSET_MS",
      "ntp_rtt_output": "$RTT_MS"
    }
  ]
}

# NTP Schema and Formulas

## Timestamps Diagram

t'₂         t'₃
          ↑           ↑
    ------|-----------|------  SERVER
          |           |
         δ₁          δ₂
         ↙            ↘
    ----•----•-----------•---- CLIENT
       t₁   δ₁          δ₂   t₄

**Schema Explanation:**

- **t₁** : Client request send time
- **t'₂** : Server request receive time
- **t'₃** : Server response send time
- **t₄** : Client response receive time
- **δ₁** : Network delay (client → server)
- **δ₂** : Network delay (server → client)

## Timestamps

- Timestamp: **t₁** | Description: Client request send time | Source: Client (wall-clock)
- Timestamp: **t'₂** | Description: Server request receive time | Source: Server (NTP)
- Timestamp: **t'₃** | Description: Server response send time | Source: Server (NTP)
- Timestamp: **t₄** | Description: Client response receive time | Source: Client (wall-clock)
- Timestamp: **δ₁** | Description: Network delay (client → server) | Source: Network delay
- Timestamp: **δ₂** | Description: Network delay (server → client) | Source: Network delay

## Calculation Formulas

### Round-Trip Time (RTT)

RTT = (t₄ - t₁) - (t'₃ - t'₂)
    = δ₁ + δ₂

**Explanation**:

- '(t₄ - t₁)' : Total elapsed time on client side
- '(t'₃ - t'₂)' : Server processing time
- **Result** : Pure network latency (sum of both delays)

### Time Offset

Offset = ((t'₂ - t₁) + (t'₃ - t₄)) / 2
       = (δ₁ - δ₂) / 2

**Explanation**:

- '(t'₂ - t₁)' : Offset at reception
- '(t'₃ - t₄)' : Offset at transmission
- **Division by 2** : Average of both measurements
- **Result** : Difference between server time and client time

### Concrete Example

Network delays: δ₁ = 50 ms, δ₂ = 50 ms
Time offset: -100 ms

t₁ = 1000 ms (client sends)
t'₂ = 1050 ms (server receives) = t₁ + δ₁
t'₃ = 1100 ms (server sends) = t'₂ + 50 ms (processing)
t₄ = 1150 ms (client receives) = t'₃ + δ₂

RTT = (1150 - 1000) - (1100 - 1050)
    = 150 - 50
    = 100 ms ✓ (δ₁ + δ₂ = 50 + 50 = 100)

Offset = ((1050 - 1000) + (1100 - 1150)) / 2
       = (50 + (-50)) / 2
       = 0 / 2
       = 0 ms

## Validations Performed

- Check: **Valid RTT** | Condition: 0 < RTT ≤ 1000 ms | Description: Rejects responses with invalid latency
- Check: **Originate timestamp** | Condition: |originate - t1| ≤ 5 ms | Description: Validates that response is authentic
- Check: **Transmit timestamp** | Condition: t3 ≠ 0 | Description: Verifies server sent a response
- Check: **Server mode** | Condition: mode = 4 or 5 | Description: Accepts server or broadcast responses
- Check: **Stratum** | Condition: 0 < stratum ≤ 15 | Description: Validates quality of time source
- Check: **Leap Indicator** | Condition: LI ≠ 3 | Description: Rejects if server not synchronized
- Check: **NTP Version** | Condition: 3 ≤ version ≤ 4 | Description: Accepts NTP v3 and v4

- **SNTP Client**: RFC 5905 compliant implementation
- **Timeout**: Fixed 5-second timeout for NTP request
- **RTT Filter**: Responses with RTT > 1000 ms are rejected for mobile safety
- **Timestamp Validation**: Originate timestamp must match within 5 ms tolerance
- **Monotonic Timing**: Uses 'SystemClock.elapsedRealtime()' for accurate timing calculations
- **No Permissions Cache**: Internet permission required for NTP communication