# Workflows Introduction

## What is a Workflow?

A **workflow** is a sequence of tasks executed in a specific order on an Android device. It defines the logic, conditions, and flow of automation actions.

### Internal Structure: Graph-Based

Internally, workflows are represented as a **directed graph** with:

- **Nodes**: Individual tasks (Start, End, Normal tasks, Conditions)
- **Edges/Links**: Connections between nodes defining the execution flow
- **Entry Point**: Single START node where execution begins
- **Exit Points**: One or more END nodes where execution terminates

The workflow engine traverses the graph starting from START, follows the links, and executes each node until reaching an END node.

**Example JSON structure:**

```json
{
  "Start": [
    {
      "id": "0",
      "title": "Network Connectivity Test",
      "variables": [
        {
          "variableName": "$network_status",
          "variableValue": "unknown",
          "is_kpi": false
        }
      ]
    }
  ],
  
  "CmdStage": [
    {
      "id": "1",
      "title": "Ping Google DNS",
      "cmd_text": "ping -c 1 8.8.8.8",
      "cmd_result_output": "$PING_RESULT",
      "cmd_error_output": "$PING_ERROR"
    }
  ],
  
  "CompareText": [
    {
      "id": "2",
      "title": "Check if Network Unreachable",
      "text_x": "$PING_ERROR",
      "text_y": "unreachable",
      "compare_type": 2
    }
  ],
  
  "TextReport": [
    {
      "id": "3",
      "title": "Log Network Down",
      "texte": "Network is unreachable: $PING_ERROR"
    },
    {
      "id": "4",
      "title": "Log Network Up",
      "texte": "Network is OK: $PING_RESULT"
    }
  ],
  
  "End": [
    {
      "id": "100",
      "title": "Workflow Complete"
    }
  ],
  
  "Links": [
    {
      "from": "0",
      "to": "1"
    },
    {
      "from": "1",
      "to": "2"
    },
    {
      "from": "2",
      "true": "3",
      "false": "4"
    },
    {
      "from": "3",
      "to": "100"
    },
    {
      "from": "4",
      "to": "100"
    }
  ]
}
```

**Graph visualization:**

```
START (id:0)
    ↓
TextReport (id:1)
    ↓
CompareNumber (id:2)
    ├─→ TRUE → END (id:100)
    └─→ FALSE → TextReport (id:1) [loop back]
```

## Understanding Links (Connections)

The **Links** section defines how nodes are connected and the execution flow:

### Link Types

#### 1. Sequential Link (Normal Task)

Connects one task directly to the next:

```json
{
  "from": "0",
  "to": "1"
}
```

**Meaning**: After node 0 completes, immediately execute node 1.

#### 2. Conditional Link (Decision Node)

Branches execution based on condition result:

```json
{
  "from": "2",
  "true": "100",
  "false": "1"
}
```

**Meaning**:

- If condition in node 2 is TRUE → go to node 100
- If condition in node 2 is FALSE → go to node 1

### Graph Traversal Algorithm

The workflow engine:

1. **Starts** at the START node (id: 0 or similar)
2. **Follows** the "from" → "to" links
3. **Evaluates** conditions and branches (true/false)
4. **Executes** each task at every node visited
5. **Terminates** when reaching an END node

## Complete Workflow Example with Graph Structure

### Scenario: Check temperature and log result

```json
{
  "Start": [
    {
      "id": "0",
      "title": "Initialize",
      "variables": [
        {
          "variableName": "$temperature",
          "variableValue": "25",
          "is_kpi": true
        }
      ]
    }
  ],
  
  "TextReport": [
    {
      "id": "1",
      "title": "Log Temperature",
      "texte": "Current temperature: $temperature°C"
    }
  ],
  
  "CompareNumber": [
    {
      "id": "2",
      "title": "Temperature Check",
      "num_x": "$temperature",
      "num_y": "30",
      "compare_type": 1
    }
  ],
  
  "TextReport": [
    {
      "id": "3",
      "title": "Too Hot Alert",
      "texte": "Temperature exceeds 30°C: $temperature°C"
    },
    {
      "id": "4",
      "title": "Normal Temperature",
      "texte": "Temperature is OK: $temperature°C"
    }
  ],
  
  "End": [
    {
      "id": "100"
    }
  ],
  
  "Links": [
    {
      "from": "0",
      "to": "1"
    },
    {
      "from": "1",
      "to": "2"
    },
    {
      "from": "2",
      "true": "3",
      "false": "4"
    },
    {
      "from": "3",
      "to": "100"
    },
    {
      "from": "4",
      "to": "100"
    }
  ]
}
```

