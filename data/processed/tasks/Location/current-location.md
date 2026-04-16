# Current Location Stage

## Summary

- **Internal name**: `GetCurrentLocation`
- **Category**: Location
- **Purpose**: Retrieve the device's current GPS location (latitude,
longitude, accuracy) with configurable timeout handling.
- **Task type**: Normal

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

- Parameter: `location_timeout_ms` | Type: Integer | Required: No | Possible values: Time in milliseconds | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `10000`

## Output parameters

- Field: `location_lat_output` | Type: Double | Trigger condition: When location is successfully retrieved | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`
- Field: `location_long_output` | Type: Double | Trigger condition: When location is successfully retrieved | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`
- Field: `location_accuracy_output` | Type: Float | Trigger condition: When location is successfully retrieved | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`

## Exceptions

- Code: `GPS-ERROR-001` | Description: Failed to obtain GPS position within the specified timeout (`location_timeout_ms`).
- Code: `GPS-ERROR-002` | Description: Location could not be obtained — the GPS provider returned a null position.
- Code: `GPS-ERROR-003` | Description: Location services are disabled on the device. Enable GPS in device settings.
- Code: `GPS-ERROR-004` | Description: The application does not have `ACCESS_FINE_LOCATION` or `ACCESS_COARSE_LOCATION` permission.

## Execution flowchart

Diagram Nodes:
- E3: ❌ GPS-ERROR-003\nDisabled location
- E4: ❌ GPS-ERROR-004\nNo location permission
- GetLoc: 📍 getCurrentLocation\nPriority: HIGH_ACCURACY\nTimeout: location_timeout_ms
- E1: ❌ GPS-ERROR-001\nGPS timeout
- E2: ❌ GPS-ERROR-002\nNull location
- ExtractData: 📊 Extract\nlocation_lat_output\nlocation_long_output\nlocation_accuracy_output

Workflow Flow:
- 📊 Extract\nlocation_lat_output\nlocation_long_output\nlocation_accuracy_output → Success
- ❌ GPS-ERROR-001\nGPS timeout → Error
- ❌ GPS-ERROR-002\nNull location → Error
- ❌ GPS-ERROR-003\nDisabled location → Error
- ❌ GPS-ERROR-004\nNo location permission → Error

**How it works:**

1. **Check location services**: Throws `GPS-ERROR-003` if GPS is disabled on the device
2. **Permission check**: Throws `GPS-ERROR-004` if `ACCESS_FINE_LOCATION` is not granted
3. **GPS request**: Gets the current position with high accuracy via `FusedLocationProviderClient`
4. **Wait with timeout**: Throws `GPS-ERROR-001` if GPS does not respond within `location_timeout_ms`
5. **Null check**: Throws `GPS-ERROR-002` if the GPS provider returns a null location
6. **Extract data**: Retrieves latitude → `location_lat_output`, longitude → `location_long_output`, accuracy → `location_accuracy_output`
7. **Result**: Returns `LocationTaskResult` on success

## Input parameter details

### 1. Input parameter: `location_timeout_ms`

Maximum time (in milliseconds) to wait for a valid GPS fix before throwing `GPS-ERROR-001`.

#### Example

```json
"location_timeout_ms": 15000
```

- **Default**: `10000` ms
- Recommended values: 5000–30000 ms

## Output parameter details

### 2. Result variable: `location_lat_output`

Stores the latitude value returned by the GPS provider.

#### Example

```json
"location_lat_output": "$LATITUDE"
```

### 3. Result variable: `location_long_output`

Stores the longitude value returned by the GPS provider.

#### Example

```json
"location_long_output": "$LONGITUDE"
```

### 4. Result variable: `location_accuracy_output`

Stores the accuracy of the location fix in meters (rounded to 3 decimal places).

#### Example

```json
"location_accuracy_output": "$ACCURACY"
```

- Lower value = better accuracy.

## Complete JSON example

```json
{
  "GetCurrentLocation": [
    {
      "id": "-1",
      "title": "Get Current Location",
      "location_timeout_ms": 15000,
      "location_lat_output": "$LATITUDE",
      "location_long_output": "$LONGITUDE",
      "location_accuracy_output": "$ACCURACY"
    }
  ]
}
```