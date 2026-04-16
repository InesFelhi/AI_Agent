# Java Code

## Summary

- **Internal name**: `JavaCode`
- **Category**: System
- **Purpose**: Execute inline Java code using a BeanShell scripting interpreter directly on the Android device.
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
  - None

## Detailed description

The **Java Code** task executes inline Java code at runtime using **BeanShell** — a lightweight Java scripting engine that supports standard Java syntax. Code runs directly on the Android device inside the AndroMate process.

It is used to:

- Perform custom computations not available through built-in tasks
- Manipulate strings, numbers, and data structures
- Implement conditional logic or loops inside a single task
- Process results from previous tasks before passing them further
- Debug and inspect values during workflow development

The task handles:

- injecting workflow variables into the BeanShell interpreter scope via **Set Variable** entries,
- executing Java code blocks via **Code** entries,
- intercepting `System.out.println()` and forwarding output to the **AndroMate execution console**,
- intercepting `System.err.println()` and forwarding it as an error message in the console,
- stripping `//` and `/* */` comments before execution,
- splitting code into balanced brace blocks and evaluating them sequentially.

**Note:** `System.out.println("...")` messages written inside your BeanShell code are captured and displayed in the AndroMate execution console in real time. This is useful for debugging variable values or tracing execution flow.

## How BeanShell works

BeanShell is a **Java-compatible scripting engine**. It supports:

- Standard Java syntax (variables, loops, conditionals, method calls)
- Java standard library classes (`String`, `Math`, `Integer`, `ArrayList`, etc.)
- Dynamic typing (no need to declare variable types explicitly)
- Multi-line code with balanced braces `{ }`

**Important limitations:**

- No access to Android APIs (e.g., `Context`, `Activity`)
- No file system or network access from within the script
- Each `JavaCode` task runs in its own interpreter scope — variables do not persist between separate `JavaCode` tasks

## Entry types

The `javaCodeEntries` array defines a sequence of operations executed in order. There are two entry types:

### Entry type 1 — `Set Variable`

Injects a value into the BeanShell interpreter scope so it can be used inside subsequent `Code` entries.

- Field: `type` | Type: String | Required: Yes | Description: Must be `"Set Variable"`
- Field: `variableName` | Type: String | Required: Yes | Description: Name of the variable in the BeanShell scope
- Field: `value` | Type: String | Required: Yes | Description: Value to inject — can be a `$workflow_variable` reference

**Type resolution:** The value string is automatically parsed to the most specific numeric type (Integer → Long → Float → String).

### Entry type 2 — `Code`

Executes a BeanShell Java code block.

- Field: `type` | Type: String | Required: Yes | Description: Must be `"Code"`
- Field: `code` | Type: String | Required: Yes | Description: The BeanShell Java code to execute

## Input parameters

- Parameter: `javaCodeEntries` | Type: Array | Required: Yes | Possible values: Ordered array of `"Set Variable"` and/or `"Code"` entry objects — see Entry types section | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `[]`

## Output parameters

This task produces **no output variables**. It returns `VoidResult`.

- Field: — | Type: VoidResult | Trigger condition: Always | Default: —

To pass values out of BeanShell into the workflow, use a **Set Variable** entry to inject a workflow variable into the BeanShell scope, modify it inside a **Code** entry, then use a `SetVariable` task afterward to write it back. BeanShell variables do not automatically update workflow context variables.

## Exceptions

- Code: `JAVA-CODE-ERROR-001` | Exception Name: Unsupported Variable Type | Description: The value provided in a `Set Variable` entry cannot be mapped to a supported type (int, long, float, String).
- Code: `JAVA-CODE-ERROR-003` | Exception Name: Missing Variable Name or Value | Description: A `Set Variable` entry is missing the `variableName` or `value` field.
- Code: `JAVA-CODE-ERROR-004` | Exception Name: Missing Code Field | Description: A `Code` entry is missing the `code` field.
- Code: `JAVA-CODE-ERROR-005` | Exception Name: Malformed JSON Entry | Description: One of the entries in `javaCodeEntries` contains malformed JSON.
- Code: `JAVA-CODE-ERROR-006` | Exception Name: Unsupported Entry Type | Description: An entry has an unknown `type` value — only `"Code"` and `"Set Variable"` are supported.
- Code: `JAVA-CODE-ERROR-007` | Exception Name: BeanShell Eval Error | Description: The BeanShell interpreter failed to evaluate the code — syntax error, undefined variable, or runtime exception inside the script.
- Code: `ERROR-000` | Exception Name: Other Error | Description: An unexpected runtime error occurred during execution.

## Execution flowchart

Diagram Nodes:
- ReadEntries: 📋 Read javaCodeEntries array
- E3: ❌ JAVA-CODE-ERROR-003
- ParseType: 🔄 Auto-parse value\nInt → Long → Float → String
- InjectVar: 💉 Inject variable\ninto BeanShell scope
- E4: ❌ JAVA-CODE-ERROR-004
- StripComments: ✂️ Strip // and /* */ comments
- SplitBlocks: 📦 Split into\nbalanced brace blocks
- Eval: ⚙️ BeanShell eval\neach block
- E7: ❌ JAVA-CODE-ERROR-007
- Console: 📋 System.out → AndroMate Console
- ConsoleErr: ⚠️ System.err → AndroMate Console
- E6: ❌ JAVA-CODE-ERROR-006

