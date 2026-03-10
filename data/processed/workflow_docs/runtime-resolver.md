# Runtime Resolver

## Introduction

The **Runtime Resolver** is the core engine of the Workflow Runtime that processes variables during workflow execution. It manages the lifecycle of variables by registering outputs, resolving parameters, and casting types.

## Execution Flow Overview

Diagram Nodes:
- Start: 1️⃣ START NODE Variables declared Dictionary initialized: {}
- Task1: 2️⃣ TASK 1 EXECUTES Produces output Example: cmd_error_output
- Register: 3️⃣ REGISTRATION Output stored in dictionary {$VAR: 'value'}
- Task2: 4️⃣ TASK 2 AWAITS Has parameters with variables Example: text_x: '$VAR'
- Resolve: 5️⃣ RESOLUTION Scan parameters for $variables Replace with dictionary values
- Cast: 6️⃣ CASTING Convert String → Target type String → Double, JSON, etc.
- Execute: 7️⃣ TASK 2 EXECUTES With resolved & casted values
- End: 8️⃣ END NODE Dictionary persists

Workflow Flow:
- 1️⃣ START NODE Variables declared Dictionary initialized: {} → 2️⃣ TASK 1 EXECUTES Produces output Example: cmd_error_output
- 2️⃣ TASK 1 EXECUTES Produces output Example: cmd_error_output → 3️⃣ REGISTRATION Output stored in dictionary {$VAR: 'value'}
- 3️⃣ REGISTRATION Output stored in dictionary {$VAR: 'value'} → 4️⃣ TASK 2 AWAITS Has parameters with variables Example: text_x: '$VAR'
- 4️⃣ TASK 2 AWAITS Has parameters with variables Example: text_x: '$VAR' → 5️⃣ RESOLUTION Scan parameters for $variables Replace with dictionary values
- 5️⃣ RESOLUTION Scan parameters for $variables Replace with dictionary values → 6️⃣ CASTING Convert String → Target type String → Double, JSON, etc.
- 6️⃣ CASTING Convert String → Target type String → Double, JSON, etc. → 7️⃣ TASK 2 EXECUTES With resolved & casted values
- 7️⃣ TASK 2 EXECUTES With resolved & casted values → 8️⃣ END NODE Dictionary persists

## Stage 1: Variable Declaration and Dictionary Initialization

At the START node, variables are **declared and the runtime dictionary is initialized**.

```json
{
  "Start": [
    {
      "id": "0",
      "variables": [
        {
          "variableName": "$TIME_OFFSET",
          "variableValue": "0",
          "is_kpi": false
        },
        {
          "variableName": "$LATITUDE",
          "variableValue": "0.0",
          "is_kpi": true
        },
        {
          "variableName": "$API_RESPONSE",
          "variableValue": "{}",
          "is_kpi": false
        }
      ]
    }
  ]
}
```

**Initial Runtime Dictionary:**

```
{
  "$TIME_OFFSET": "0",
  "$LATITUDE": "0.0",
  "$API_RESPONSE": "{}"
}
```

## Stage 2: Task Execution and Output Registration

When a task executes and produces output, the **Runtime Resolver registers** that output in the dictionary.

### Example: NtpSync Task

```json
{
  "NtpSync": [
    {
      "id": "1",
      "ntp_server": "time.google.com",
      "ntp_port": 123,
      "ntp_timeout": 5000,
      "ntp_offset_output": "$TIME_OFFSET"
    }
  ]
}
```

### Execution Timeline

Diagram describing workflow steps.

**Dictionary State After Task 1:**

```
{
  "$TIME_OFFSET": "125",
  "$LATITUDE": "0.0",
  "$API_RESPONSE": "{}"
}
```

## Stage 3: Parameter Resolution

Before Task 2 executes, the **Runtime Resolver scans all parameters** for variables (strings starting with `$`) and replaces them with dictionary values.

### Example: CompareNumber Task

