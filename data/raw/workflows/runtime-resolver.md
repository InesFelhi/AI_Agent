# Runtime Resolver

## Introduction

The **Runtime Resolver** is the core engine of the Workflow Runtime that processes variables during workflow execution. It manages the lifecycle of variables by registering outputs, resolving parameters, and casting types.

---

## Execution Flow Overview

```mermaid
flowchart TD
    Start["1️⃣ START NODE<br/>Variables declared<br/>Dictionary initialized: {}"] 
    
    Task1["2️⃣ TASK 1 EXECUTES<br/>Produces output<br/>Example: cmd_error_output"]
    
    Register["3️⃣ REGISTRATION<br/>Output stored in dictionary<br/>{$VAR: 'value'}"]
    
    Task2["4️⃣ TASK 2 AWAITS<br/>Has parameters with variables<br/>Example: text_x: '$VAR'"]
    
    Resolve["5️⃣ RESOLUTION<br/>Scan parameters for $variables<br/>Replace with dictionary values"]
    
    Cast["6️⃣ CASTING<br/>Convert String → Target type<br/>String → Double, JSON, etc."]
    
    Execute["7️⃣ TASK 2 EXECUTES<br/>With resolved & casted values"]
    
    End["8️⃣ END NODE<br/>Dictionary persists"]
    
    Start --> Task1
    Task1 --> Register
    Register --> Task2
    Task2 --> Resolve
    Resolve --> Cast
    Cast --> Execute
    Execute --> End
    
    style Start fill:#e3f2fd
    style Task1 fill:#f3e5f5
    style Register fill:#fff9c4
    style Task2 fill:#f3e5f5
    style Resolve fill:#fff9c4
    style Cast fill:#fff9c4
    style Execute fill:#f3e5f5
    style End fill:#c8e6c9
```

---

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

---

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

```mermaid
sequenceDiagram
    participant Task as Task 1<br/>(NtpSync)
    participant Resolver as Runtime<br/>Resolver
    participant Dict as Runtime<br/>Dictionary
    
    Task->>Task: Query NTP server<br/>time.google.com
    Task->>Task: Receive time response
    Task->>Resolver: Output produced<br/>Offset: '125'
    Resolver->>Dict: Register output<br/>$TIME_OFFSET = '125'
    Dict->>Dict: Update dictionary
    Resolver-->>Task: ✅ Output registered
    
    Note over Dict: {<br/>  "$TIME_OFFSET": "125",<br/>  "$LATITUDE": "0.0",<br/>  "$API_RESPONSE": "{}"<br/>}
```

**Dictionary State After Task 1:**
```
{
  "$TIME_OFFSET": "125",
  "$LATITUDE": "0.0",
  "$API_RESPONSE": "{}"
}
```

---

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

```mermaid
flowchart LR
    Scan["1️⃣ SCAN<br/>Find parameters<br/>with variables"] 
    
    Identify["2️⃣ IDENTIFY<br/>num_x: '$TIME_OFFSET'<br/>Contains variable"]
    
    Lookup["3️⃣ LOOKUP<br/>Search dictionary<br/>for $TIME_OFFSET"]
    
    Found["4️⃣ FOUND<br/>Value:<br/>'125'"]
    
    Replace["5️⃣ REPLACE<br/>num_x = <br/>'125'"]
    
    Ready["6️⃣ READY<br/>Parameter resolved<br/>Ready for casting"]
    
    Scan --> Identify
    Identify --> Lookup
    Lookup --> Found
    Found --> Replace
    Replace --> Ready
    
    style Scan fill:#fff9c4
    style Identify fill:#fff9c4
    style Lookup fill:#fff9c4
    style Found fill:#c8e6c9
    style Replace fill:#fff9c4
    style Ready fill:#c8e6c9
```

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

---

## Stage 4: Type Casting

After resolution, values are **cast to the expected parameter type**.

### Casting Types

| From | To | Example | Process |
|------|-----|---------|---------|
| String | String | `"Synchronized"` | No conversion |
| String | Integer | `"125"` | Parse to integer: `125` |
| String | Double | `"25.5"` | Parse to float: `25.5` |
| String | JSON | `'{"status": "ok"}'` | Parse to object: `{status: "ok"}` |
| String | Boolean | `"true"` | Parse to boolean: `true` |

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

