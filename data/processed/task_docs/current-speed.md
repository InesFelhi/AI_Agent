# Current Speed Stage

## Summary

- **Internal name**: 'Current Speed'
- **Category**: Location
- **Purpose**: Measure the device's current speed using GPS updates,
with configurable sampling, timeout, and accuracy filtering.

## Compatibility

- **Minimum AndroMate version**: '{{ ANDROMATE_FIRST_VERSION }}'
- **Maximum AndroMate version**: '{{ ANDROMATE_CURRENT_VERSION }}'
- **Minimum Android**: '{{ ANDROMATE_MIN_APP_SDK }}'
- **Maximum Android tested**: '{{ ANDROID_CURRENT_APP_SDK }}'
  - ✅ All manufacturers (tested on Samsung One UI 6.x / 7.x / 8.x and Google Pixel Android Stock)
- **Supported manufacturers**:
  - 'ACCESS_FINE_LOCATION'
  - 'ACCESS_COARSE_LOCATION'
  - 'ACCESS_BACKGROUND_LOCATION' (if used in background)
  - Location services must be enabled on the device
- **Required permissions**:

## Detailed description

The **Current Speed Stage** task calculates the device's movement speed
based on GPS location updates.

It is used to:

- Measure real-time speed (km/h)
- Track movement over time
- Compute traveled distance
- Filter speed measurements based on GPS accuracy
- Attach speed metrics to telemetry or monitoring reports

The task handles:

- configurable GPS timeout handling,
- configurable sampling interval,
- maximum allowed speed accuracy filtering,
- calculation of speed value in km/h,
- calculation of traveled distance in meters.

## Flowchart

The following diagram illustrates the actual implementation based on Android code:

flowchart TD
    Start([Start GetCurrentSpeedTask]) --> CheckLocation{Location services<br/>enabled?}
    
    CheckLocation -->|No| E1[❌ GPS_DISABLED_LOCATION]
    CheckLocation -->|Yes| CheckPerm{Has<br/>ACCESS_FINE_LOCATION<br/>permission?}
    
    CheckPerm -->|No| E2[❌ GPS_APP_HAS_NO_LOCATION_PERMISSION]
    CheckPerm -->|Yes| GetLocA[📍 getCurrentLocation A<br/>Priority: HIGH_ACCURACY<br/>Timeout: location_timeout_ms]
    
    GetLocA -->|Timeout| E6[❌ GPS_GET_CURRENT_LOCATION_TIMEOUT]
    GetLocA -->|Success| CheckNullA{locA == null?}
    
    CheckNullA -->|Yes| E3[❌ GPS_GET_CURRENT_LOCATION_NULL_VALUE]
    CheckNullA -->|No| CheckAccA{locA.accuracy ><br/>max_speed_accuracy?}
    
    CheckAccA -->|Yes| E4[❌ GPS_LOCATION_ACCURACY_TOO_LOW<br/>accuracy too high]
    CheckAccA -->|No| StoreA[Store:<br/>locA position<br/>tA = System.nanoTime]
    
    StoreA --> Sleep[⏱️ deepSleep<br/>sample_interval_ms<br/>default: 10000ms]
    
    Sleep --> GetLocB[📍 getCurrentLocation B<br/>Priority: HIGH_ACCURACY<br/>Timeout: location_timeout_ms]
    
    GetLocB -->|Timeout| E6
    GetLocB -->|Success| CheckNullB{locB == null?}
    
    CheckNullB -->|Yes| E3
    CheckNullB -->|No| CheckAccB{locB.accuracy ><br/>max_speed_accuracy?}
    
    CheckAccB -->|Yes| E4
    CheckAccB -->|No| StoreB[Store:<br/>locB position<br/>tB = System.nanoTime]
    
    StoreB --> CalcDist[Calculate:<br/>distanceM = locA.distanceTo locB]
    
    CalcDist --> CalcDelta[Calculate:<br/>deltaSec = tB - tA / 1e9]
    
    CalcDelta --> CheckDelta{deltaSec <=<br/>MIN_GPS_DELTA_TIME<br/>0.2 sec?}
    
    CheckDelta -->|Yes| E5[❌ GPS_SPEED_DELTA_TIME_TOO_SMALL]
    CheckDelta -->|No| CalcSpeed[Calculate:<br/>speedMps = distanceM / deltaSec<br/>speedKmh = speedMps × 3.6]
    
    CalcSpeed --> Round[Round to 3 decimals:<br/>speedKmh<br/>distanceM<br/>max locA.accuracy, locB.accuracy]
    
    Round --> SetResults[✅ Set TaskResult:<br/>currentSpeedKmH<br/>distanceM<br/>accuracyUsed]
    
    SetResults --> Success([Task completed successfully])
    
    E1 --> Error([Task failed with exception])
    E2 --> Error
    E3 --> Error
    E4 --> Error
    E5 --> Error
    E6 --> Error
    
    GetLocA -.Runtime Exception.-> E7[❌ OTHER_ERROR]
    GetLocB -.Runtime Exception.-> E7
    CalcDist -.Runtime Exception.-> E7
    CalcSpeed -.Runtime Exception.-> E7
    E7 --> Error
    
    style Start fill:#e3f2fd
    style Success fill:#c8e6c9
    style Error fill:#ffcdd2
    style CalcSpeed fill:#fff9c4
    style CalcDist fill:#fff9c4
    style CalcDelta fill:#fff9c4
    style Round fill:#fff9c4
    style Sleep fill:#f3e5f5
    style SetResults fill:#c8e6c9
    style E1 fill:#ffcdd2
    style E2 fill:#ffcdd2
    style E3 fill:#ffcdd2
    style E4 fill:#ffcdd2
    style E5 fill:#ffcdd2
    style E6 fill:#ffcdd2
    style E7 fill:#ffcdd2

