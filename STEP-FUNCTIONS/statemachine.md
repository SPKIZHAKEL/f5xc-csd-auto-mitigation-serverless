## Configure Account-Specific Values

1. Replace all instances of `YOUR_ACCOUNT_ID` with your 12-digit AWS account ID.

2. Create the Step Functions state machine:
   - Name: `CSD-Playbook`
   - Click **Create state machine**

3. After the state machine is created:
   - Copy the **State Machine ARN**
   - Open **Lambda 1 (`csd_poller`)**
   - Update the `STEP_FUNCTIONS_ARN` environment variable with the copied ARN
   - Click **Deploy** on Lambda 1 again

4. Open **Lambda 3**
   - Replace `YOUR_ACCOUNT_ID` in the `SNS_TOPIC_ARN` value with your 12-digit AWS account ID
   - Save and deploy the function if required
