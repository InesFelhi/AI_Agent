# HTTP Request

## Summary

- **Internal name**: `HttpRequest`
- **Category**: Communication
- **Purpose**: Perform an HTTP GET or POST request with configurable parameters, headers, body, and timeouts. Returns the HTTP response code and body.
- **Task type**: Normal

## Compatibility

- **Minimum AndroMate version**: `{{ ANDROMATE_FIRST_VERSION }}`
- **Maximum AndroMate version**: `{{ ANDROMATE_CURRENT_VERSION }}`
- **Minimum Android**: `{{ ANDROMATE_MIN_APP_SDK }}`
- **Maximum Android tested**: `{{ ANDROID_CURRENT_APP_SDK }}`
- **Required permissions**:
  - `INTERNET`
  - `ACCESS_NETWORK_STATE`

## Detailed description

The **HTTP Request** task performs an HTTP GET or POST request to the specified `url`. Parameters, headers, and the request body are configured individually. Connection and read timeouts are controlled separately. Debug logging can be enabled via `httpDebug`.

The task resolves all dynamic variables in `url`, `headers`, `parameters`, and `body` before executing the request. On success, the HTTP response code and response body are stored in the output variables from `HttpRequestResult`. An `IOException` during execution raises `HTTP-ERROR-001`.

## Input parameters

- Parameter: `url` | Type: String | Required: Yes | Possible values: Valid HTTP/HTTPS URL — supports `$variable` | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `""`
- Parameter: `method` | Type: String | Required: No | Possible values: `"GET"`, `"POST"` | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `"GET"`
- Parameter: `connectionTimeout` | Type: Long | Required: No | Possible values: Connection timeout in milliseconds | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `5000`
- Parameter: `readTimeout` | Type: Long | Required: No | Possible values: Read timeout in milliseconds | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `5000`
- Parameter: `httpDebug` | Type: Boolean | Required: No | Possible values: `true` / `false` — enable debug logging | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `false`
- Parameter: `parameters` | Type: JSONArray | Required: No | Possible values: List of `{"param_name": "...", "value": "..."}` objects | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `[]`
- Parameter: `headers` | Type: JSONArray | Required: No | Possible values: List of `{"header_name": "...", "value": "..."}` objects | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `[]`
- Parameter: `body` | Type: String | Required: No | Possible values: Raw request body string | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `""`

## Output parameters

- Field: `responseCode_output` | Type: String (Integer) | Trigger condition: Always on success — HTTP status code | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`
- Field: `responseBody_output` | Type: String | Trigger condition: Always on success — response body string | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`

**Note:** Output variables are only written if the corresponding workflow variable already exists in the execution context (declared in the **Start** task).

## Exceptions

- Code: `HTTP-ERROR-001` | Exception Name: HTTP I/O Error | Description: An `IOException` occurred during HTTP execution (from `AndromateExceptionTypes.HTTP_REQUEST_IO_EXCEPTION_ERROR`).

## Execution flowchart

Diagram Nodes:
- ResolveParams: 🔄 Resolve url, headers,\nparameters, body
- CreateClient: 🔗 Create HTTP client\nmethod, connectionTimeout, readTimeout, httpDebug
- Execute: 📡 Execute HTTP request\nGET or POST
- E1: ❌ HTTP-ERROR-001\nHTTP I/O Error
- GetResponse: 📥 Get response body\n+ HTTP status code
- StoreResult: 💾 Store HttpRequestResult\nresponseCode_output\nresponseBody_output
- LogReport: 📋 Log report\nReportSection

Workflow Flow:
- 🔄 Resolve url, headers,\nparameters, body → 🔗 Create HTTP client\nmethod, connectionTimeout, readTimeout, httpDebug
- 🔗 Create HTTP client\nmethod, connectionTimeout, readTimeout, httpDebug → 📡 Execute HTTP request\nGET or POST
- 📥 Get response body\n+ HTTP status code → 💾 Store HttpRequestResult\nresponseCode_output\nresponseBody_output
- 💾 Store HttpRequestResult\nresponseCode_output\nresponseBody_output → 📋 Log report\nReportSection
- 📋 Log report\nReportSection → Success
- ❌ HTTP-ERROR-001\nHTTP I/O Error → Error

**How it works:**

1. **Resolve parameters**: resolves dynamic variables in `url`, `headers`, `parameters`, and `body`
2. **Create HTTP client**: initializes the HTTP client with `method`, `connectionTimeout`, `readTimeout`, and `httpDebug`
3. **Execute request**: sends the HTTP GET or POST request
4. **On IOException**: throws `HTTP-ERROR-001`
5. **Get response**: retrieves the response body and HTTP status code
6. **Store result**: saves results in `HttpRequestResult` — `responseCode_output` and `responseBody_output`
7. **Log report**: records the execution report
8. **Result**: returns `HttpRequestResult`

## Code examples

### Example 1 — Simple GET request