```json
{
  "CompareNumber": [
    {
      "id": "2",
      "num_x": "$TIME_OFFSET",
      "num_y": "200",
      "compare_type": 2
    }
  ]
}
```

### Resolution Process

Diagram Nodes:
- Scan: 1️⃣ SCAN Find parameters with variables
- Identify: 2️⃣ IDENTIFY num_x: '$TIME_OFFSET' Contains variable
- Lookup: 3️⃣ LOOKUP Search dictionary for $TIME_OFFSET
- Found: 4️⃣ FOUND Value: '125'
- Replace: 5️⃣ REPLACE num_x =  '125'
- Ready: 6️⃣ READY Parameter resolved Ready for casting

Workflow Flow:
- 1️⃣ SCAN Find parameters with variables → 2️⃣ IDENTIFY num_x: '$TIME_OFFSET' Contains variable
- 2️⃣ IDENTIFY num_x: '$TIME_OFFSET' Contains variable → 3️⃣ LOOKUP Search dictionary for $TIME_OFFSET
- 3️⃣ LOOKUP Search dictionary for $TIME_OFFSET → 4️⃣ FOUND Value: '125'
- 4️⃣ FOUND Value: '125' → 5️⃣ REPLACE num_x =  '125'
- 5️⃣ REPLACE num_x =  '125' → 6️⃣ READY Parameter resolved Ready for casting

**Before Resolution:**

```json
{
  "num_x": "$TIME_OFFSET",
  "num_y": "200",
  "compare_type": 2
}
```

**Note:** `num_x` contains a variable reference

**After Resolution:**

```json
{
  "num_x": "125",
  "num_y": "200",
  "compare_type": 2
}
```

**Note:** `num_x` now contains the resolved value (still String, casting comes next)

## Stage 4: Type Casting

After resolution, values are **cast to the expected parameter type**.

### Casting Types

- From: String | To: String | Example: `"Synchronized"` | Process: No conversion
- From: String | To: Integer | Example: `"125"` | Process: Parse to integer: `125`
- From: String | To: Double | Example: `"25.5"` | Process: Parse to float: `25.5`
- From: String | To: JSON | Example: `'{"status": "ok"}'` | Process: Parse to object: `{status: "ok"}`
- From: String | To: Boolean | Example: `"true"` | Process: Parse to boolean: `true`

### Casting Example 1: Integer Casting

```json
{
  "CompareNumber": [
    {
      "id": "3",
      "num_x": "$TIME_OFFSET",
      "num_y": "100",
      "compare_type": 1
    }
  ]
}
```

Diagram Nodes:
- Before: BEFORE CASTING num_x = '$TIME_OFFSET' (String from dictionary)
- Resolved: AFTER RESOLUTION num_x = '125' (Still String type)
- CheckType: CHECK PARAMETER TYPE num_x expects: Integer Current type: String
- Convert: CONVERT String '125' → Integer 125 (type cast)
- CastSuccess: CAST SUCCESS num_x = 125 (Integer type) Ready for execution
- CastError: ❌ CAST ERROR Cannot convert 'abc' to Integer Execution stops

Workflow Flow:
- BEFORE CASTING num_x = '$TIME_OFFSET' (String from dictionary) → AFTER RESOLUTION num_x = '125' (Still String type)
- AFTER RESOLUTION num_x = '125' (Still String type) → CHECK PARAMETER TYPE num_x expects: Integer Current type: String
- CHECK PARAMETER TYPE num_x expects: Integer Current type: String → CONVERT String '125' → Integer 125 (type cast)
- CONVERT String '125' → Integer 125 (type cast) → CAST SUCCESS num_x = 125 (Integer type) Ready for execution

### Casting Example 2: Double Casting

```json
{
  "CompareNumber": [
    {
      "id": "4",
      "num_x": "$LATITUDE",
      "num_y": "50.0",
      "compare_type": 1
    }
  ]
}
```

