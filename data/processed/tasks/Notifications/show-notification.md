# Show Notification

## Summary

- **Internal name**: `ShowNotification`
- **Category**: Notifications
- **Purpose**: Display a system notification with a title and a message. Reuse the same notification ID to update or replace an existing notification.
- **Task type**: Normal

## Compatibility

- **Minimum AndroMate version**: `{{ ANDROMATE_FIRST_VERSION }}`
- **Maximum AndroMate version**: `{{ ANDROMATE_CURRENT_VERSION }}`
- **Minimum Android**: `{{ ANDROMATE_MIN_APP_SDK }}`
- **Maximum Android tested**: `{{ ANDROID_CURRENT_APP_SDK }}`
- **Required permissions**: `POST_NOTIFICATIONS`

## Detailed description

The **Show Notification** task posts a notification to the system tray on a dedicated channel (`andromate_workflow_notifications`). The message is displayed with `BigTextStyle`, so long content is shown in full.

The task works from the background (foreground service) — notifications are designed for that. On Android 13+ (API 33), the `POST_NOTIFICATIONS` runtime permission must be granted; if it is not, the task throws `NOTIFICATION-TASK-001`.

## Input parameters

- Parameter: `title_text` | Type: String | Required: Yes | Possible values / Rules: Notification title (supports interpolation) | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `""`
- Parameter: `message` | Type: String | Required: Yes | Possible values / Rules: Notification body (supports interpolation) | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `""`
- Parameter: `notification_id` | Type: Integer | Required: No | Possible values / Rules: Reuse the same ID to update/replace a notification | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `0` (auto)

## Output parameters

This task produces no output variable. It returns a `VoidResult` on success.

## Exceptions

- Code: `NOTIFICATION-TASK-001` | Trigger condition: `POST_NOTIFICATIONS` permission not granted (Android 13+)

## Execution flowchart

Diagram Nodes:
- Resolve: 🔧 Resolve title & message
- Channel: 📡 Ensure notification channel
- Build: 🔔 Build notification\nBigTextStyle
- Notify: 📬 NotificationManager.notify

Workflow Flow:
- 🔧 Resolve title & message → 📡 Ensure notification channel
- 📡 Ensure notification channel → 🔔 Build notification\nBigTextStyle
- 🔔 Build notification\nBigTextStyle → Post
- 📬 NotificationManager.notify → Success

**How it works:**

1. **Resolve**: `title_text` and `message` are resolved against the AndroMate context
2. **Channel**: the notification channel is created (idempotent)
3. **Build**: a notification is built with `BigTextStyle`
4. **Post**: `NotificationManager.notify(id, ...)` — throws `NOTIFICATION-TASK-001` if the permission is missing
5. **Result**: returns `VoidResult`

## Code examples

### Example 1 — Notify when a workflow finishes

```json
{
  "ShowNotification": [
    {
      "id": "1",
      "title": "Notify done",
      "title_text": "Workflow finished",
      "message": "Job $job_name completed successfully"
    }
  ]
}
```

### Example 2 — Update the same notification (fixed ID)

```json
{
  "ShowNotification": [
    {
      "id": "2",
      "title": "Progress notification",
      "title_text": "Progress",
      "message": "Step 2 / 5 done",
      "notification_id": 42
    }
  ]
}
```

## Input parameter details

### `title_text` — Notification title

The bold title line of the notification. Supports `$variable` and `${SPECIAL_VAR}` interpolation.

### `message` — Notification body

The body text. Long messages are displayed in full thanks to `BigTextStyle`.

### `notification_id` — Notification ID

Optional. If a positive value is given, the notification reuses that ID (a new call with the same ID **updates/replaces** the existing one). If left empty or `0`, a unique ID is generated so each call shows a new notification.

## Output parameter details

This task produces no output variable.

## Complete JSON example

```json
{
  "ShowNotification": [
    {
      "id": "1",
      "title": "Show Notification",
      "title_text": "AndroMate",
      "message": "Test completed",
      "notification_id": 100
    }
  ]
}
```