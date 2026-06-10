
## Create the EventBridge Schedule

1. Search for **EventBridge** in the AWS Console.
2. Go to **Schedules** → **Create schedule**.

### Schedule Configuration

| Field | Value |
|---------|---------|
| Schedule name | `csd-poller-schedule` |
| Schedule pattern | Recurring schedule |
| Occurrence | Rate-based |
| Rate | Every 10 minutes |

3. Click **Next**.

### Target Configuration

| Field | Value |
|---------|---------|
| Target API | AWS Lambda Invoke |
| Function | `csd_poller` |

4. Click **Create schedule**.