Diagram Nodes:
- Before: BEFORE CASTING num_x = '$LATITUDE' (String from dictionary)
- Resolved: AFTER RESOLUTION num_x = '48.8566' (Still String type)
- CheckType: CHECK PARAMETER TYPE num_x expects: Double Current type: String
- Convert: CONVERT String '48.8566' → Double 48.8566 (type cast)
- CastSuccess: CAST SUCCESS num_x = 48.8566 (Double type) Ready for execution
- CastError: ❌ CAST ERROR Cannot convert 'abc' to Double Execution stops

Workflow Flow:
- BEFORE CASTING num_x = '$LATITUDE' (String from dictionary) → AFTER RESOLUTION num_x = '48.8566' (Still String type)
- AFTER RESOLUTION num_x = '48.8566' (Still String type) → CHECK PARAMETER TYPE num_x expects: Double Current type: String
- CHECK PARAMETER TYPE num_x expects: Double Current type: String → CONVERT String '48.8566' → Double 48.8566 (type cast)
- CONVERT String '48.8566' → Double 48.8566 (type cast) → CAST SUCCESS num_x = 48.8566 (Double type) Ready for execution

## Complete Workflow Execution Example

### Workflow JSON

**Scenario:** Check NTP RTT quality. If RTT > 100ms, retry with different server.

```json
{
  "Start": [
    {
      "id": "0",
      "variables": [
        {"variableName": "$NTP_RTT", "variableValue": "0"},
        {"variableName": "$TIME_OFFSET", "variableValue": "0"}
      ]
    }
  ],
  
  "NtpSync": [
    {
      "id": "1",
      "ntp_server": "time.google.com",
      "ntp_port": 123,
      "ntp_timeout": 5000,
      "ntp_rtt_output": "$NTP_RTT",
      "ntp_offset_output": "$TIME_OFFSET"
    },
    {
      "id": "3",
      "ntp_server": "pool.ntp.org",
      "ntp_port": 123,
      "ntp_timeout": 5000,
      "ntp_rtt_output": "$NTP_RTT",
      "ntp_offset_output": "$TIME_OFFSET"
    }
  ],
  
  "CompareNumber": [
    {
      "id": "2",
      "num_x": "$NTP_RTT",
      "num_y": "100",
      "compare_type": 2
    },
    {
      "id": "4",
      "num_x": "$NTP_RTT",
      "num_y": "100",
      "compare_type": 2
    }
  ],
  
  "TextReport": [
    {
      "id": "5",
      "texte": "NTP sync OK! RTT: $NTP_RTT ms, Offset: $TIME_OFFSET ms"
    },
    {
      "id": "6",
      "texte": "NTP sync failed after retry. RTT: $NTP_RTT ms (too high)"
    }
  ],
  
  "End": [{"id": "100"}],
  
  "Links": [
    {"from": "0", "to": "1"},
    {"from": "1", "to": "2"},
    {"from": "2", "true": "5", "false": "3"},
    {"from": "3", "to": "4"},
    {"from": "4", "true": "5", "false": "6"},
    {"from": "5", "to": "100"},
    {"from": "6", "to": "100"}
  ]
}
```

### Execution Table

