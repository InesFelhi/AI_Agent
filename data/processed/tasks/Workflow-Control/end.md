# End

## Summary

- **Internal name**: `End`
- **Category**: Workflow Control
- **Purpose**: Mark the termination point of a workflow execution graph.
- **Task type**: Workflow Control

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

The **End** task marks the **terminal node** of a workflow execution graph. Every workflow must have exactly one End node. When execution reaches the End task, the workflow is considered complete and the AndroMate engine stops traversal.

The End task is a **Workflow Control** task — like the Start task, it is skipped during normal graph traversal and only marks the boundary of execution. It accepts no input parameters and produces no output.

Every workflow link chain must eventually reach the End node. Graphs without a reachable End node are considered malformed.

## Input parameters

This task has **no input parameters**.

## Output parameters

This task produces **no output variables**. It returns `VoidResult`.

## Execution flowchart

Diagram describing workflow steps.

**How it works:**

1. The workflow engine reaches the End node via a link from the last task
2. No logic is executed — the End node is a marker
3. The workflow execution is finalized

## Complete JSON example

```json
{
  "Start": [{ "id": "0", "title": "Start" }],

  "End": [{ "id": "100", "title": "End" }],

  "Links": [
    { "from": "0", "to": "100" }
  ]
}
```