# Current Speed

## Summary

- **Internal name**: `GetCurrentSpeed`
- **Category**: Location
- **Purpose**: Measure the device's current speed in km/h using two GPS samples separated by a configurable interval.
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
  - Location services must be enabled on the device

## Detailed description

The **GetCurrentSpeed** task calculates the device's movement speed by taking two GPS samples separated by a configurable interval, then computing distance ÷ time.

It is used to:

- Measure real-time speed (km/h)
- Compute traveled distance (meters) over the sample interval
- Filter GPS samples by accuracy threshold
- Attach speed metrics to telemetry or monitoring reports

The task handles:

- configurable GPS timeout (`location_timeout_ms`),
- configurable sampling interval (`sample_interval_ms`),
- maximum allowed GPS accuracy filtering (`max_speed_accuracy_km_h`),
- calculation of speed in km/h and distance in meters (rounded to 3 decimal places).

## Input parameters

- Parameter: `location_timeout_ms` | Type: Integer | Required: No | Possible values: Time in milliseconds | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `10000`
- Parameter: `sample_interval_ms` | Type: Integer | Required: No | Possible values: Time in milliseconds | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `10000`
- Parameter: `max_speed_accuracy_km_h` | Type: Integer | Required: No | Possible values: Accuracy threshold in meters | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `1000`

## Output parameters

- Field: `speed_kmh_output` | Type: Float | Trigger condition: When calculation is successful | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`
- Field: `distance_m_output` | Type: Float | Trigger condition: When calculation is successful | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`
- Field: `accuracy_used_km_h_output` | Type: Float | Trigger condition: When calculation is successful | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`

## Exceptions

- Code: `GPS-ERROR-001` | Description: Failed to obtain GPS position within `location_timeout_ms`.
- Code: `GPS-ERROR-002` | Description: The GPS provider returned a null location.
- Code: `GPS-ERROR-003` | Description: Location services are disabled on the device.
- Code: `GPS-ERROR-004` | Description: The app does not have `ACCESS_FINE_LOCATION` permission.
- Code: `GPS-ERROR-005` | Description: GPS accuracy exceeds `max_speed_accuracy_km_h` threshold.
- Code: `GPS-ERROR-006` | Description: Time delta between the two GPS samples is too small (< 0.2 s) — speed cannot be computed reliably.

## Execution flowchart

Diagram Nodes:
- E3: ❌ GPS-ERROR-003\nDisabled location
- E4: ❌ GPS-ERROR-004\nNo permission
- GetA: 📍 GPS sample A\nPriority: HIGH_ACCURACY\nTimeout: location_timeout_ms
- E1: ❌ GPS-ERROR-001\nGPS timeout
- E2: ❌ GPS-ERROR-002\nNull location
- E5: ❌ GPS-ERROR-005\nAccuracy too low
- StoreA: ⏱️ tA = System.nanoTime\nWait sample_interval_ms
- GetB: 📍 GPS sample B\nPriority: HIGH_ACCURACY\nTimeout: location_timeout_ms
- Calc: 🔢 tB = System.nanoTime\ndistanceM = locA.distanceTo locB\ndeltaSec = tB - tA / 1e9
- E6: ❌ GPS-ERROR-006\nDelta too small
- Speed: speedKmh = distanceM / deltaSec × 3.6\nRound to 3 decimals

Workflow Flow:
- ⏱️ tA = System.nanoTime\nWait sample_interval_ms → 📍 GPS sample B\nPriority: HIGH_ACCURACY\nTimeout: location_timeout_ms
- 🔢 tB = System.nanoTime\ndistanceM = locA.distanceTo locB\ndeltaSec = tB - tA / 1e9 → CheckDelta
- speedKmh = distanceM / deltaSec × 3.6\nRound to 3 decimals → Success
- ❌ GPS-ERROR-001\nGPS timeout → Error
- ❌ GPS-ERROR-002\nNull location → Error
- ❌ GPS-ERROR-003\nDisabled location → Error
- ❌ GPS-ERROR-004\nNo permission → Error
- ❌ GPS-ERROR-005\nAccuracy too low → Error
- ❌ GPS-ERROR-006\nDelta too small → Error

**How it works:**

1. **Check location services**: Throws `GPS-ERROR-003` if GPS is disabled
2. **Permission check**: Throws `GPS-ERROR-004` if `ACCESS_FINE_LOCATION` is not granted
3. **GPS sample A**: Gets first position — throws `GPS-ERROR-001` on timeout, `GPS-ERROR-002` if null, `GPS-ERROR-005` if accuracy exceeds threshold
4. **Record time tA**: Captures `System.nanoTime()` after sample A
5. **Wait**: Sleeps for `sample_interval_ms` milliseconds
6. **GPS sample B**: Same checks as sample A
7. **Record time tB**: Captures `System.nanoTime()` after sample B
8. **Compute delta**: `deltaSec = (tB - tA) / 1e9` — throws `GPS-ERROR-006` if < 0.2 s
9. **Compute speed**: `speedKmh = (distanceM / deltaSec) × 3.6`
10. **Result**: Returns `GetSpeedTaskResult` with `speed_kmh_output`, `distance_m_output`, `accuracy_used_km_h_output` (each rounded to 3 decimal places)

## Input parameter details

### 1. Input parameter: `location_timeout_ms`

Maximum time (in milliseconds) to wait for each GPS sample before throwing `GPS-ERROR-001`.

```json
"location_timeout_ms": 15000
```

- **Default**: `10000` ms
- Applied to both GPS sample A and GPS sample B independently.

### 2. Input parameter: `sample_interval_ms`

Wait time (in milliseconds) between GPS sample A and GPS sample B.

```json
"sample_interval_ms": 5000
```

- **Default**: `10000` ms (10 seconds)
- Longer intervals improve speed accuracy for slow movements.

### 3. Input parameter: `max_speed_accuracy_km_h`

Maximum allowed GPS accuracy (in meters). Samples with accuracy worse than this value are rejected with `GPS-ERROR-005`.

```json
"max_speed_accuracy_km_h": 50
```

- **Default**: `1000` (very permissive — accepts nearly all GPS readings)
- Lower values give more reliable measurements but may cause more `GPS-ERROR-005` errors in poor GPS conditions.

## Output parameter details

### `speed_kmh_output` — Speed in km/h

Stores the calculated speed rounded to 3 decimal places.

```json
"speed_kmh_output": "$SPEED_KMH"
```

### `distance_m_output` — Distance in meters

Stores the distance traveled between the two GPS samples, in meters, rounded to 3 decimal places.

```json
"distance_m_output": "$DISTANCE_M"
```

### `accuracy_used_km_h_output` — GPS accuracy used

Stores the worst GPS accuracy among the two samples (in meters), rounded to 3 decimal places.

```json
"accuracy_used_km_h_output": "$GPS_ACCURACY"
```

## Complete JSON example

```json
{
  "GetCurrentSpeed": [
    {
      "id": "-1",
      "title": "Get Current Speed",
      "location_timeout_ms": 15000,
      "sample_interval_ms": 5000,
      "max_speed_accuracy_km_h": 100,
      "speed_kmh_output": "$SPEED_KMH",
      "distance_m_output": "$DISTANCE_M",
      "accuracy_used_km_h_output": "$GPS_ACCURACY"
    }
  ]
}
```