- Step: 1 | Task: START (id:0) | Operation: Initialize variables | Dictionary State: `{"$NTP_RTT": "0", "$TIME_OFFSET": "0"}` | Notes: Initial values
- Step: 2 | Task: NtpSync (id:1) | Operation: Query time.google.com | Dictionary State: Same | Notes: First attempt
- Step: 3 | Task: NtpSync (id:1) | Operation: Response received | Dictionary State: Same | Notes: RTT=300ms, Offset=125ms
- Step: 4 | Task: Runtime Resolver | Operation: **Register outputs** | Dictionary State: `{"$NTP_RTT": "300", "$TIME_OFFSET": "125"}` | Notes: ⚠️ **RTT too high**
- Step: 5 | Task: CompareNumber (id:2) | Operation: Await execution | Dictionary State: Same | Notes: Will check RTT quality
- Step: 6 | Task: Runtime Resolver | Operation: **Resolve $NTP_RTT** | Dictionary State: Same | Notes: Scan: `num_x: "$NTP_RTT"`
- Step: 7 | Task: Runtime Resolver | Operation: **Replace & cast** | Dictionary State: Same | Notes: `num_x = "300" → 300`
- Step: 8 | Task: CompareNumber (id:2) | Operation: Execute: 300 < 100 | Dictionary State: Same | Notes: Result: **FALSE**
- Step: 9 | Task: Runtime Resolver | Operation: **Branch to Task 3** | Dictionary State: Same | Notes: RTT not acceptable, retry
- Step: 10 | Task: NtpSync (id:3) | Operation: Query pool.ntp.org | Dictionary State: Same | Notes: **Retry** with different server
- Step: 11 | Task: NtpSync (id:3) | Operation: Response received | Dictionary State: Same | Notes: RTT=45ms, Offset=98ms
- Step: 12 | Task: Runtime Resolver | Operation: **Register outputs** | Dictionary State: `{"$NTP_RTT": "45", "$TIME_OFFSET": "98"}` | Notes: ✅ **RTT acceptable**
- Step: 13 | Task: CompareNumber (id:4) | Operation: Await execution | Dictionary State: Same | Notes: Check RTT again
- Step: 14 | Task: Runtime Resolver | Operation: **Resolve $NTP_RTT** | Dictionary State: Same | Notes: Lookup: finds '45'
- Step: 15 | Task: Runtime Resolver | Operation: **Replace & cast** | Dictionary State: Same | Notes: `num_x = "45" → 45`
- Step: 16 | Task: CompareNumber (id:4) | Operation: Execute: 45 < 100 | Dictionary State: Same | Notes: Result: **TRUE** ✅
- Step: 17 | Task: Runtime Resolver | Operation: **Branch to Task 5** | Dictionary State: Same | Notes: RTT acceptable, success
- Step: 18 | Task: TextReport (id:5) | Operation: Await execution | Dictionary State: Same | Notes: Prepare success message
- Step: 19 | Task: Runtime Resolver | Operation: **Resolve multi-variables** | Dictionary State: Same | Notes: `$NTP_RTT → '45'`, `$TIME_OFFSET → '98'`
- Step: 20 | Task: TextReport (id:5) | Operation: Display message | Dictionary State: Same | Notes: "NTP sync OK! RTT: 45 ms, Offset: 98 ms"
- Step: 21 | Task: END (id:100) | Operation: Workflow complete | Dictionary State: `{"$NTP_RTT": "45", "$TIME_OFFSET": "98"}` | Notes: Final state persists

### Visual Execution Timeline

**Real-World Example:** Check NTP RTT (Round Trip Time) before accepting offset. If RTT > 100ms, retry synchronization.

Diagram describing workflow steps.

### Dictionary Lifecycle Through Workflow

This example shows how the dictionary evolves:

