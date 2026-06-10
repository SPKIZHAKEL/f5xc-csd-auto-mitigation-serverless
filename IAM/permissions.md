
## Create the IAM Role for Lambda

1. Search for **IAM** in the AWS Console.
2. Go to **Roles** → **Create role**.
3. Select **AWS service** as the trusted entity.
4. Choose **Lambda**.
5. Click **Next**.

### Attach the Following Policies

| Policy | Purpose |
|----------|----------|
| `AmazonDynamoDBFullAccess` | Read and write access to `CSDKnownItems`, `CSDIncidents`, and `CSDauditLog` tables |
| `AWSSecretsManagerReadWrite` | Read the F5 API token and configuration at runtime |
| `AmazonSNSFullAccess` | Publish notifications and alerts |
| `CloudWatchLogsFullAccess` | Create and manage audit trail logs |
| `AWSStepFunctionsFullAccess` | Start and manage Step Functions state machine executions |

6. Click **Next**.
7. Provide a role name (for example, `CSD-Lambda-Role`).
8. Click **Create role**.
