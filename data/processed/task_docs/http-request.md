# Http Request Stage

## Summary

- **Internal name**: 'HttpRequest'
- **Category**: Communication
- **Purpose**: Perform an HTTP request (GET or POST) with configurable
parameters, headers, timeouts, and optional JSON body.

## Compatibility

- **Minimum AndroMate version**: '{{ ANDROMATE_FIRST_VERSION }}'
- **Maximum AndroMate version**: '{{ ANDROMATE_CURRENT_VERSION }}'
- **Minimum Android**: '{{ ANDROMATE_MIN_APP_SDK }}'
- **Maximum Android tested**: '{{ ANDROID_CURRENT_APP_SDK }}'
  - 'INTERNET'
  - 'ACCESS_NETWORK_STATE'
- **Required permissions**:

# Input parameters

- Parameter: `url` | Type: String | Required: Yes | Possible values: Valid URL | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: —
- Parameter: `method` | Type: String | Required: Yes | Possible values: GET, POST | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: GET
- Parameter: `connection_timeout` | Type: Integer | Required: No | Possible values: Time in milliseconds | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: 10000
- Parameter: `read_timeout` | Type: Integer | Required: No | Possible values: Time in milliseconds | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: 10000
- Parameter: `http_debug` | Type: Boolean | Required: No | Possible values: true / false | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: false
- Parameter: `request_body_json` | Type: String | Required: No | Possible values: Valid JSON string | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: —
- Parameter: `parameters` | Type: List | Required: No | Possible values: List of parameters | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: []
- Parameter: `headers` | Type: List | Required: No | Possible values: List of headers | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: []

# Output parameters

- Field: `http_response_output` | Type: String | Trigger condition: When request succeeds | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`
- Field: `http_error_output` | Type: String | Trigger condition: When request fails | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`
- Field: `http_status_code` | Type: Integer | Trigger condition: Always | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: -1

## Exceptions

- Code: HTTP_REQUEST_IO_EXCEPTION_ERROR | Exception Name: HTTP I/O Error | Description: Connection or server access error (IOException).
- Code: HTTP_REQUEST_INVALID_URL | Exception Name: Invalid URL | Description: The provided URL is invalid or empty.
- Code: HTTP_REQUEST_TIMEOUT | Exception Name: HTTP Timeout | Description: Connection or read timeout exceeded.

# Flowchart

The following diagram illustrates the actual implementation based on Android code:

flowchart TD
    Start([Start HttpRequestTask]) --> ResolveParams[🔄 Resolve Parameters<br/>URL, headers, params, body]
    
    ResolveParams --> ValidateURL{URL<br/>valid ?}
    
    ValidateURL -->|No| E1[❌ HTTP_REQUEST_INVALID_URL]
    ValidateURL -->|Yes| CreateClient[🔗 Create HttpClient<br/>Method, timeouts, debug]
    
    CreateClient --> Execute[📡 Execute HTTP Request<br/>GET or POST]
    
    Execute -->|IOException| E2[❌ HTTP_REQUEST_IO_EXCEPTION_ERROR]
    Execute -->|Timeout| E3[❌ HTTP_REQUEST_TIMEOUT]
    Execute -->|Success| GetResponse[📥 Get Response<br/>Body + HTTP Code]
    
    GetResponse --> StoreResult[💾 Store Result<br/>HttpRequestResult]
    
    StoreResult --> LogReport[📋 Log Report<br/>ReportSection]
    
    LogReport --> Success([✅ Success])
    
    E1 --> Error([❌ Exception])
    E2 --> Error
    E3 --> Error
    
    style Start fill:#e3f2fd
    style Success fill:#c8e6c9
    style Error fill:#ffcdd2
    style ResolveParams fill:#fff9c4
    style CreateClient fill:#f3e5f5
    style Execute fill:#f3e5f5
    style GetResponse fill:#fff9c4
    style StoreResult fill:#c8e6c9
    style E1 fill:#ffcdd2
    style E2 fill:#ffcdd2
    style E3 fill:#ffcdd2

**How it works:**

1. **Resolve parameters**: Resolves dynamic variables in URL, headers, parameters and body
2. **Validate URL**: Checks that URL is valid and not empty
3. **Create HTTP client**: Initializes HttpClient with parameters (timeouts, method, debug)
4. **Execute request**: Sends HTTP request (GET or POST)
5. **Get response**: Retrieves response body and HTTP status code
6. **Store result**: Saves results in HttpRequestResult
7. **Log report**: Records execution report
8. **Result**: Returns success or exception

# Parameter details

## 1. Input parameter: `url`

Target endpoint URL.

### Example

"url": "https://api.example.com/monitoring"

## 2. Input parameter: `method`

HTTP method used for the request.

### Default value

'GET'

### Possible values

'GET', 'POST'

### Example

"method": "POST"

## 3. Input parameter: `connection_timeout`

Maximum time (ms) to establish connection.

### Default value

'10000'

## 4. Input parameter: `read_timeout`

Maximum time (ms) to wait for server response.

### Default value

'10000'

## 5. Input parameter: `http_debug`

Enable verbose HTTP logging.

### Default value

'false'

## 6. Input parameter: `request_body_json`

Optional JSON body (used mainly with POST).

### Example

"request_body_json": "{ \"deviceId\": \"$DEVICE_ID\" }"

## 7. Input parameter: `parameters`

List of query parameters.

### Example

"parameters": [
  { "param_name": "deviceId", "value": "$DEVICE_ID" }
]

## 8. Input parameter: `headers`

List of HTTP headers.

### Example

"headers": [
  { "param_name": "Authorization", "value": "Bearer $TOKEN" }
]

# Output details

## 1. Result variable: `http_error_output`

Contains error output when request fails.

## 2. Result variable: `http_response_output`

Contains response body when request succeeds.

## 3. Result variable: `http_status_code`

Contains HTTP status code returned by server.

# Complete JSON example

{
  "HttpRequest": [
    {
      "id": "-1",
      "title": "Http Request Stage",
      "url": "https://api.example.com/monitoring",
      "method": "POST",
      "connection_timeout": 5000,
      "read_timeout": 10000,
      "http_debug": true,
      "request_body_json": "{ \"deviceId\": \"$DEVICE_ID\" }",
      "parameters": [
        { "param_name": "deviceId", "value": "$DEVICE_ID" }
      ],
      "headers": [
        { "param_name": "Authorization", "value": "Bearer $TOKEN" }
      ],
      "http_error_output": "$HTTP_ERROR",
      "http_response_output": "$HTTP_RESULT",
      "http_status_code": "$HTTP_STATUS"
    }
  ]
}