- Step: 1 | Action: **START** | Dictionary State: `{$NTP_RTT: '0', $TIME_OFFSET: '0'}` | Notes: Initial values
- Step: 2 | Action: **NtpSync #1** executes | Dictionary State: Same | Notes: First query to time.google.com
- Step: 3 | Action: **Register outputs** | Dictionary State: `{$NTP_RTT: '300', $TIME_OFFSET: '125'}` | Notes: ⚠️ RTT too high (300ms)
- Step: 4 | Action: **CompareNumber #2** resolves | Dictionary State: Same | Notes: Check if 300 < 100
- Step: 5 | Action: **CompareNumber #2** result | Dictionary State: Same | Notes: FALSE → RTT not acceptable
- Step: 6 | Action: **Branch to retry** | Dictionary State: Same | Notes: Follow FALSE path
- Step: 7 | Action: **NtpSync #3** executes | Dictionary State: Same | Notes: Retry with pool.ntp.org
- Step: 8 | Action: **Register outputs** | Dictionary State: `{$NTP_RTT: '45', $TIME_OFFSET: '98'}` | Notes: ✅ RTT acceptable (45ms)
- Step: 9 | Action: **CompareNumber #4** resolves | Dictionary State: Same | Notes: Check if 45 < 100
- Step: 10 | Action: **CompareNumber #4** result | Dictionary State: Same | Notes: TRUE → RTT acceptable
- Step: 11 | Action: **Branch to success** | Dictionary State: Same | Notes: Follow TRUE path
- Step: 12 | Action: **TextReport #5** resolves | Dictionary State: Same | Notes: Multi-variable resolution
- Step: 13 | Action: **Display message** | Dictionary State: Same | Notes: Final report
- Step: 14 | Action: **END** | Dictionary State: `{$NTP_RTT: '45', $TIME_OFFSET: '98'}` | Notes: Final state persists

## Multi-Variable Resolution

A parameter can contain **multiple variables** that all need resolution:

```json
{
  "TextReport": [
    {
      "id": "5",
      "texte": "NTP Offset: $TIME_OFFSET ms | Location: Latitude $LATITUDE"
    }
  ]
}
```

### Resolution Steps

Diagram Nodes:
- Text: Text parameter: 'NTP Offset: $TIME_OFFSET ms Location: Latitude $LATITUDE'
- Find: FIND variables: $TIME_OFFSET $LATITUDE
- Lookup1: LOOKUP $TIME_OFFSET: Found: '125'
- Lookup2: LOOKUP $LATITUDE: Found: '48.8566'
- Replace: REPLACE both: 'NTP Offset: 125 ms Location: Latitude 48.8566'
- Ready: READY for execution

Workflow Flow:
- Text parameter: 'NTP Offset: $TIME_OFFSET ms Location: Latitude $LATITUDE' → FIND variables: $TIME_OFFSET $LATITUDE
- FIND variables: $TIME_OFFSET $LATITUDE → LOOKUP $TIME_OFFSET: Found: '125'
- FIND variables: $TIME_OFFSET $LATITUDE → LOOKUP $LATITUDE: Found: '48.8566'
- LOOKUP $TIME_OFFSET: Found: '125' → REPLACE both: 'NTP Offset: 125 ms Location: Latitude 48.8566'
- LOOKUP $LATITUDE: Found: '48.8566' → REPLACE both: 'NTP Offset: 125 ms Location: Latitude 48.8566'
- REPLACE both: 'NTP Offset: 125 ms Location: Latitude 48.8566' → READY for execution

## Error Scenarios

### Scenario 1: Undefined Variable

```json
{
  "CompareText": [
    {
      "id": "2",
      "text_x": "$UNDEFINED_VAR",
      "text_y": "test"
    }
  ]
}
```

Diagram Nodes:
- Scan: SCAN parameter Find: $UNDEFINED_VAR
- Lookup: LOOKUP in dictionary Search: $UNDEFINED_VAR
- NotFound: NOT FOUND Variable doesn't exist
- Error: ❌ ERROR Variable $UNDEFINED_VAR not found in runtime dictionary
- Stop: ⛔ STOP EXECUTION Workflow fails

Workflow Flow:
- SCAN parameter Find: $UNDEFINED_VAR → LOOKUP in dictionary Search: $UNDEFINED_VAR
- LOOKUP in dictionary Search: $UNDEFINED_VAR → NOT FOUND Variable doesn't exist
- NOT FOUND Variable doesn't exist → ❌ ERROR Variable $UNDEFINED_VAR not found in runtime dictionary
- ❌ ERROR Variable $UNDEFINED_VAR not found in runtime dictionary → ⛔ STOP EXECUTION Workflow fails

### Scenario 2: Type Casting Error

