# Download File

## Summary

- **Internal name**: `DownloadTask`
- **Category**: Communication
- **Purpose**: Download a file from a remote URL to a local path on the Android device and report transfer statistics.
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
  - `WRITE_EXTERNAL_STORAGE`

## Detailed description

The **Download File** task opens an HTTP or HTTPS connection to the remote `url` and streams the response body to the local file at `path`, using OkHttp via `FileTransferClient.downloadToFile()`. The operation runs asynchronously and waits for a callback. Progress is logged as `bytes/totalBytes` in the task report.

Both `url` and `path` support `$workflow_variable` references — resolved at runtime before the transfer starts. The operation is bounded by `timeout_ms`. If the timeout is exceeded, an `AndromateTimeoutException` is thrown. If the transfer fails for any other reason, exception `DOWNLOAD-UPLOAD-ERROR-001` is raised.

On success, the task writes the file size, transfer duration, and bitrate to the three output variables from `TransferStatResult`.

## Input parameters

- Parameter: `url` | Type: String | Required: Yes | Possible values: Valid HTTP/HTTPS URL — supports `$variable` | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `""`
- Parameter: `path` | Type: String | Required: Yes | Possible values: Absolute local path (e.g. `/sdcard/Downloads/file.zip`) — supports `$variable` | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `""`
- Parameter: `timeout_ms` | Type: Long | Required: No | Possible values: Timeout in milliseconds | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `5000`

## Output parameters

- Field: `file_size_output` | Type: Long | Trigger condition: Always on success — downloaded file size in bytes | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`
- Field: `duration_ms_output` | Type: Long | Trigger condition: Always on success — transfer duration in milliseconds | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`
- Field: `bitrate_output` | Type: Double | Trigger condition: Always on success — transfer bitrate in bytes/second | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`

**Note:** Output variables are only written if the corresponding workflow variable already exists in the execution context (declared in the **Start** task).

## Exceptions

- Code: `DOWNLOAD-UPLOAD-ERROR-001` | Exception Name: File Transfer Error | Description: A file transfer error occurred (from `AndromateExceptionTypes.FILE_TRANSFER_ERROR`). Raised on any download failure.
- Code: Timeout | Exception Name: Timeout | Description: `AndromateTimeoutException` — the operation exceeded `timeout_ms`. No specific exception code.

## Execution flowchart

Diagram Nodes:
- ResolveParams: 🔄 Resolve url + path\n+ timeout_ms
- CallClient: 🌐 FileTransferClient.downloadToFile\nOkHttp — async
- WaitCallback: ⏳ Wait for async callback
- ETimeout: ❌ Timeout\nAndromateTimeoutException
- E1: ❌ DOWNLOAD-UPLOAD-ERROR-001\nFile Transfer Error
- WriteOutputs: 💾 Write TransferStatResult\nfile_size_output\nduration_ms_output\nbitrate_output

Workflow Flow:
- 🔄 Resolve url + path\n+ timeout_ms → 🌐 FileTransferClient.downloadToFile\nOkHttp — async
- 🌐 FileTransferClient.downloadToFile\nOkHttp — async → ⏳ Wait for async callback
- 💾 Write TransferStatResult\nfile_size_output\nduration_ms_output\nbitrate_output → Success
- ❌ Timeout\nAndromateTimeoutException → Error
- ❌ DOWNLOAD-UPLOAD-ERROR-001\nFile Transfer Error → Error

**How it works:**

1. **Resolve parameters**: `url`, `path`, and `timeout_ms` are resolved from the workflow context
2. **Call FileTransferClient**: invokes `FileTransferClient.downloadToFile()` via OkHttp — the call is asynchronous
3. **Wait for callback**: blocks until the async callback fires or `timeout_ms` is exceeded
4. **On timeout**: throws `AndromateTimeoutException`
5. **On error**: throws `DOWNLOAD-UPLOAD-ERROR-001` (file transfer error)
6. **On success**: writes `file_size_output`, `duration_ms_output`, and `bitrate_output` from `TransferStatResult`
7. **Result**: returns `TransferStatResult`

## Code examples

### Example 1 — Download a file with default timeout

```json
{
  "DownloadTask": [
    {
      "id": "1",
      "title": "Download firmware package",
      "url": "https://example.com/firmware.zip",
      "path": "/sdcard/Downloads/firmware.zip",
      "file_size_output": "$downloaded_bytes",
      "duration_ms_output": "$download_duration_ms",
      "bitrate_output": "$download_bitrate"
    }
  ]
}
```

### Example 2 — Download using workflow variables

```json
{
  "DownloadTask": [
    {
      "id": "2",
      "title": "Download dynamic target",
      "url": "$remote_url",
      "path": "$local_path",
      "file_size_output": "$file_size",
      "duration_ms_output": "$dl_time",
      "bitrate_output": "$dl_bitrate"
    }
  ]
}
```

### Example 3 — Download with custom timeout

```json
{
  "DownloadTask": [
    {
      "id": "3",
      "title": "Download with 30s timeout",
      "url": "https://example.com/large-dataset.csv",
      "path": "/sdcard/data/dataset.csv",
      "timeout_ms": 30000,
      "file_size_output": "$csv_size",
      "duration_ms_output": "$csv_dl_ms",
      "bitrate_output": "$csv_bitrate"
    }
  ]
}
```

### Example 4 — Download and measure transfer speed

```json
{
  "DownloadTask": [
    {
      "id": "4",
      "title": "Download speed test",
      "url": "https://example.com/testfile.bin",
      "path": "/sdcard/Downloads/testfile.bin",
      "timeout_ms": 15000,
      "file_size_output": "$bytes_received",
      "duration_ms_output": "$elapsed_ms",
      "bitrate_output": "$speed_bps"
    }
  ]
}
```

## Input parameter details

### 1. `url` — Remote file URL

The full HTTP or HTTPS URL of the remote resource to download. Must be a non-empty, well-formed URL including the scheme (`http://` or `https://`).