### Graph Flow:

Diagram Nodes:
- TextReport1: TextReport id:1 Log Temperature
- CompareNum: CompareNumber id:2 25 > 30?
- TextReport3: TextReport id:3 Too Hot Alert
- TextReport4: TextReport id:4 Normal Temperature
- End: END id:100

Workflow Flow:
- TextReport id:1 Log Temperature → CompareNumber id:2 25 > 30?
- TextReport id:3 Too Hot Alert → END id:100
- TextReport id:4 Normal Temperature → END id:100

## Workflow Components Summary

- Component: **START Task** | Purpose: Entry point, initializes workflow | Quantity: Exactly 1 | JSON Key: `"Start"` | Example ID: `"0"` | Description: Begins execution.
- Component: **Normal Tasks** | Purpose: Execute sequentially without conditions | Quantity: 0 or more | JSON Key: Task type (CmdStage, Sleep, etc.) | Example ID: `"1", "2"` | Description: Execute one after another in sequence.
- Component: **Conditional Tasks** | Purpose: Branch execution based on conditions | Quantity: 0 or more | JSON Key: CompareNumber, CompareText | Example ID: `"2"` | Description: Evaluate true/false and branch execution.
- Component: **END Task** | Purpose: Exit point, terminates workflow | Quantity: 1 or more | JSON Key: `"End"` | Example ID: `"100"` | Description: Ends execution. Can have multiple endpoints.
- Component: **Links** | Purpose: Define connections between nodes | Quantity: Required | JSON Key: `"Links"` | Example ID: N/A | Description: Maps node IDs with "from", "to", "true", "false"

## Workflow Execution Flow

### Basic Flow (Linear)

Linear execution: START → Task 1 → Task 2 → END

**JSON Example:**

```json
{
  "Start": [{"id": "0"}],
  "CmdStage": [{"id": "1", "cmd_text": "ping -c 1 8.8.8.8"}],
  "Sleep": [{"id": "2", "Time_sleep": 1000}],
  "End": [{"id": "100"}],
  "Links": [
    {"from": "0", "to": "1"},
    {"from": "1", "to": "2"},
    {"from": "2", "to": "100"}
  ]
}
```

**Mermaid Diagram:**

Diagram Nodes:
- Task1: CmdStage id:1 ping
- Task2: Sleep id:2 1000ms
- End: END id:100

Workflow Flow:
- CmdStage id:1 ping → Sleep id:2 1000ms
- Sleep id:2 1000ms → END id:100

### Branching Flow (Conditional)

Branching execution with true/false paths: START → Task 1 → Condition → (TRUE→Task2 | FALSE→Task3) → END

**JSON Example:**

```json
{
  "Start": [{"id": "0"}],
  "CmdStage": [{"id": "1", "cmd_text": "ping -c 1 8.8.8.8", "cmd_error_output": "$ERROR"}],
  "CompareText": [{"id": "2", "text_x": "$ERROR", "text_y": "unreachable", "compare_type": 2}],
  "TextReport": [
    {"id": "3", "texte": "Network down"},
    {"id": "4", "texte": "Network up"}
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
```

**Mermaid Diagram:**

Diagram Nodes:
- Task1: CmdStage id:1 ping
- Condition: CompareText id:2 ERROR contains unreachable?
- Task3: TextReport id:3 Network Down
- Task4: TextReport id:4 Network Up
- End: END id:100

Workflow Flow:
- CmdStage id:1 ping → CompareText id:2 ERROR contains unreachable?
- TextReport id:3 Network Down → END id:100
- TextReport id:4 Network Up → END id:100