```json
{
  "CompareNumber": [
    {
      "id": "2",
      "num_x": "$TEXT_VALUE",
      "num_y": "50.0"
    }
  ]
}
```

Dictionary: `{"$TEXT_VALUE": "abc"}` (not a valid number)

Diagram Nodes:
- Resolve: RESOLVE num_x = 'abc'
- CheckType: CHECK TYPE num_x expects: Double Current: String
- TryConvert: TRY CONVERT 'abc' → Double
- ConvertFail: CONVERSION FAILS 'abc' is not a valid number
- Error: ❌ ERROR Cannot cast 'abc' to Double
- Stop: ⛔ STOP EXECUTION

Workflow Flow:
- RESOLVE num_x = 'abc' → CHECK TYPE num_x expects: Double Current: String
- CHECK TYPE num_x expects: Double Current: String → TRY CONVERT 'abc' → Double
- TRY CONVERT 'abc' → Double → CONVERSION FAILS 'abc' is not a valid number
- CONVERSION FAILS 'abc' is not a valid number → ❌ ERROR Cannot cast 'abc' to Double
- ❌ ERROR Cannot cast 'abc' to Double → ⛔ STOP EXECUTION

## Runtime Dictionary State Machine

The runtime dictionary evolves through the workflow lifecycle:

Diagram Nodes:
- Start: 🏁 INITIALIZED ━━━━━━━━━━━━━━ START Node Dictionary = {} Variables declared Initial values set
- Task1Exec: ⚙️ TASK 1 EXECUTES ━━━━━━━━━━━━━━ Task runs Produces output
- Task1Done: ✅ OUTPUT REGISTERED ━━━━━━━━━━━━━━ Dictionary updated {$VAR1: 'value1'}
- Task2Ready: ⏳ TASK 2 AWAITS ━━━━━━━━━━━━━━ Resolver scans parameters
- Task2Resolve: 🔍 RESOLVER RESOLVES ━━━━━━━━━━━━━━ Replaces variables with values
- Task2Cast: 🔄 RESOLVER CASTS ━━━━━━━━━━━━━━ Types converted as needed
- Task2Exec: ⚙️ TASK 2 EXECUTES ━━━━━━━━━━━━━━ With resolved values
- Task2Done: ✅ OUTPUT REGISTERED ━━━━━━━━━━━━━━ Dictionary extends
- Completed: 🎯 COMPLETED ━━━━━━━━━━━━━━ Workflow End Final dictionary state persists

Workflow Flow:
- 🏁 INITIALIZED ━━━━━━━━━━━━━━ START Node Dictionary = {} Variables declared Initial values set → ⚙️ TASK 1 EXECUTES ━━━━━━━━━━━━━━ Task runs Produces output
- ⚙️ TASK 1 EXECUTES ━━━━━━━━━━━━━━ Task runs Produces output → ✅ OUTPUT REGISTERED ━━━━━━━━━━━━━━ Dictionary updated {$VAR1: 'value1'}
- ✅ OUTPUT REGISTERED ━━━━━━━━━━━━━━ Dictionary updated {$VAR1: 'value1'} → ⏳ TASK 2 AWAITS ━━━━━━━━━━━━━━ Resolver scans parameters
- ⏳ TASK 2 AWAITS ━━━━━━━━━━━━━━ Resolver scans parameters → 🔍 RESOLVER RESOLVES ━━━━━━━━━━━━━━ Replaces variables with values
- 🔍 RESOLVER RESOLVES ━━━━━━━━━━━━━━ Replaces variables with values → 🔄 RESOLVER CASTS ━━━━━━━━━━━━━━ Types converted as needed
- 🔄 RESOLVER CASTS ━━━━━━━━━━━━━━ Types converted as needed → ⚙️ TASK 2 EXECUTES ━━━━━━━━━━━━━━ With resolved values
- ⚙️ TASK 2 EXECUTES ━━━━━━━━━━━━━━ With resolved values → ✅ OUTPUT REGISTERED ━━━━━━━━━━━━━━ Dictionary extends
- ✅ OUTPUT REGISTERED ━━━━━━━━━━━━━━ Dictionary extends → 🎯 COMPLETED ━━━━━━━━━━━━━━ Workflow End Final dictionary state persists

