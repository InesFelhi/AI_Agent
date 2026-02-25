# Variables in Workflows

## Introduction to Variables

Variables are **named containers** that store data produced by tasks and can be used by subsequent tasks. They enable data flow and communication between different stages of a workflow.

## Variable Declaration and Roles

Variables must be **declared in the START node** with these characteristics:

- **Naming**: Must start with '$' (mandatory prefix)
- **Scope**: Available throughout the entire workflow
  - 'String' - Text values
  - 'Double' - Decimal numbers
  - 'JSON' - Complex structured data
- **Types Supported**:

**Example: Variable Declaration in START Node**

{
  "Start": [
    {
      "id": "0",
      "variables": [
        {
          "variableName": "$PING_ERROR",
          "variableValue": "",
          "is_kpi": false
        },
        {
          "variableName": "$NETWORK_STATUS",
          "variableValue": "unknown",
          "is_kpi": false
        },
        {
          "variableName": "$TEMPERATURE",
          "variableValue": "0.0",
          "is_kpi": true
        }
      ]
    }
  ]
}

## Task Output Registration

Task outputs can be **registered into variables** declared in START for reuse in other tasks:

{
  "CmdStage": [
    {
      "id": "1",
      "cmd_text": "ping -c 1 8.8.8.8",
      "cmd_error_output": "$PING_ERROR"
    }
  ]
}

**How it works:**

1. Declare variable '$PING_ERROR' in START node
2. Task CmdStage (id:1) executes ping command
3. Error output is automatically stored in '$PING_ERROR'
4. Variable becomes available for subsequent tasks

## Variable Usage in Other Tasks

Once a variable is populated by a task output, it can be used in subsequent tasks:

{
  "CompareText": [
    {
      "id": "2",
      "text_x": "$PING_ERROR",
      "text_y": "unreachable",
      "compare_type": 2
    }
  ]
}

**Variable references:**

- Use the variable name with '$' prefix: '$PING_ERROR'
- Can be used in any parameter that accepts variable values
- Variable persists until workflow ends

## Variable Types and Examples

- Type: **String** | Example: `"$ERROR_MSG"` | Declaration: `"variableValue": ""` | Task Output: `cmd_error_output` | Usage: CompareText, TextReport
- Type: **Double** | Example: `"$TEMPERATURE"` | Declaration: `"variableValue": "0.0"` | Task Output: `ntp_offset_output` | Usage: CompareNumber
- Type: **JSON** | Example: `"$RESPONSE_DATA"` | Declaration: `"variableValue": "{}"` | Task Output: `http_response_output` | Usage: Parse, extract

### String Variables

Store text data produced by commands or APIs:

"variableName": "$ERROR_MESSAGE",
"variableValue": ""

Usage: Error messages, command outputs, API responses

### Double Variables

Store decimal numbers for arithmetic operations and comparisons:

"variableName": "$TEMPERATURE",
"variableValue": "0.0"

Usage: Temperature values, sensor readings, metrics

### JSON Variables

Store complex structured data for detailed processing:

"variableName": "$API_RESPONSE",
"variableValue": "{}"

Usage: API responses, data arrays, nested objects

## Complete Workflow Example with Variables

{
  "Start": [
    {
      "id": "0",
      "variables": [
        {
          "variableName": "$PING_ERROR",
          "variableValue": "",
          "is_kpi": false
        },
        {
          "variableName": "$NETWORK_STATUS",
          "variableValue": "unknown",
          "is_kpi": false
        },
        {
          "variableName": "$RESPONSE_TIME",
          "variableValue": "0.0",
          "is_kpi": true
        }
      ]
    }
  ],
  
  "CmdStage": [
    {
      "id": "1",
      "cmd_text": "ping -c 1 8.8.8.8",
      "cmd_error_output": "$PING_ERROR"
    }
  ],
  
  "CompareText": [
    {
      "id": "2",
      "text_x": "$PING_ERROR",
      "text_y": "unreachable",
      "compare_type": 2
    }
  ],
  
  "TextReport": [
    {
      "id": "3",
      "texte": "Network unreachable: $PING_ERROR"
    },
    {
      "id": "4",
      "texte": "Network available - Status: $NETWORK_STATUS"
    }
  ],
  
  "End": [{"id": "100"}],
  
  "Links": [
    {"from": "0", "to": "1"},
    {"from": "1", "to": "2"},
    {"from": "2", "true": "3", "false": "4"},
    {"from": "3", "to": "100"},
    {"from": "4", "to": "100"}
  ]
}

## Variable Data Flow

flowchart LR
    Start["START<br/>Declare Variables<br/>$PING_ERROR<br/>$NETWORK_STATUS<br/>$RESPONSE_TIME"] -->|"Register output"| Task1["CmdStage<br/>ping -c 1 8.8.8.8<br/>→ $PING_ERROR"]
    Task1 -->|"Use variable"| Task2["CompareText<br/>$PING_ERROR contains<br/>unreachable?"]
    Task2 -->|"TRUE: Use variable"| Task3["TextReport<br/>Display $PING_ERROR"]
    Task2 -->|"FALSE: Use variable"| Task4["TextReport<br/>Display $NETWORK_STATUS"]
    Task3 --> End["END"]
    Task4 --> End
    
    style Start fill:#e3f2fd
    style Task1 fill:#f3e5f5
    style Task2 fill:#fff9c4
    style Task3 fill:#ffe0e0
    style Task4 fill:#e0f0e0
    style End fill:#c8e6c9

## Best Practices

### 1. Declare All Variables in START

Declare variables upfront in the START node:

{
  "Start": [
    {
      "id": "0",
      "variables": [
        {"variableName": "$VAR1", "variableValue": ""},
        {"variableName": "$VAR2", "variableValue": "0.0"}
      ]
    }
  ]
}

### 2. Use Descriptive Variable Names

"$PING_ERROR"      // Good: Clear purpose
"$NETWORK_STATUS"  // Good: Descriptive

"$x"               // Bad: Not descriptive
"$var1"            // Bad: Generic name

### 3. Initialize with Appropriate Defaults

"$ERROR_MSG": ""           // String: empty string
"$TEMPERATURE": "0.0"      // Double: zero value
"$RESPONSE": "{}"          // JSON: empty object

### 4. Use Variables for Data Continuity

Pass data between tasks using variables instead of hardcoding values:

// ✅ Good: Use variable
"text_x": "$PING_ERROR"

// ❌ Bad: Hardcoded value
"text_x": "Network unreachable"

## Variable Lifecycle

1. **Declaration** - Variable declared in START node
2. **Initialization** - Given initial value (usually empty/zero)
3. **Population** - Task output registers value in variable
4. **Usage** - Subsequent tasks reference the variable
5. **Persistence** - Value persists until workflow ends

## Common Use Cases

### Case 1: Error Handling

{
  "CmdStage": [{"id": "1", "cmd_error_output": "$ERROR"}],
  "CompareText": [
    {"id": "2", "text_x": "$ERROR", "text_y": "failed"}
  ]
}

### Case 2: Conditional Branching

{
  "CmdStage": [{"id": "1", "cmd_result_output": "$RESULT"}],
  "CompareNumber": [
    {"id": "2", "num_x": "$RESULT", "num_y": "100"}
  ]
}

### Case 3: Data Passing

{
  "HttpRequest": [{"id": "1", "response_output": "$API_DATA"}],
  "TextReport": [
    {"id": "2", "texte": "Response: $API_DATA"}
  ]
}