```mermaid
flowchart TD
    Before["BEFORE CASTING<br/>num_x = '$TIME_OFFSET'<br/>(String from dictionary)"]
    
    Resolved["AFTER RESOLUTION<br/>num_x = '125'<br/>(Still String type)"]
    
    CheckType["CHECK PARAMETER TYPE<br/>num_x expects: Integer<br/>Current type: String"]
    
    Convert["CONVERT<br/>String '125'<br/>→ Integer 125<br/>(type cast)"]
    
    CastSuccess["CAST SUCCESS<br/>num_x = 125<br/>(Integer type)<br/>Ready for execution"]
    
    CastError["❌ CAST ERROR<br/>Cannot convert 'abc'<br/>to Integer<br/>Execution stops"]
    
    Before --> Resolved
    Resolved --> CheckType
    CheckType --> Convert
    Convert --> CastSuccess
    CheckType -->|Invalid value| CastError
    
    style Before fill:#ffe0e0
    style Resolved fill:#fff9c4
    style CheckType fill:#fff9c4
    style Convert fill:#fff9c4
    style CastSuccess fill:#c8e6c9
    style CastError fill:#ffcdd2
```

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

```mermaid
flowchart TD
    Before["BEFORE CASTING<br/>num_x = '$LATITUDE'<br/>(String from dictionary)"]
    
    Resolved["AFTER RESOLUTION<br/>num_x = '48.8566'<br/>(Still String type)"]
    
    CheckType["CHECK PARAMETER TYPE<br/>num_x expects: Double<br/>Current type: String"]
    
    Convert["CONVERT<br/>String '48.8566'<br/>→ Double 48.8566<br/>(type cast)"]
    
    CastSuccess["CAST SUCCESS<br/>num_x = 48.8566<br/>(Double type)<br/>Ready for execution"]
    
    CastError["❌ CAST ERROR<br/>Cannot convert 'abc'<br/>to Double<br/>Execution stops"]
    
    Before --> Resolved
    Resolved --> CheckType
    CheckType --> Convert
    Convert --> CastSuccess
    CheckType -->|Invalid value| CastError
    
    style Before fill:#ffe0e0
    style Resolved fill:#fff9c4
    style CheckType fill:#fff9c4
    style Convert fill:#fff9c4
    style CastSuccess fill:#c8e6c9
    style CastError fill:#ffcdd2
```

---

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

| Step | Task | Operation | Dictionary State | Notes |
|------|------|-----------|------------------|-------|
| 1 | START (id:0) | Initialize variables | `{"$NTP_RTT": "0", "$TIME_OFFSET": "0"}` | Initial values |
| 2 | NtpSync (id:1) | Query time.google.com | Same | First attempt |
| 3 | NtpSync (id:1) | Response received | Same | RTT=300ms, Offset=125ms |
| 4 | Runtime Resolver | **Register outputs** | `{"$NTP_RTT": "300", "$TIME_OFFSET": "125"}` | ⚠️ **RTT too high** |
| 5 | CompareNumber (id:2) | Await execution | Same | Will check RTT quality |
| 6 | Runtime Resolver | **Resolve $NTP_RTT** | Same | Scan: `num_x: "$NTP_RTT"` |
| 7 | Runtime Resolver | **Replace & cast** | Same | `num_x = "300" → 300` |
| 8 | CompareNumber (id:2) | Execute: 300 < 100 | Same | Result: **FALSE** |
| 9 | Runtime Resolver | **Branch to Task 3** | Same | RTT not acceptable, retry |
| 10 | NtpSync (id:3) | Query pool.ntp.org | Same | **Retry** with different server |
| 11 | NtpSync (id:3) | Response received | Same | RTT=45ms, Offset=98ms |
| 12 | Runtime Resolver | **Register outputs** | `{"$NTP_RTT": "45", "$TIME_OFFSET": "98"}` | ✅ **RTT acceptable** |
| 13 | CompareNumber (id:4) | Await execution | Same | Check RTT again |
| 14 | Runtime Resolver | **Resolve $NTP_RTT** | Same | Lookup: finds '45' |
| 15 | Runtime Resolver | **Replace & cast** | Same | `num_x = "45" → 45` |
| 16 | CompareNumber (id:4) | Execute: 45 < 100 | Same | Result: **TRUE** ✅ |
| 17 | Runtime Resolver | **Branch to Task 5** | Same | RTT acceptable, success |
| 18 | TextReport (id:5) | Await execution | Same | Prepare success message |
| 19 | Runtime Resolver | **Resolve multi-variables** | Same | `$NTP_RTT → '45'`, `$TIME_OFFSET → '98'` |
| 20 | TextReport (id:5) | Display message | Same | "NTP sync OK! RTT: 45 ms, Offset: 98 ms" |
| 21 | END (id:100) | Workflow complete | `{"$NTP_RTT": "45", "$TIME_OFFSET": "98"}` | Final state persists |