```json
{
  "HttpRequest": [
    {
      "id": "1",
      "title": "GET device status",
      "url": "https://api.example.com/status",
      "method": "GET",
      "responseCode_output": "$http_status",
      "responseBody_output": "$http_body"
    }
  ]
}
```

### Example 2 — POST request with JSON body

```json
{
  "HttpRequest": [
    {
      "id": "2",
      "title": "POST device report",
      "url": "https://api.example.com/report",
      "method": "POST",
      "connectionTimeout": 5000,
      "readTimeout": 10000,
      "body": "{ \"deviceId\": \"$DEVICE_ID\", \"status\": \"ok\" }",
      "headers": [
        { "header_name": "Content-Type", "value": "application/json" },
        { "header_name": "Authorization", "value": "Bearer $TOKEN" }
      ],
      "responseCode_output": "$http_code",
      "responseBody_output": "$http_response"
    }
  ]
}
```

### Example 3 — GET request with query parameters

```json
{
  "HttpRequest": [
    {
      "id": "3",
      "title": "GET with parameters",
      "url": "https://api.example.com/monitoring",
      "method": "GET",
      "parameters": [
        { "param_name": "deviceId", "value": "$DEVICE_ID" },
        { "param_name": "session", "value": "$SESSION_ID" }
      ],
      "httpDebug": true,
      "responseCode_output": "$status_code",
      "responseBody_output": "$response_body"
    }
  ]
}
```

### Example 4 — POST with custom timeouts

```json
{
  "HttpRequest": [
    {
      "id": "4",
      "title": "POST with extended timeouts",
      "url": "$api_endpoint",
      "method": "POST",
      "connectionTimeout": 10000,
      "readTimeout": 30000,
      "body": "$request_payload",
      "headers": [
        { "header_name": "X-API-Key", "value": "$API_KEY" }
      ],
      "responseCode_output": "$resp_code",
      "responseBody_output": "$resp_body"
    }
  ]
}
```

## Input parameter details

### 1. `url` — Target URL

The HTTP or HTTPS URL of the endpoint to call. Supports `$workflow_variable` references — resolved at runtime.

- **Default**: `""`
- **Supports variables**: Yes

### 2. `method` — HTTP method

The HTTP method used for the request.

- Value: `"GET"` | Description: Retrieve data from the server — parameters appended to URL
- Value: `"POST"` | Description: Send data to the server — body or parameters in request body

- **Default**: `"GET"`

### 3. `connectionTimeout` — Connection timeout

Maximum time in milliseconds to establish the HTTP connection.

- **Type**: Long
- **Default**: `5000` (5 seconds)

### 4. `readTimeout` — Read timeout

Maximum time in milliseconds to wait for the server response after the connection is established.

- **Type**: Long
- **Default**: `5000` (5 seconds)

### 5. `httpDebug` — Debug logging

When `true`, enables verbose HTTP debug logging in the task report.

- **Default**: `false`

### 6. `parameters` — Query/body parameters

A JSON array of parameter objects, each with `param_name` and `value` fields. Parameters are appended to the URL for GET requests or included in the request body for POST requests.

```json
"parameters": [
  { "param_name": "deviceId", "value": "$DEVICE_ID" },
  { "param_name": "type", "value": "diagnostic" }
]
```

- **Default**: `[]`

### 7. `headers` — HTTP headers

A JSON array of header objects, each with `header_name` and `value` fields. Added to every request.

```json
"headers": [
  { "header_name": "Authorization", "value": "Bearer $TOKEN" },
  { "header_name": "Content-Type", "value": "application/json" }
]
```

- **Default**: `[]`

### 8. `body` — Raw request body

A raw string body sent with the request. Typically used with POST. Supports `$workflow_variable` references.

```json
"body": "{ \"deviceId\": \"$DEVICE_ID\" }"
```

- **Default**: `""`

## Output parameter details

### `responseCode_output` — HTTP response code

Stores the HTTP status code returned by the server as a string (from `HttpRequestResult`).

- Examples: `"200"` (OK), `"201"` (Created), `"400"` (Bad Request), `"500"` (Server Error)
- Written on every successful HTTP exchange (regardless of HTTP status value)

### `responseBody_output` — HTTP response body

Stores the raw response body string returned by the server (from `HttpRequestResult`).

- Written on every successful HTTP exchange
- May be empty if the server returns no body

## Complete JSON example

```json
{
  "HttpRequest": [
    {
      "id": "1",
      "title": "HTTP Request",
      "url": "https://api.example.com/monitoring",
      "method": "POST",
      "connectionTimeout": 5000,
      "readTimeout": 10000,
      "httpDebug": true,
      "body": "{ \"deviceId\": \"$DEVICE_ID\" }",
      "parameters": [
        { "param_name": "deviceId", "value": "$DEVICE_ID" }
      ],
      "headers": [
        { "header_name": "Authorization", "value": "Bearer $TOKEN" }
      ],
      "responseCode_output": "$HTTP_STATUS",
      "responseBody_output": "$HTTP_RESULT"
    }
  ]
}
```