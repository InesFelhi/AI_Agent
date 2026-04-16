# Upload File

## Summary

- **Internal name**: `UploadTask`
- **Category**: Communication
- **Purpose**: Upload a local file from the Android device to a remote server via HTTP multipart upload and report transfer statistics.
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
  - `READ_EXTERNAL_STORAGE`

## Detailed description

The **Upload File** task reads a local file from `path` and uploads it to the remote server at `url` using HTTP multipart upload via `FileTransferClient.uploadMultipart()` (OkHttp). The call is asynchronous and waits for a callback. Progress is logged as `bytes/totalBytes` in the task report.

The `path` parameter is the local file to upload; `url` is the server endpoint receiving the file. Both support `$workflow_variable` references — resolved at runtime before the transfer starts. The operation is bounded by `timeout_ms`. If the timeout is exceeded, an `AndromateTimeoutException` is thrown. If the transfer fails for any other reason, exception `DOWNLOAD-UPLOAD-ERROR-001` is raised.

On success, the task writes the file size, transfer duration, and bitrate to the three output variables from `TransferStatResult`.

## Input parameters

- Parameter: `url` | Type: String | Required: Yes | Possible values: Valid HTTP/HTTPS server endpoint URL — supports `$variable` | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `""`
- Parameter: `path` | Type: String | Required: Yes | Possible values: Absolute local file path to upload — supports `$variable` | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `""`
- Parameter: `timeout_ms` | Type: Long | Required: No | Possible values: Timeout in milliseconds | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `5000`

## Output parameters

- Field: `file_size_output` | Type: Long | Trigger condition: Always on success — uploaded file size in bytes | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`
- Field: `duration_ms_output` | Type: Long | Trigger condition: Always on success — transfer duration in milliseconds | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`
- Field: `bitrate_output` | Type: Double | Trigger condition: Always on success — transfer bitrate in bytes/second | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`

**Note:** Output variables are only written if the corresponding workflow variable already exists in the execution context (declared in the **Start** task). The outputs are file transfer statistics, not HTTP response data.

## Exceptions

- Code: `DOWNLOAD-UPLOAD-ERROR-001` | Exception Name: File Transfer Error | Description: A file transfer error occurred (from `AndromateExceptionTypes.FILE_TRANSFER_ERROR`). Raised on any upload failure.
- Code: Timeout | Exception Name: Timeout | Description: `AndromateTimeoutException` — the operation exceeded `timeout_ms`. No specific exception code.

## Execution flowchart

Diagram Nodes:
- ResolveParams: 🔄 Resolve url + path\n+ timeout_ms
- CallClient: 🌐 FileTransferClient.uploadMultipart\nOkHttp — async multipart upload
- WaitCallback: ⏳ Wait for async callback
- ETimeout: ❌ Timeout\nAndromateTimeoutException
- E1: ❌ DOWNLOAD-UPLOAD-ERROR-001\nFile Transfer Error
- WriteOutputs: 💾 Write TransferStatResult\nfile_size_output\nduration_ms_output\nbitrate_output

Workflow Flow:
- 🔄 Resolve url + path\n+ timeout_ms → 🌐 FileTransferClient.uploadMultipart\nOkHttp — async multipart upload
- 🌐 FileTransferClient.uploadMultipart\nOkHttp — async multipart upload → ⏳ Wait for async callback
- 💾 Write TransferStatResult\nfile_size_output\nduration_ms_output\nbitrate_output → Success
- ❌ Timeout\nAndromateTimeoutException → Error
- ❌ DOWNLOAD-UPLOAD-ERROR-001\nFile Transfer Error → Error

**How it works:**

1. **Resolve parameters**: `url`, `path`, and `timeout_ms` are resolved from the workflow context
2. **Call FileTransferClient**: invokes `FileTransferClient.uploadMultipart()` via OkHttp — HTTP multipart upload, asynchronous
3. **Wait for callback**: blocks until the async callback fires or `timeout_ms` is exceeded
4. **On timeout**: throws `AndromateTimeoutException`
5. **On error**: throws `DOWNLOAD-UPLOAD-ERROR-001` (file transfer error)
6. **On success**: writes `file_size_output`, `duration_ms_output`, and `bitrate_output` from `TransferStatResult`
7. **Result**: returns `TransferStatResult`

## Code examples

### Example 1 — Upload a file with default timeout

```json
{
  "UploadTask": [
    {
      "id": "1",
      "title": "Upload report",
      "url": "https://api.example.com/upload",
      "path": "/sdcard/Download/report.json",
      "file_size_output": "$uploaded_bytes",
      "duration_ms_output": "$upload_duration_ms",
      "bitrate_output": "$upload_bitrate"
    }
  ]
}
```

### Example 2 — Upload using workflow variables

```json
{
  "UploadTask": [
    {
      "id": "2",
      "title": "Upload dynamic file",
      "url": "$upload_endpoint",
      "path": "$local_file_path",
      "file_size_output": "$file_size",
      "duration_ms_output": "$upload_time",
      "bitrate_output": "$upload_rate"
    }
  ]
}
```

### Example 3 — Upload with custom timeout

```json
{
  "UploadTask": [
    {
      "id": "3",
      "title": "Upload large file with 60s timeout",
      "url": "https://storage.example.com/results/run1.zip",
      "path": "/sdcard/results/run1.zip",
      "timeout_ms": 60000,
      "file_size_output": "$zip_size",
      "duration_ms_output": "$zip_upload_ms",
      "bitrate_output": "$zip_bitrate"
    }
  ]
}
```

## Input parameter details

### 1. `url` — Upload endpoint

The HTTP or HTTPS URL of the server endpoint receiving the uploaded file. Supports `$workflow_variable` references.

- **Default**: `""`
- **Supports variables**: Yes

### 2. `path` — Local file path

The absolute path of the file on the Android device to upload. The file must exist and be readable. This is the **local** file sent to the server.

- Valid: `/sdcard/Download/report.json` | Invalid: `report.json` (relative path)
- Valid: `/data/local/tmp/test.bin` | Invalid: `sdcard/test.bin` (no leading `/`)
- Valid: `$local_file_path` | Invalid: `""` (empty)

- **Default**: `""`
- **Supports variables**: Yes

### 3. `timeout_ms` — Operation timeout

Maximum time in milliseconds allowed for the entire upload operation. If exceeded, an `AndromateTimeoutException` is thrown.

- **Type**: Long
- **Default**: `5000` (5 seconds)
- **For large files**: increase to `60000` or higher to avoid premature timeouts

## Output parameter details

### `file_size_output` — Uploaded file size

Stores the total size of the uploaded file in bytes (Long), from `TransferStatResult`, in the specified workflow variable.

- Written only on successful completion
- Value is the byte count of the local file that was uploaded

### `duration_ms_output` — Transfer duration

Stores the total elapsed time of the upload operation in milliseconds (Long), from `TransferStatResult`.

- Measured from the moment the transfer starts to completion of the multipart upload

### `bitrate_output` — Transfer bitrate

Stores the measured transfer bitrate in bytes per second (Double), from `TransferStatResult`.

- Computed as `file_size / (duration_ms / 1000.0)`
- Useful for network upload throughput reporting

## Complete JSON example

```json
{
  "UploadTask": [
    {
      "id": "1",
      "title": "Upload report file",
      "url": "https://api.example.com/upload",
      "path": "/sdcard/Download/report.json",
      "timeout_ms": 30000,
      "file_size_output": "$uploaded_bytes",
      "duration_ms_output": "$upload_ms",
      "bitrate_output": "$upload_bitrate_bps"
    }
  ]
}
```