### Visual Execution Timeline

**Real-World Example:** Check NTP RTT (Round Trip Time) before accepting offset. If RTT > 100ms, retry synchronization.

```mermaid
sequenceDiagram
    autonumber
    participant Start as 🏁 START
    participant Dict as 📦 Dictionary
    participant NTP1 as ⚙️ NtpSync 1
    participant Resolver as 🔍 Resolver
    participant CmpNum2 as 🔢 Compare 2
    participant NTP3 as 🔄 NtpSync 3
    participant CmpNum4 as 🔢 Compare 4
    participant Report as 📄 Report 5
    participant EndNode as 🎯 END
    
    rect rgb(230, 240, 255)
    Note over Start,Dict: 📋 PHASE 1 - INITIALIZATION
    Start->>Dict: Initialize Variables
    Note over Dict: Dictionary Created
    Note over Dict: {$NTP_RTT: 0, $TIME_OFFSET: 0}
    end
    
    rect rgb(245, 230, 255)
    Note over Dict,NTP1: ⚙️ PHASE 2 - FIRST NTP SYNC
    Dict->>NTP1: Execute Task 1
    NTP1->>NTP1: Query time.google.com
    Note over NTP1: Response RTT: 300ms, Offset: 125ms
    NTP1->>Resolver: Output RTT=300, Offset=125
    Resolver->>Dict: Register Outputs
    Note over Dict: Dictionary Updated
    Note over Dict: {$NTP_RTT: 300, $TIME_OFFSET: 125}
    end
    
    rect rgb(255, 250, 230)
    Note over Dict,CmpNum2: 🔍 PHASE 3 - CHECK RTT QUALITY
    Dict->>CmpNum2: Execute Task 2
    CmpNum2->>Resolver: Resolve param $NTP_RTT
    Resolver->>Dict: Lookup $NTP_RTT
    Dict-->>Resolver: Return 300
    Resolver->>CmpNum2: num_x = 300 (cast to Integer)
    CmpNum2->>CmpNum2: Compare 300 < 100
    Note over CmpNum2: Result FALSE - RTT too high!
    CmpNum2->>Dict: Branch to FALSE path
    end
    
    rect rgb(230, 255, 245)
    Note over Dict,NTP3: 🔄 PHASE 4 - RETRY NTP SYNC
    Dict->>NTP3: Execute Task 3 (Retry)
    NTP3->>NTP3: Query pool.ntp.org
    Note over NTP3: Response RTT: 45ms, Offset: 98ms
    NTP3->>Resolver: Output RTT=45, Offset=98
    Resolver->>Dict: Update Dictionary
    Note over Dict: Dictionary Updated
    Note over Dict: {$NTP_RTT: 45, $TIME_OFFSET: 98}
    end
    
    rect rgb(255, 250, 230)
    Note over Dict,CmpNum4: 🔍 PHASE 5 - RECHECK RTT
    Dict->>CmpNum4: Execute Task 4
    CmpNum4->>Resolver: Resolve param $NTP_RTT
    Resolver->>Dict: Lookup $NTP_RTT
    Dict-->>Resolver: Return 45
    Resolver->>CmpNum4: num_x = 45 (cast to Integer)
    CmpNum4->>CmpNum4: Compare 45 < 100
    Note over CmpNum4: Result TRUE - RTT acceptable!
    CmpNum4->>Dict: Branch to TRUE path
    end
    
    rect rgb(240, 255, 240)
    Note over Dict,Report: 📄 PHASE 6 - SUCCESS REPORT
    Dict->>Report: Execute Task 5
    Report->>Resolver: Resolve $NTP_RTT and $TIME_OFFSET
    Resolver->>Dict: Lookup both variables
    Dict-->>Resolver: $NTP_RTT=45, $TIME_OFFSET=98
    Resolver->>Report: Multi-variable resolved
    Report->>Report: Display message
    Note over Report: NTP sync OK! RTT: 45 ms, Offset: 98 ms
    end
    
    rect rgb(230, 255, 230)
    Note over Report,EndNode: 🎯 PHASE 7 - COMPLETION
    Report->>EndNode: Workflow Complete
    Note over Dict: Final State
    Note over Dict: {$NTP_RTT: 45, $TIME_OFFSET: 98}
    end
```