Workflow Flow:
- 📋 Read javaCodeEntries array → Loop
- Loop → CheckType
- 🔄 Auto-parse value\nInt → Long → Float → String → 💉 Inject variable\ninto BeanShell scope
- 💉 Inject variable\ninto BeanShell scope → Loop
- ✂️ Strip // and /* */ comments → 📦 Split into\nbalanced brace blocks
- 📦 Split into\nbalanced brace blocks → ⚙️ BeanShell eval\neach block
- ❌ JAVA-CODE-ERROR-003 → Error
- ❌ JAVA-CODE-ERROR-004 → Error
- ❌ JAVA-CODE-ERROR-006 → Error
- ❌ JAVA-CODE-ERROR-007 → Error

**How it works:**

1. **Read entries**: Loads the `javaCodeEntries` array
2. **For each entry** — processes in order:
  - **Set Variable**: validates fields → auto-parses value type → injects into BeanShell scope
  - **Code**: strips comments → splits into brace-balanced blocks → evaluates each block
3. **Console output**: `System.out.println()` is intercepted and shown in the AndroMate console; `System.err` is shown as an error
4. **Result**: Returns `VoidResult` on success

## Code examples

### Example 1 — Basic arithmetic and console output

```json
{
  "JavaCode": [
    {
      "id": "1",
      "title": "Java Code",
      "javaCodeEntries": [
        {
          "type": "Code",
          "code": "int a = 10;\nint b = 20;\nint result = a + b;\nSystem.out.println(\"Result: \" + result);"
        }
      ]
    }
  ]
}
```

`System.out.println` output: `Result: 30` — visible in the AndroMate execution console.

### Example 2 — Inject a workflow variable, compute, print

```json
{
  "JavaCode": [
    {
      "id": "2",
      "title": "Java Code",
      "javaCodeEntries": [
        {
          "type": "Set Variable",
          "variableName": "rttMs",
          "value": "$ntp_rtt"
        },
        {
          "type": "Code",
          "code": "double rttSec = rttMs / 1000.0;\nSystem.out.println(\"RTT in seconds: \" + rttSec);"
        }
      ]
    }
  ]
}
```

### Example 3 — String manipulation

```json
{
  "JavaCode": [
    {
      "id": "3",
      "title": "Java Code",
      "javaCodeEntries": [
        {
          "type": "Set Variable",
          "variableName": "rawOutput",
          "value": "$cmd_result"
        },
        {
          "type": "Code",
          "code": "String trimmed = rawOutput.trim();\nboolean contains = trimmed.contains(\"unreachable\");\nSystem.out.println(\"Contains unreachable: \" + contains);"
        }
      ]
    }
  ]
}
```

### Example 4 — Conditional logic with console trace

```json
{
  "JavaCode": [
    {
      "id": "4",
      "title": "Java Code",
      "javaCodeEntries": [
        {
          "type": "Set Variable",
          "variableName": "httpStatus",
          "value": "$http_status"
        },
        {
          "type": "Code",
          "code": "if (httpStatus == 200) {\n    System.out.println(\"[OK] Request succeeded\");\n} else {\n    System.err.println(\"[ERROR] Unexpected status: \" + httpStatus);\n}"
        }
      ]
    }
  ]
}
```

### Example 5 — Loop and accumulation

```json
{
  "JavaCode": [
    {
      "id": "5",
      "title": "Java Code",
      "javaCodeEntries": [
        {
          "type": "Code",
          "code": "int sum = 0;\nfor (int i = 1; i <= 5; i++) {\n    sum += i;\n    System.out.println(\"Step \" + i + \" → sum = \" + sum);\n}\nSystem.out.println(\"Final sum: \" + sum);"
        }
      ]
    }
  ]
}
```

## Input parameter details

### 1. Input parameter: `javaCodeEntries`

An ordered JSON array of entry objects executed sequentially. There are two entry types:

#### Entry type: `"Set Variable"`

Injects a workflow variable value into the BeanShell interpreter scope.

- Field: `type` | Type: String | Required: Yes | Description: Must be `"Set Variable"`
- Field: `variableName` | Type: String | Required: Yes | Description: Name of the variable in BeanShell scope (no `$` prefix)
- Field: `value` | Type: String | Required: Yes | Description: Value to inject — supports `$workflow_variable` references

**Type auto-resolution**: the string value is automatically parsed in order: Integer → Long → Float → String. The resolved Java type is what BeanShell sees.

#### Entry type: `"Code"`

Executes a BeanShell Java code block.

- Field: `type` | Type: String | Required: Yes | Description: Must be `"Code"`
- Field: `code` | Type: String | Required: Yes | Description: Java code to execute — multi-line supported

**Execution pipeline**:

1. `//` and `/* */` comments are stripped
2. Code is split into balanced brace blocks `{ }`
3. Each block is evaluated sequentially by the BeanShell interpreter
4. `System.out.println()` → forwarded to the AndroMate execution console
5. `System.err.println()` → forwarded as an error in the console

- **Default**: `[]` (empty array — task is a no-op)

## Complete JSON example

```json
{
  "JavaCode": [
    {
      "id": "1",
      "title": "Compute RTT statistics",
      "javaCodeEntries": [
        {
          "type": "Set Variable",
          "variableName": "rttMs",
          "value": "$ntp_rtt"
        },
        {
          "type": "Set Variable",
          "variableName": "threshold",
          "value": "200"
        },
        {
          "type": "Code",
          "code": "double rttSec = rttMs / 1000.0;\nSystem.out.println(\"RTT: \" + rttMs + \" ms (\" + rttSec + \" s)\");\nif (rttMs <= threshold) {\n    System.out.println(\"RTT within acceptable range\");\n} else {\n    System.err.println(\"RTT too high: \" + rttMs + \" ms\");\n}"
        }
      ]
    }
  ]
}
```