# F5XC-csd-auto-mitigation-serverless

Serverless SOAR-equivalent on AWS that automatically detects and mitigates
malicious domains and suspicious scripts reported by F5 XC
Client Side Defense (CSD).



---

## Architecture overview

```
EventBridge (every 30 min)
        │
        ▼
Lambda: csd_poller  ──────────────────── F5 XC CSD API
        │                                (GET /domains, GET /scripts)
        ▼
DynamoDB: CSDKnownItems
   already seen? → skip
   new item?     → start Step Functions
        │
        ▼
Step Functions: CSD-Playbook
   ├── csd_create_incident  → DynamoDB: CSDIncidents
   ├── csd_notify           → SNS: CSD-Alerts → email
   └── csd_mitigate         → F5 XC CSD API
           domain → POST /mitigated_domains
           script (High Risk or form_fields_read > 1)
                  → POST /script_read_status
        │
        ▼
DynamoDB: CSDauditLog  (every action timestamped)
```

---

## Prerequisites

### AWS account
- AWS account with billing enabled (all services used are within free tier)
- Region: `eg. ap-south-1` — all resources must be in the same region
- IAM user or role with admin access to create the services below

### AWS services used
| Service | Purpose |
|---|---|
| IAM | Execution roles for Lambda, Step Functions, EventBridge |
| Secrets Manager | Stores F5 XC API token and namespace |
| DynamoDB | Three tables for state, incidents, and audit log |
| Lambda (Python 3.12) | Four functions implementing the playbook steps |
| Step Functions (Standard) | Orchestrates the four Lambda steps |
| EventBridge Scheduler | Triggers the poller every 10 minutes |
| SNS | Sends email alerts to the security team |
| CloudWatch Logs | Automatic Lambda execution logs |

### F5 prerequisites
- F5 XC tenant with Client Side Defense enabled
- F5 XC API token with CSD read and write permissions
- Tenant name and namespace

### Python layer
- `Klayers-p312-requests` layer — find the versioned ARN for `ap-south-1` at:
  `https://api.klayers.cloud/api/v2/p3.12/layers/latest/ap-south-1/json`
- Required by `csd_poller` and `csd_mitigate` only

---

## Setup phases

### Phase 1 — IAM role
Create role `F5-CSD-SOAR-Role` with trust for Lambda service.

Attach policies: `AmazonDynamoDBFullAccess`, `AWSSecretsManagerReadWrite`,
`AmazonSNSFullAccess`, `CloudWatchLogsFullAccess`, `AWSStepFunctionsFullAccess`.

### Phase 2 — Secrets Manager
Create secret `f5-csd-soar` with keys:
`base_url`, `token`, `namespace`.

### Phase 3 — SNS topic
Create standard topic `CSD-Alerts`.
Add email subscription and confirm via the verification link.

### Phase 4 — DynamoDB tables
Create three tables with partition key `item_id` (String) each:
- `CSDKnownItems` — detection state (the diff engine)
- `CSDIncidents` — incident log
- `CSDauditLog` — full action audit trail

### Phase 5 — Lambda functions
Create four functions, all Python 3.12, role `F5-CSD-SOAR-Role`,
timeout 5 minutes:

| Function | Purpose | Requests layer needed |
|---|---|---|
| `csd_poller` | Polls F5, compares state, starts Step Functions | Yes |
| `csd_create_incident` | Writes incident to DynamoDB | No |
| `csd_notify` | Publishes SNS alert | No |
| `csd_mitigate` | Calls F5 block/read-status APIs | Yes |

Add the `Klayers-p312-requests` layer to `csd_poller` and `csd_mitigate`.

### Phase 6 — Requests Lambda layer
Add the versioned `Klayers-p312-requests` ARN for `ap-south-1` to
`csd_poller` and `csd_mitigate`.

### Phase 7 — Step Functions state machine

<img width="1600" height="1040" alt="image" src="https://github.com/user-attachments/assets/301c5294-bc18-47f8-ac26-9fad56d57e3f" />


Create Standard workflow named `CSD-Playbook`.

Create role `F5-CSD-StepFunctions-Role` with trust for `states.amazonaws.com`
and `lambda:InvokeFunction` permission on all four Lambda ARNs.

State machine order: `CreateIncident → NotifyAnalyst → Mitigate → PlaybookComplete`.
Each state retries up to 3 times before routing to `HandleError`.

Update `csd_poller` with the state machine ARN after creation.

### Phase 8 — EventBridge Scheduler
Create schedule `csd-poller-schedule`, rate 30 minutes, target `csd_poller`.

Create role `F5-CSD-EventBridge-Role` with trust for `scheduler.amazonaws.com`
and `lambda:InvokeFunction` on `csd_poller`.

---

## Detection and mitigation logic

### New domain detected
Any domain not present in `CSDKnownItems` is immediately submitted to
`POST /mitigated_domains` on the F5 XC CSD API (auto-block).

### New script detected
A script not present in `CSDKnownItems` triggers `POST /script_read_status`
(UpdateScriptReadStatus) only if either condition is true:

```
risk_level == "High Risk"   OR   form_fields_read > 1
```

If neither condition is met, an incident and SNS alert are still created
but no read-status update is sent to F5.

---

## Resetting for a re-run

Run the `csd_reset_tables` Lambda (created separately) to purge all three
DynamoDB tables. This makes the poller treat every domain and script as new
on the next execution, restarting the full detection and mitigation flow.

---

## Estimated cost

| Service | Free tier | Estimated monthly |
|---|---|---|
| Lambda | 1M requests free | Free |
| Step Functions | 4,000 transitions free | Free |
| DynamoDB | 25 GB + 25 WCU free | Free |
| SNS | 1M publishes + 1,000 emails free | Free |
| EventBridge | 14M events free | Free |
| Secrets Manager | — | ~$0.40 |
| **Total** | | **~$0.40/month** |

---

## Monitoring

| Where | What to check |
|---|---|
| EventBridge → Schedules → Invocation history | Last 24h trigger attempts |
| CloudWatch → Metrics → EventBridge → InvocationAttemptCount | Trigger count over any period |
| Lambda → csd_poller → Monitor | Invocations, errors, duration |
| Step Functions → CSD-Playbook → Executions | Visual playbook run history |
| DynamoDB → CSDIncidents → Explore items | All incidents |
| DynamoDB → CSDauditLog → Explore items | Full audit trail |