### Dictionary Lifecycle Through Workflow

This example shows how the dictionary evolves:

| Step | Action | Dictionary State | Notes |
|------|--------|------------------|-------|
| 1 | **START** | `{$NTP_RTT: '0', $TIME_OFFSET: '0'}` | Initial values |
| 2 | **NtpSync #1** executes | Same | First query to time.google.com |
| 3 | **Register outputs** | `{$NTP_RTT: '300', $TIME_OFFSET: '125'}` | ⚠️ RTT too high (300ms) |
| 4 | **CompareNumber #2** resolves | Same | Check if 300 < 100 |
| 5 | **CompareNumber #2** result | Same | FALSE → RTT not acceptable |
| 6 | **Branch to retry** | Same | Follow FALSE path |
| 7 | **NtpSync #3** executes | Same | Retry with pool.ntp.org |
| 8 | **Register outputs** | `{$NTP_RTT: '45', $TIME_OFFSET: '98'}` | ✅ RTT acceptable (45ms) |
| 9 | **CompareNumber #4** resolves | Same | Check if 45 < 100 |
| 10 | **CompareNumber #4** result | Same | TRUE → RTT acceptable |
| 11 | **Branch to success** | Same | Follow TRUE path |
| 12 | **TextReport #5** resolves | Same | Multi-variable resolution |
| 13 | **Display message** | Same | Final report |
| 14 | **END** | `{$NTP_RTT: '45', $TIME_OFFSET: '98'}` | Final state persists |


---

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

```mermaid
flowchart LR
    Text["Text parameter:<br/>'NTP Offset: $TIME_OFFSET ms<br/>Location: Latitude $LATITUDE'"]
    
    Find["FIND variables:<br/>$TIME_OFFSET<br/>$LATITUDE"]
    
    Lookup1["LOOKUP $TIME_OFFSET:<br/>Found: '125'"]
    
    Lookup2["LOOKUP $LATITUDE:<br/>Found: '48.8566'"]
    
    Replace["REPLACE both:<br/>'NTP Offset: 125 ms<br/>Location: Latitude 48.8566'"]
    
    Ready["READY for execution"]
    
    Text --> Find
    Find --> Lookup1
    Find --> Lookup2
    Lookup1 --> Replace
    Lookup2 --> Replace
    Replace --> Ready
    
    style Text fill:#ffe0e0
    style Find fill:#fff9c4
    style Lookup1 fill:#fff9c4
    style Lookup2 fill:#fff9c4
    style Replace fill:#c8e6c9
    style Ready fill:#c8e6c9
```

---

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

```mermaid
flowchart TD
    Scan["SCAN parameter<br/>Find: $UNDEFINED_VAR"]
    
    Lookup["LOOKUP in dictionary<br/>Search: $UNDEFINED_VAR"]
    
    NotFound["NOT FOUND<br/>Variable doesn't exist"]
    
    Error["❌ ERROR<br/>Variable $UNDEFINED_VAR<br/>not found in<br/>runtime dictionary"]
    
    Stop["⛔ STOP EXECUTION<br/>Workflow fails"]
    
    Scan --> Lookup
    Lookup --> NotFound
    NotFound --> Error
    Error --> Stop
    
    style Scan fill:#fff9c4
    style Lookup fill:#fff9c4
    style NotFound fill:#ffcdd2
    style Error fill:#ffcdd2
    style Stop fill:#ffcdd2
```

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