## Where to Find Variables in Workflow Runtime

Variables exist in **three key locations** during workflow execution:

Diagram Nodes:
- D1: <b>1️⃣ VARIABLE DECLARATION</b>  📍 <b>START Node</b>  variables: [   $TIME_OFFSET = '0'   $LATITUDE = '0.0'
- D2: <b>2️⃣ RUNTIME DICTIONARY</b>  📦 <b>Memory Storage</b>  {   $TIME_OFFSET: '0'   $LATITUDE: '0.0' }  🔄 <b>Dynamic Updates</b> During Execution
- D3A: <b>3️⃣ TASK INPUT</b>  📖 <b>Read Variable</b>  CompareNumber:   num_x: $TIME_OFFSET  🎯 <b>Purpose:</b> Use variable value
- D3B: <b>3️⃣ TASK OUTPUT</b>  ✏️ <b>Write Variable</b>  NtpSync:   ntp_offset_output:   $TIME_OFFSET  🎯 <b>Purpose:</b> Store result

Workflow Flow:
- <b>1️⃣ VARIABLE DECLARATION</b>  📍 <b>START Node</b>  variables: [   $TIME_OFFSET = '0'   $LATITUDE = '0.0' → <b>2️⃣ RUNTIME DICTIONARY</b>  📦 <b>Memory Storage</b>  {   $TIME_OFFSET: '0'   $LATITUDE: '0.0' }  🔄 <b>Dynamic Updates</b> During Execution
- <b>2️⃣ RUNTIME DICTIONARY</b>  📦 <b>Memory Storage</b>  {   $TIME_OFFSET: '0'   $LATITUDE: '0.0' }  🔄 <b>Dynamic Updates</b> During Execution → <b>3️⃣ TASK INPUT</b>  📖 <b>Read Variable</b>  CompareNumber:   num_x: $TIME_OFFSET  🎯 <b>Purpose:</b> Use variable value
- <b>3️⃣ TASK OUTPUT</b>  ✏️ <b>Write Variable</b>  NtpSync:   ntp_offset_output:   $TIME_OFFSET  🎯 <b>Purpose:</b> Store result → <b>2️⃣ RUNTIME DICTIONARY</b>  📦 <b>Memory Storage</b>  {   $TIME_OFFSET: '0'   $LATITUDE: '0.0' }  🔄 <b>Dynamic Updates</b> During Execution

### Variable Lifecycle Example

Diagram Nodes:
- V1: <b>START</b>  Declare:  $TIME_OFFSET = '0'
- V2: <b>DICT INIT</b>  Store:  { $TIME_OFFSET: '0' }
- V3: <b>TASK 1</b> <b>OUTPUT</b>  ntp_offset _output:  $TIME_OFFSET
- V4: <b>DICT</b> <b>UPDATE</b>  { $TIME_OFFSET: '125' }
- V5: <b>TASK 2</b> <b>INPUT</b>  num_x:  $TIME_OFFSET
- V6: <b>RESOLVER</b>  Replace:  num_x = '125'
- V7: <b>TASK 2</b> <b>EXECUTE</b>  Run with:  125

Workflow Flow:
- <b>START</b>  Declare:  $TIME_OFFSET = '0' → <b>DICT INIT</b>  Store:  { $TIME_OFFSET: '0' }
- <b>DICT INIT</b>  Store:  { $TIME_OFFSET: '0' } → <b>TASK 1</b> <b>OUTPUT</b>  ntp_offset _output:  $TIME_OFFSET
- <b>TASK 1</b> <b>OUTPUT</b>  ntp_offset _output:  $TIME_OFFSET → <b>DICT</b> <b>UPDATE</b>  { $TIME_OFFSET: '125' }
- <b>DICT</b> <b>UPDATE</b>  { $TIME_OFFSET: '125' } → <b>TASK 2</b> <b>INPUT</b>  num_x:  $TIME_OFFSET
- <b>TASK 2</b> <b>INPUT</b>  num_x:  $TIME_OFFSET → <b>RESOLVER</b>  Replace:  num_x = '125'
- <b>RESOLVER</b>  Replace:  num_x = '125' → <b>TASK 2</b> <b>EXECUTE</b>  Run with:  125

### How to Access Variables in Different Contexts

- Context: **START Node** | How to Find: Look at `Start[0].variables` array | Example: `{"variableName": "$TIME_OFFSET", "variableValue": "0"}` | Purpose: Declaration & initialization
- Context: **Task Output** | How to Find: Look at task's output parameter fields | Example: `"ntp_offset_output": "$TIME_OFFSET"` | Purpose: Write task result to variable
- Context: **Task Input** | How to Find: Look at task's input parameter fields | Example: `"num_x": "$TIME_OFFSET"` | Purpose: Read variable value into parameter
- Context: **Runtime Dictionary** | How to Find: Internal memory structure (not in JSON) | Example: `{"$TIME_OFFSET": "125"}` | Purpose: Current variable values
- Context: **Resolver** | How to Find: Automatically scans all task parameters | Example: Finds all strings starting with `$` | Purpose: Resolve variables before execution

### Quick Reference: Variable Syntax

```json
{
  "Comment": "✅ CORRECT - Variables start with $",
  "Examples": {
    "declaration": {"variableName": "$MY_VAR", "variableValue": "initial"},
    "output": {"cmd_error_output": "$MY_VAR"},
    "input": {"text_x": "$MY_VAR"},
    "multi_var": {"texte": "Error: $VAR1, Code: $VAR2"}
  }
}
```

```json
{
  "Comment": "❌ INCORRECT - Common mistakes",
  "Mistakes": {
    "no_dollar": {"variableName": "MY_VAR"},
    "wrong_case": {"variableName": "$my_var"},
    "undefined": {"text_x": "$UNDEFINED_VAR"}
  }
}
```

## Best Practices for Runtime Resolution

### 1. Declare Variables Early

Always declare all variables in START node:

**✅ Good: All variables declared upfront**

```json
{
  "Start": [{"id": "0", "variables": [...]}]
}
```

**❌ Bad: Missing variable declarations**

```json
{
  "CmdStage": [{"id": "1", "cmd_error_output": "$UNDEFINED"}]
}
```

### 2. Use Descriptive Variable Names

**✅ Good: Clear purpose**

```json
{
  "ntp_status_output": "$NTP_STATUS",
  "ntp_offset_output": "$TIME_OFFSET"
}
```

**❌ Bad: Generic names**

```json
{
  "ntp_status_output": "$x",
  "ntp_offset_output": "$var1"
}
```

### 3. Initialize with Correct Types

**✅ Good: Type-appropriate defaults**

```json
[
  {"variableName": "$ERROR_MSG", "variableValue": ""},
  {"variableName": "$LATITUDE", "variableValue": "0.0"},
  {"variableName": "$DATA", "variableValue": "{}"}
]
```

**❌ Bad: Mismatched types**

```json
{
  "variableName": "$LATITUDE",
  "variableValue": "unknown"
}
```

### 4. Verify Type Compatibility

Ensure parameter types match expected casts:

**✅ Good: Compatible types**

- `"num_x": "$TIME_OFFSET"` - String stored, cast to Integer
- `"num_x": "$LATITUDE"` - String stored, cast to Double
- `"texte": "$ERROR_MSG"` - String stays String

**❌ Bad: Type mismatch**

- `"num_x": "$TEXT_VALUE"` - Contains "abc", cannot cast to Integer