**How it works:**

1. **Initial checks**: Verifies location services are enabled and app has location permissions
2. **First GPS sample**: Gets initial position with high accuracy priority
3. **Accuracy validation**: Ensures GPS accuracy is acceptable (≤ max threshold)
4. **Wait period**: Pauses for the configured sampling interval (default 10 seconds)
5. **Second GPS sample**: Gets new position with same accuracy priority
6. **Distance calculation**: Measures distance traveled between the two positions
7. **Time calculation**: Calculates elapsed time between samples
8. **Delta validation**: Ensures enough time passed (≥ 0.2 seconds) for reliable calculation
9. **Speed calculation**: Computes speed in km/h from distance and time
10. **Results**: Returns speed, distance, and accuracy (rounded to 3 decimals)

**Legend:**

- 🔵 **Blue**: Start
- 🟢 **Green**: Success
- 🔴 **Red**: Exceptions
- 🟡 **Yellow**: Calculations
- 🟣 **Purple**: Time delay
- **Dotted lines**: Runtime exceptions

## Input parameters

- Parameter: `location_timeout` | Type: Integer | Required: Yes | Possible values: Time in milliseconds | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: 20000
- Parameter: `sample_interval` | Type: Integer | Required: Yes | Possible values: Time in milliseconds | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: 1000
- Parameter: `max_speed_accuracy` | Type: Float | Required: Yes | Possible values: Accuracy in meters | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: 5.0

## Outputs

- Field: `speed_value_output` | Type: Double | Trigger condition: When calculation is successful | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`
- Field: `distance_output` | Type: Double | Trigger condition: When calculation is successful | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`
- Field: `speed_accuracy_used` | Type: Float | Trigger condition: When calculation is successful | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`

## Exceptions

- Code: GPS_DISABLED_LOCATION | Exception Name: GPS Disabled | Description: Location services are disabled on the device. Enable GPS in device settings.
- Code: GPS_APP_HAS_NO_LOCATION_PERMISSION | Exception Name: Missing Location Permission | Description: The app does not have ACCESS_FINE_LOCATION permission. Grant location permissions to AndroMate.
- Code: GPS_GET_CURRENT_LOCATION_NULL_VALUE | Exception Name: GPS Position Null | Description: Unable to obtain GPS position. The GPS provider returned a null location.
- Code: GPS_LOCATION_ACCURACY_TOO_LOW | Exception Name: Insufficient GPS Accuracy | Description: GPS accuracy exceeds the maximum threshold (max_speed_accuracy). Current accuracy is too low for reliable speed measurement.
- Code: GPS_SPEED_DELTA_TIME_TOO_SMALL | Exception Name: Time Delta Too Small | Description: Time difference between two GPS samples is too small (< 0.2s). Cannot calculate reliable speed.
- Code: GPS_GET_CURRENT_LOCATION_TIMEOUT | Exception Name: GPS Timeout | Description: Failed to obtain GPS position within the specified timeout period (location_timeout).
- Code: OTHER_ERROR | Exception Name: Unexpected Error | Description: An unexpected runtime error occurred during execution. Check logs for details.

# Parameter details

## 1. Input parameter: `location_timeout`

Defines the maximum time (in milliseconds) to wait for valid GPS
updates.

### Example

"location_timeout": 20000

### Details

- If no valid GPS data is received within this period, the task fails.

## 2. Input parameter: `sample_interval`

Defines the interval (in milliseconds) between two GPS samples used for
speed calculation.

### Example

"sample_interval": 1000

### Details

- Lower values provide more precise tracking but increase battery
consumption.
- Recommended range: 500 -- 2000 ms.

## 3. Input parameter: `max_speed_accuracy`

Defines the maximum allowed GPS speed accuracy threshold.

### Example

"max_speed_accuracy": 5.0

### Details

- If the reported GPS accuracy exceeds this threshold, the sample is
ignored.
- Ensures more reliable speed measurements.

# Output details

## 4. Result variable: `speed_value_output`

Stores the calculated speed value in **km/h**.

### Example

"speed_value_output": "$SPEED_KMH"

## 5. Result variable: `distance_output`

Stores the total traveled distance in **meters (m)**.

### Example

"distance_output": "$DISTANCE_M"

## 6. Result variable: `speed_accuracy_used`

Stores the GPS accuracy value (converted/used) associated with the speed
calculation (km/h equivalent context).

### Example

"speed_accuracy_used": "$SPEED_ACCURACY"

### Details

- **Note**: The accuracy value represents the margin of error. For example, if the calculated speed is 50 km/h with an accuracy of 5 km/h, the actual speed is **50 ± 5 km/h** with a probability of approximately **68%**.

## Complete JSON example

{
  "Current Speed": [
    {
      "category": "Current Speed",
      "text": "Current Speed",
      "visible": true,
      "description": "This task will ask phone GPS to get your current speed (Km/h)",
      "key": -1,
      "loc": "-400 40"
    }
  ]
}