```mermaid
flowchart TD
    Resolve["RESOLVE<br/>num_x = 'abc'"]
    
    CheckType["CHECK TYPE<br/>num_x expects: Double<br/>Current: String"]
    
    TryConvert["TRY CONVERT<br/>'abc' → Double"]
    
    ConvertFail["CONVERSION FAILS<br/>'abc' is not<br/>a valid number"]
    
    Error["❌ ERROR<br/>Cannot cast 'abc'<br/>to Double"]
    
    Stop["⛔ STOP EXECUTION"]
    
    Resolve --> CheckType
    CheckType --> TryConvert
    TryConvert --> ConvertFail
    ConvertFail --> Error
    Error --> Stop
    
    style Resolve fill:#ffe0e0
    style CheckType fill:#fff9c4
    style TryConvert fill:#fff9c4
    style ConvertFail fill:#ffcdd2
    style Error fill:#ffcdd2
    style Stop fill:#ffcdd2
```

---

## Runtime Dictionary State Machine

The runtime dictionary evolves through the workflow lifecycle:

```mermaid
flowchart TD
    Start["🏁 INITIALIZED<br/>━━━━━━━━━━━━━━<br/>START Node<br/>Dictionary = {}<br/>Variables declared<br/>Initial values set"]
    
    Task1Exec["⚙️ TASK 1 EXECUTES<br/>━━━━━━━━━━━━━━<br/>Task runs<br/>Produces output"]
    
    Task1Done["✅ OUTPUT REGISTERED<br/>━━━━━━━━━━━━━━<br/>Dictionary updated<br/>{$VAR1: 'value1'}"]
    
    Task2Ready["⏳ TASK 2 AWAITS<br/>━━━━━━━━━━━━━━<br/>Resolver scans<br/>parameters"]
    
    Task2Resolve["🔍 RESOLVER RESOLVES<br/>━━━━━━━━━━━━━━<br/>Replaces variables<br/>with values"]
    
    Task2Cast["🔄 RESOLVER CASTS<br/>━━━━━━━━━━━━━━<br/>Types converted<br/>as needed"]
    
    Task2Exec["⚙️ TASK 2 EXECUTES<br/>━━━━━━━━━━━━━━<br/>With resolved<br/>values"]
    
    Task2Done["✅ OUTPUT REGISTERED<br/>━━━━━━━━━━━━━━<br/>Dictionary extends"]
    
    Completed["🎯 COMPLETED<br/>━━━━━━━━━━━━━━<br/>Workflow End<br/>Final dictionary<br/>state persists"]
    
    Start --> Task1Exec
    Task1Exec --> Task1Done
    Task1Done --> Task2Ready
    Task2Ready --> Task2Resolve
    Task2Resolve --> Task2Cast
    Task2Cast --> Task2Exec
    Task2Exec --> Task2Done
    Task2Done --> Completed
    
    style Start fill:#e3f2fd,stroke:#1976d2,stroke-width:3px
    style Task1Exec fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style Task1Done fill:#c8e6c9,stroke:#388e3c,stroke-width:3px
    style Task2Ready fill:#fff9c4,stroke:#f57c00,stroke-width:2px
    style Task2Resolve fill:#fff9c4,stroke:#f57c00,stroke-width:2px
    style Task2Cast fill:#fff9c4,stroke:#f57c00,stroke-width:2px
    style Task2Exec fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style Task2Done fill:#c8e6c9,stroke:#388e3c,stroke-width:3px
    style Completed fill:#c8e6c9,stroke:#2e7d32,stroke-width:4px
```

---

## Where to Find Variables in Workflow Runtime

Variables exist in **three key locations** during workflow execution:

