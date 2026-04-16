# Iperf3 Benchmark

## Summary

- **Internal name**: `Iperf3`
- **Category**: Communication
- **Purpose**: Run an iperf3 network throughput test against a remote iperf3 server and store the measured performance metrics as a JSON string.
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
  - `INTERNET`
  - `ACCESS_NETWORK_STATE`

## Detailed description

The **Iperf3 Benchmark** task executes the iperf3 client on the Android device via JNI (`Iperf3Runner.run()`) to measure network throughput between the device and a remote iperf3 server. It supports both TCP and UDP protocols and both upload and download directions.

The task builds an `Iperf3Options` object from the provided parameters and invokes the iperf3 JNI layer with `json=true` and `oneOff=true`. The raw JSON output from iperf3 is parsed and stored as a single string in `value_output`. There are no pre-defined exception codes in `AndromateExceptionTypes` for this task — connection and execution errors surface as runtime exceptions from the JNI layer.

**Note**: `packetLength` is only applied if greater than 0. `bandwidth` is only applied if greater than 0 (appended as `"<value>M"` to target Mbit/s).

## Input parameters

- Parameter: `serverHost` | Type: String | Required: Yes | Possible values: IP address or hostname of the iperf3 server — supports `$variable` | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `""`
- Parameter: `serverPort` | Type: Integer | Required: No | Possible values: Valid port number (1–65535) | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `5201`
- Parameter: `packetLength` | Type: Integer | Required: No | Possible values: Buffer/packet length in bytes; `0` = use iperf3 default | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `0`
- Parameter: `bandwidth` | Type: Integer | Required: No | Possible values: Target bandwidth in Mbit/s for UDP; `0` = use iperf3 default | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `0`
- Parameter: `protocol` | Type: String | Required: No | Possible values: `"TCP"` or `"UDP"` | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `"TCP"`
- Parameter: `direction` | Type: String | Required: No | Possible values: `"UPLOAD"` (client→server) or `"DOWNLOAD"` (server→client, reverse `-R`) | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `"UPLOAD"`

## Output parameters

