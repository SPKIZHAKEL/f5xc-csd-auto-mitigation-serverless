
## Create the SNS Topic and Email Subscription

1. Search for **SNS** in the AWS Console.
2. Go to **Topics** → **Create topic**.

### Topic Configuration

| Field | Value |
|---------|---------|
| Type | Standard |
| Name | `CSD-Alerts` |

3. Click **Create topic**.

### Create an Email Subscription

1. Open the newly created topic.
2. Click **Create subscription**.

| Field | Value |
|---------|---------|
| Protocol | Email |
| Endpoint | `your-security-team@company.com` |

3. Click **Create subscription**.

### Confirm the Subscription

1. Check the inbox for the email address you specified.
2. Open the AWS SNS confirmation email.
3. Click the **Confirm subscription** link.

### Copy the Topic ARN

After the topic is created, copy the **Topic ARN** (for example):

```text
arn:aws:sns:us-east-1:123456789012:CSD-Alerts
```

This ARN is needed when configuring the Lambda functions and updating the `SNS_TOPIC_ARN` environment variable.
