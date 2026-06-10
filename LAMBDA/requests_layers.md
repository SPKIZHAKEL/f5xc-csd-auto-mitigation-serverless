## Add the Requests Layer to AWS Lambda Functions

### Lambda 1: `csd_poller`

1. Open **Lambda** → **csd_poller**
2. Go to **Layers** → **Add a layer**
3. Select **Specify an ARN. note instead of latest it should be version**
4. Paste the following public ARN (Requests library for Python 3.12 in `us-east-1`):

   ```text
   arn:aws:lambda:us-east-1:770693421928:layer:Klayers-p312-requests:latest
   ```

5. Click **Verify**
6. Click **Add**

### Lambda 4: `csd_mitigate`

Repeat the same steps:

1. Open **Lambda** → **csd_mitigate**
2. Go to **Layers** → **Add a layer**
3. Select **Specify an ARN. note instead of latest it should be version**
4. Paste:

   ```text
   arn:aws:lambda:us-east-1:770693421928:layer:Klayers-p312-requests:latest
   ```

5. Click **Verify**
6. Click **Add**