```mermaid
flowchart TD
    D1["<b>1️⃣ VARIABLE DECLARATION</b><br/><br/>📍 <b>START Node</b><br/><br/>variables: [<br/>  $TIME_OFFSET = '0'<br/>  $LATITUDE = '0.0'<br/>]<br/><br/>🎯 <b>Purpose:</b><br/>Declare & Initialize"]
    
    D2["<b>2️⃣ RUNTIME DICTIONARY</b><br/><br/>📦 <b>Memory Storage</b><br/><br/>{<br/>  $TIME_OFFSET: '0'<br/>  $LATITUDE: '0.0'<br/>}<br/><br/>🔄 <b>Dynamic Updates</b><br/>During Execution"]
    
    D3A["<b>3️⃣ TASK INPUT</b><br/><br/>📖 <b>Read Variable</b><br/><br/>CompareNumber:<br/>  num_x: $TIME_OFFSET<br/><br/>🎯 <b>Purpose:</b><br/>Use variable value"]
    
    D3B["<b>3️⃣ TASK OUTPUT</b><br/><br/>✏️ <b>Write Variable</b><br/><br/>NtpSync:<br/>  ntp_offset_output:<br/>  $TIME_OFFSET<br/><br/>🎯 <b>Purpose:</b><br/>Store result"]
    
    D1 --> D2
    D2 --> D3A
    D3B --> D2
    
    style D1 fill:#bbdefb,stroke:#1565c0,stroke-width:6px,color:#000
    style D2 fill:#fff59d,stroke:#f57c00,stroke-width:6px,color:#000
    style D3A fill:#ce93d8,stroke:#6a1b9a,stroke-width:6px,color:#000
    style D3B fill:#ffcdd2,stroke:#c62828,stroke-width:6px,color:#000
```

### Variable Lifecycle Example

```mermaid
flowchart LR
    V1["<b>START</b><br/><br/>Declare:<br/><br/>$TIME_OFFSET<br/>=<br/>'0'"]
    
    V2["<b>DICT INIT</b><br/><br/>Store:<br/><br/>{<br/>$TIME_OFFSET:<br/>'0'<br/>}"]
    
    V3["<b>TASK 1</b><br/><b>OUTPUT</b><br/><br/>ntp_offset<br/>_output:<br/><br/>$TIME_OFFSET"]
    
    V4["<b>DICT</b><br/><b>UPDATE</b><br/><br/>{<br/>$TIME_OFFSET:<br/>'125'<br/>}"]
    
    V5["<b>TASK 2</b><br/><b>INPUT</b><br/><br/>num_x:<br/><br/>$TIME_OFFSET"]
    
    V6["<b>RESOLVER</b><br/><br/>Replace:<br/><br/>num_x<br/>=<br/>'125'"]
    
    V7["<b>TASK 2</b><br/><b>EXECUTE</b><br/><br/>Run with:<br/><br/>125"]
    
    V1 --> V2
    V2 --> V3
    V3 --> V4
    V4 --> V5
    V5 --> V6
    V6 --> V7
    
    style V1 fill:#bbdefb,stroke:#1565c0,stroke-width:6px,color:#000
    style V2 fill:#fff59d,stroke:#f57c00,stroke-width:6px,color:#000
    style V3 fill:#ffcdd2,stroke:#c62828,stroke-width:6px,color:#000
    style V4 fill:#fff59d,stroke:#f57c00,stroke-width:6px,color:#000
    style V5 fill:#ce93d8,stroke:#6a1b9a,stroke-width:6px,color:#000
    style V6 fill:#fff59d,stroke:#f57c00,stroke-width:6px,color:#000
    style V7 fill:#a5d6a7,stroke:#2e7d32,stroke-width:6px,color:#000
```

### How to Access Variables in Different Contexts

| Context | How to Find | Example | Purpose |
|---------|-------------|---------|---------|
| **START Node** | Look at `Start[0].variables` array | `{"variableName": "$TIME_OFFSET", "variableValue": "0"}` | Declaration & initialization |
| **Task Output** | Look at task's output parameter fields | `"ntp_offset_output": "$TIME_OFFSET"` | Write task result to variable |
| **Task Input** | Look at task's input parameter fields | `"num_x": "$TIME_OFFSET"` | Read variable value into parameter |
| **Runtime Dictionary** | Internal memory structure (not in JSON) | `{"$TIME_OFFSET": "125"}` | Current variable values |
| **Resolver** | Automatically scans all task parameters | Finds all strings starting with `$` | Resolve variables before execution |

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

---

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