Supports `$workflow_variable` references — resolved at runtime before the transfer starts.

- Valid: `https://example.com/file.zip` | Invalid: `file.zip` (no scheme)
- Valid: `http://192.168.1.1/data.bin` | Invalid: `ftp://example.com/file` (unsupported scheme)
- Valid: `$remote_url` | Invalid: `""` (empty)

- **Default**: `""`

### 2. `path` — Local destination path

The absolute path on the Android device where the downloaded file will be saved. The parent directory must exist and the application must have write access to it.

- **Must be absolute**: paths not starting with `/` are not valid
- **Parent directory must exist**: the task does not create missing intermediate directories
- **Supports variables**: Yes — e.g. `/sdcard/$filename`
- **Default**: `""`

### 3. `timeout_ms` — Operation timeout

Maximum time in milliseconds allowed for the entire download operation (including connection and data transfer). If exceeded, an `AndromateTimeoutException` is thrown.

- **Type**: Long
- **Default**: `5000` (5 seconds)
- **For large files**: increase to `30000` or higher to avoid premature timeouts

## Output parameter details

### `file_size_output` — Downloaded file size

Stores the total size of the downloaded file in bytes (Long), from `TransferStatResult`, in the specified workflow variable.

- Written only on successful completion
- Value is the byte count of the written file (e.g. `204800` for 200 KB)

### `duration_ms_output` — Transfer duration

Stores the total elapsed time of the download operation in milliseconds (Long), from `TransferStatResult`.

- Measured from the moment the transfer starts to when the last byte is written to disk

### `bitrate_output` — Transfer bitrate

Stores the measured transfer bitrate in bytes per second (Double), from `TransferStatResult`.

- Computed as `file_size / (duration_ms / 1000.0)`
- Useful for network throughput reporting

## Complete JSON example

```json
{
  "DownloadTask": [
    {
      "id": "1",
      "title": "Download test file",
      "url": "https://speed.example.com/10mb.bin",
      "path": "/sdcard/Download/10mb.bin",
      "timeout_ms": 30000,
      "file_size_output": "$dl_bytes",
      "duration_ms_output": "$dl_time_ms",
      "bitrate_output": "$dl_bitrate_bps"
    }
  ]
}
```