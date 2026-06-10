
## Create DynamoDB Tables

Create the following three DynamoDB tables using the default settings.

### Steps

1. Search for **DynamoDB** in the AWS Console.
2. Click **Create table**.
3. Leave all settings at their defaults unless otherwise specified.
4. Create the tables listed below.

---

## Table 1: `CSDKnownItems`

### Configuration

| Field | Value |
|---------|---------|
| Table name | `CSDKnownItems` |
| Partition key | `item_id` (String) |

### Purpose

Stores every domain, script, or indicator that has already been observed.

This table is used by the polling Lambda function to:

- Track previously discovered items
- Detect newly observed items during each poll cycle
- Prevent duplicate incident creation

---

## Table 2: `CSDIncidents`

### Configuration

| Field | Value |
|---------|---------|
| Table name | `CSDIncidents` |
| Partition key | `incident_id` (String) |

### Purpose

Acts as the central incident repository for the solution.

This table stores:

- Newly detected incidents
- Incident status information
- Related indicators and metadata
- Investigation and mitigation results

Equivalent to the incident database used in traditional SOAR platforms.

---

## Table 3: `CSDauditLog`

### Configuration

| Field | Value |
|---------|---------|
| Table name | `CSDauditLog` |
| Partition key | `log_id` (String) |

### Purpose

Maintains a complete audit trail of all automated and manual actions.

Examples include:

- Domain block actions
- Notification events
- Incident updates
- Read-status changes
- Workflow execution records

Each entry should include a timestamp and relevant action details to support auditing and compliance requirements.

---

## Summary

| Table | Purpose |
|---------|---------|
| `CSDKnownItems` | Tracks previously seen domains and indicators |
| `CSDIncidents` | Stores incident records and investigation data |
| `CSDauditLog` | Stores audit logs for all workflow actions |
