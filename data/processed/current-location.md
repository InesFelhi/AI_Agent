# Current Location Stage

## Summary

- **Internal name**: `Current Location`
- **Category**: Location
- **Purpose**: Retrieve the device's current GPS location (latitude,
longitude, accuracy) with configurable timeout handling.

## Compatibility

- **Minimum AndroMate version**: `{{ ANDROMATE_FIRST_VERSION }}`
- **Maximum AndroMate version**: `{{ ANDROMATE_CURRENT_VERSION }}`
- **Minimum Android**: `{{ ANDROMATE_MIN_APP_SDK }}`
- **Maximum Android tested**: `{{ ANDROID_CURRENT_APP_SDK }}`
- **Supported manufacturers**:
  - ✅ All manufacturers (tested on Samsung One UI 6.x / 7.x / 8.x and Google Pixel Android Stock)
- **Required permissions**:
  - `ACCESS_FINE_LOCATION`
  - `ACCESS_COARSE_LOCATION`
  - `ACCESS_BACKGROUND_LOCATION` (if used in background)
  - Location services must be enabled on the device

## Detailed description

The **Current Location Stage** task requests the device GPS system to
retrieve the current geographic position.

It is used to:

- Collect device geolocation (latitude / longitude)
- Measure GPS accuracy
- Attach location data to telemetry or monitoring reports
- Trigger actions based on geographic position
- Track device movement or presence in a defined area

The task handles:

- requesting GPS updates from Android location services,
- configurable timeout handling,
- retrieval of **latitude**, **longitude**, and **accuracy** values.

## Input parameters

- Parameter: `location_timeout` | Type: Integer | Required: Yes | Possible values: Time in milliseconds | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: 10000

## Outputs

- Field: `location_latitude_output` | Type: Double | Trigger condition: When location is successfully retrieved | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`
- Field: `location_longitude_output` | Type: Double | Trigger condition: When location is successfully retrieved | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`
- Field: `location_accuracy_output` | Type: Float | Trigger condition: When location is successfully retrieved | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`

## Exceptions

- Code: GPS_GET_CURRENT_LOCATION_NULL_VALUE | Exception Name: Null Location | Description: Location could not be obtained (null) - the GPS provider returned a null position.
- Code: GPS_GET_CURRENT_LOCATION_TIMEOUT | Exception Name: GPS Timeout | Description: Failed to obtain GPS position within the specified timeout (location_timeout).
- Code: GPS_APP_HAS_NO_LOCATION_PERMISSION | Exception Name: Missing Location Permission | Description: The application does not have ACCESS_FINE_LOCATION or ACCESS_COARSE_LOCATION permission.

# Flowchart

The following diagram illustrates the actual implementation based on Android code:

Diagram Nodes:
- E2: ❌ GPS_APP_HAS_NO_LOCATION_PERMISSION
- GetLoc: 📍 getCurrentLocation Priority: HIGH_ACCURACY Timeout: location_timeout_ms
- E6: ❌ GPS_GET_CURRENT_LOCATION_TIMEOUT
- E3: ❌ GPS_GET_CURRENT_LOCATION_NULL_VALUE
- ExtractData: 📊 Extract Data Latitude, Longitude, Accuracy
- StoreResult: 💾 Store Result LocationTaskResult
- LogReport: 📋 Log Report ReportSection

Workflow Flow:
- 📊 Extract Data Latitude, Longitude, Accuracy → 💾 Store Result LocationTaskResult
- 💾 Store Result LocationTaskResult → 📋 Log Report ReportSection
- 📋 Log Report ReportSection → Success
- ❌ GPS_APP_HAS_NO_LOCATION_PERMISSION → Error
- ❌ GPS_GET_CURRENT_LOCATION_NULL_VALUE → Error
- ❌ GPS_GET_CURRENT_LOCATION_TIMEOUT → Error

**How it works:**

1. **Permission check**: Ensures the app has ACCESS_FINE_LOCATION and ACCESS_COARSE_LOCATION permissions
2. **GPS request**: Gets the current position with high accuracy via FusedLocationProviderClient
3. **Wait with timeout**: Waits for GPS response with configurable timeout
4. **Validation**: Verifies that the obtained position is not null
5. **Extract data**: Retrieves latitude, longitude and accuracy
6. **Storage**: Saves results in LocationTaskResult
7. **Logging**: Records execution report
8. **Result**: Returns success or exception

**Legend:**

- 🔵 **Blue**: Start
- 🟢 **Green**: Success
- 🔴 **Red**: Exceptions
- 🟡 **Yellow**: Data operations
- 🟣 **Purple**: GPS requests

## Parameter details

## 1. Input parameter: `location_timeout`

Defines the maximum time (in milliseconds) to wait for a valid GPS fix.

### Example

```json
"location_timeout": 15000
```

### Details

- If a valid GPS location is not obtained within the specified
timeout, the task fails.
- Recommended values: 5000 -- 30000 ms.

# Output details

## 2. Result variable: `location_latitude_output`

Stores the latitude value returned by the GPS provider.

### Example

```json
"location_latitude_output": "$LATITUDE"
```

## 3. Result variable: `location_longitude_output`

Stores the longitude value returned by the GPS provider.

### Example

```json
"location_longitude_output": "$LONGITUDE"
```

## 4. Result variable: `location_accuracy_output`

Stores the accuracy of the location fix in meters.

### Example

```json
"location_accuracy_output": "$ACCURACY"
```

### Details

- Lower value = better accuracy.
- **Note**: The accuracy value represents the margin of error. For example, if the latitude is 48.8566 with an accuracy of 10 meters, the actual position is **latitude ± 10 meters** with a probability of approximately **68%**.

## Complete JSON example

```json
{
  "Current Location": [
    {
      "id": "-1",
      "title": "Current Location",
      "location_timeout": 15000,
      "location_latitude_output": "$LATITUDE",
      "location_longitude_output": "$LONGITUDE",
      "location_accuracy_output": "$ACCURACY"
    }
  ]
}
```