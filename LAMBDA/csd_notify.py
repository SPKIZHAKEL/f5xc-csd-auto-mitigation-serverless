import json
import boto3
from datetime import datetime, timezone

sns         = boto3.client('sns',      region_name='us-east-1')
dynamodb    = boto3.resource('dynamodb', region_name='us-east-1')
audit_table = dynamodb.Table('CSDauditLog')

# Replace with your SNS Topic ARN from Phase 3
SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:CSD-Alerts'

def build_message(event):
    item_type   = event.get('item_type')
    incident_id = event.get('incident_id')

    if item_type == 'domain':
        domain = event.get('domain_name', 'unknown')
        subject = f"[F5 CSD ALERT] New domain detected — {domain}"
        message = f"""
F5 CLIENT SIDE DEFENSE — NEW DOMAIN DETECTED
=============================================
Incident ID  : {incident_id}
Detected at  : {event.get('detected_at', 'unknown')}

DOMAIN DETAILS
--------------
Domain       : {domain}

ACTION TAKEN
------------
[✓] Domain submitted to F5 CSD mitigated_domains (blocked)
[✓] Incident created in CSDIncidents
[✓] This SNS alert sent

=============================================
""".strip()

    else:
        script_id        = event.get('script_id', 'unknown')
        risk_level       = event.get('risk_level', 'unknown')
        form_fields_read = event.get('form_fields_read', 0)
        is_high_risk     = event.get('is_high_risk', False)
        exceeds_ff       = event.get('exceeds_form_fields', False)
        update_read      = event.get('should_update_read_status', False)

        triggered_by = []
        if is_high_risk:
            triggered_by.append(f"risk_level = '{risk_level}'")
        if exceeds_ff:
            triggered_by.append(f"form_fields_read = {form_fields_read} (> 1)")
        trigger_str = ' AND '.join(triggered_by) if triggered_by else 'None — notify only'

        subject = f"[F5 CSD ALERT] New script detected — {script_id} | {risk_level}"
        message = f"""
F5 CLIENT SIDE DEFENSE — NEW SCRIPT DETECTED
=============================================
Incident ID      : {incident_id}
Detected at      : {event.get('detected_at', 'unknown')}

SCRIPT DETAILS
--------------
Script ID        : {script_id}
Risk Level       : {risk_level}
Form Fields Read : {form_fields_read}

MITIGATION TRIGGER
------------------
Triggered by     : {trigger_str}
Update Read Status: {'YES' if update_read else 'NO — below threshold'}

ACTION TAKEN
------------
{'[✓] UpdateScriptReadStatus called on F5 CSD API' if update_read else '[—] Read status NOT updated (risk below threshold)'}
[✓] Incident created in CSDIncidents
[✓] This SNS alert sent

=============================================
""".strip()

    return subject, message

def lambda_handler(event, context):
    subject, message = build_message(event)
    incident_id = event.get('incident_id')

    try:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject[:100],   # SNS subject max 100 chars
            Message=message,
        )
        print(f"SNS published for incident {incident_id}")
    except Exception as e:
        print(f"SNS publish failed: {e}")
        # Do not raise — notification failure should not stop the playbook

    audit_table.put_item(Item={
        'log_id':      f"LOG-{incident_id}-NOTIFY",
        'incident_id': incident_id,
        'action':      'SNS_NOTIFICATION_SENT',
        'item_type':   event.get('item_type'),
        'timestamp':   datetime.now(timezone.utc).isoformat(),
    })

    return event