- Field: `value_output` | Type: String | Trigger condition: Always on success — iperf3 result as JSON string | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`

The `value_output` JSON string contains the following fields:

- JSON field: `exitCode` | Present: Always | Description: iperf3 process exit code
- JSON field: `sentBps` | Present: Always | Description: Sent throughput in bits/second
- JSON field: `receivedBps` | Present: Always | Description: Received throughput in bits/second
- JSON field: `seconds` | Present: Always | Description: Test duration in seconds
- JSON field: `startTimeMs` | Present: Always | Description: Test start timestamp in milliseconds
- JSON field: `localHost` | Present: Always | Description: Local endpoint host
- JSON field: `localPort` | Present: Always | Description: Local endpoint port
- JSON field: `remoteHost` | Present: Always | Description: Remote server host
- JSON field: `remotePort` | Present: Always | Description: Remote server port
- JSON field: `jitterMs` | Present: UDP only | Description: Measured jitter in milliseconds
- JSON field: `lostPackets` | Present: UDP only | Description: Number of lost packets
- JSON field: `packets` | Present: UDP only | Description: Total number of packets sent
- JSON field: `lostPercent` | Present: UDP only | Description: Packet loss percentage

## Exceptions

There are no exception codes defined in `AndromateExceptionTypes` for `Iperf3`. Connection failures, host unreachable errors, and other execution problems surface as runtime exceptions from the JNI layer.

## Execution flowchart

Diagram Nodes:
- ResolveParams: 🔄 Resolve serverHost + parameters
- BuildOptions: 🔧 Build Iperf3Options\nprotocol, direction, serverHost, serverPort\npacketLength if >0\nbandwidth+M if >0\njson=true, oneOff=true
- RunJNI: ⚙️ Iperf3Runner.run via JNI
- ERuntime: ❌ Runtime exception\nfrom JNI layer
- ParseJSON: 📊 Parse iperf3 JSON output
- WriteOutput: 💾 Set value_output\niperf3 result JSON string

Workflow Flow:
- 🔄 Resolve serverHost + parameters → 🔧 Build Iperf3Options\nprotocol, direction, serverHost, serverPort\npacketLength if >0\nbandwidth+M if >0\njson=true, oneOff=true
- 🔧 Build Iperf3Options\nprotocol, direction, serverHost, serverPort\npacketLength if >0\nbandwidth+M if >0\njson=true, oneOff=true → ⚙️ Iperf3Runner.run via JNI
- 📊 Parse iperf3 JSON output → 💾 Set value_output\niperf3 result JSON string
- 💾 Set value_output\niperf3 result JSON string → Success
- ❌ Runtime exception\nfrom JNI layer → Error

**How it works:**

1. **Resolve parameters**: `serverHost` and all other parameters are resolved from the workflow context
2. **Build Iperf3Options**: constructs the options object with protocol, direction, serverHost, serverPort; applies packetLength only if > 0; applies bandwidth as `"<value>M"` only if > 0; always sets `json=true` and `oneOff=true`
3. **Run via JNI**: calls `Iperf3Runner.run()` through the JNI layer — connection/execution errors surface as runtime exceptions
4. **Parse output**: parses the iperf3 JSON result
5. **Set output**: stores the iperf3 result JSON string in `value_output`
6. **Result**: returns `StrTaskResult`

## Code examples

### Example 1 — TCP upload test (default)

```json
{
  "Iperf3": [
    {
      "id": "1",
      "title": "TCP upload test",
      "serverHost": "192.168.1.100",
      "protocol": "TCP",
      "direction": "UPLOAD",
      "value_output": "$iperf3_result"
    }
  ]
}
```

### Example 2 — TCP download test (reverse mode)

```json
{
  "Iperf3": [
    {
      "id": "2",
      "title": "TCP download test",
      "serverHost": "192.168.1.100",
      "serverPort": 5201,
      "protocol": "TCP",
      "direction": "DOWNLOAD",
      "value_output": "$iperf3_result"
    }
  ]
}
```

### Example 3 — UDP test with bandwidth target

```json
{
  "Iperf3": [
    {
      "id": "3",
      "title": "UDP quality test at 10 Mbit/s",
      "serverHost": "$iperf3_server",
      "protocol": "UDP",
      "direction": "UPLOAD",
      "bandwidth": 10,
      "value_output": "$udp_result"
    }
  ]
}
```

UDP test — `value_output` JSON will include `jitterMs`, `lostPackets`, `packets`, and `lostPercent`.

### Example 4 — Custom port and packet length

```json
{
  "Iperf3": [
    {
      "id": "4",
      "title": "Custom port iperf3",
      "serverHost": "10.0.0.5",
      "serverPort": 5210,
      "packetLength": 1400,
      "protocol": "TCP",
      "direction": "UPLOAD",
      "value_output": "$raw_json"
    }
  ]
}
```

## Input parameter details

### 1. `serverHost` — Server address

The IP address or hostname of the remote iperf3 server. The server must be running in server mode (`iperf3 -s`). Supports `$workflow_variable` references.

- **Default**: `""`
- **Supports variables**: Yes

### 2. `serverPort` — Server port

The port on which the remote iperf3 server is listening.

- **Default**: `5201` (iperf3 default port)

### 3. `packetLength` — Buffer/packet length

The buffer or packet length in bytes passed to iperf3. A value of `0` means iperf3 uses its own default. Applied only when greater than 0.

- **Default**: `0` (use iperf3 default)

### 4. `bandwidth` — Target bandwidth (UDP)

Target bandwidth in Mbit/s for UDP tests. A value of `0` means iperf3 uses its own default. Applied only when greater than 0 — passed to iperf3 as `"<value>M"`.

- **Default**: `0` (use iperf3 default)
- **Applies to**: UDP protocol primarily

### 5. `protocol` — Transport protocol

Selects the transport layer protocol for the test.

- Value: `"TCP"` | Protocol: TCP | Notes: Measures throughput with congestion control
- Value: `"UDP"` | Protocol: UDP | Notes: Measures throughput, jitter, packet loss

- **Default**: `"TCP"`

### 6. `direction` — Traffic direction

Controls which direction the test traffic flows.

- Value: `"UPLOAD"` | Direction: Upload — device sends to server | iperf3 flag: *(default, no extra flag)*
- Value: `"DOWNLOAD"` | Direction: Download — server sends to device | iperf3 flag: `-R` (reverse mode)

- **Default**: `"UPLOAD"`

## Output parameter details

### `value_output` — iperf3 result JSON string

Stores the complete iperf3 result as a JSON string (from `StrTaskResult`). The JSON contains throughput fields for both TCP and UDP, and additionally `jitterMs`, `lostPackets`, `packets`, and `lostPercent` for UDP tests.

Example of the JSON content for a UDP test:

```json
{
  "exitCode": 0,
  "sentBps": 9876543.0,
  "receivedBps": 9654321.0,
  "seconds": 10.0,
  "startTimeMs": 1712000000000,
  "localHost": "192.168.1.10",
  "localPort": 54321,
  "remoteHost": "192.168.1.100",
  "remotePort": 5201,
  "jitterMs": 0.23,
  "lostPackets": 2,
  "packets": 1000,
  "lostPercent": 0.2
}
```

## Complete JSON example

```json
{
  "Iperf3": [
    {
      "id": "1",
      "title": "TCP upload benchmark",
      "serverHost": "192.168.1.100",
      "serverPort": 5201,
      "protocol": "TCP",
      "direction": "UPLOAD",
      "packetLength": 0,
      "bandwidth": 0,
      "value_output": "$iperf3_result_json"
    }
  ]
}
```