import json
import boto3
from datetime import datetime, timezone

dynamodb        = boto3.resource('dynamodb', region_name='us-east-1')
incidents_table = dynamodb.Table('CSDIncidents')
audit_table     = dynamodb.Table('CSDauditLog')

def lambda_handler(event, context):
    incident_id = event['incident_id']
    item_type   = event['item_type']         # 'domain' or 'script'
    detected_at = event.get('detected_at', datetime.now(timezone.utc).isoformat())
    now         = datetime.now(timezone.utc).isoformat()

    if item_type == 'domain':
        item = {
            'incident_id':  incident_id,
            'item_type':    'domain',
            'domain_name':  event.get('domain_name', 'unknown'),
            'action':       'BLOCK_DOMAIN',
            'status':       'OPEN',
            'detected_at':  detected_at,
            'created_at':   now,
            'updated_at':   now,
        }
    else:
        item = {
            'incident_id':               incident_id,
            'item_type':                 'script',
            'script_id':                 event.get('script_id', 'unknown'),
            'risk_level':                event.get('risk_level', 'unknown'),
            'form_fields_read':          event.get('form_fields_read', 0),
            'is_high_risk':              event.get('is_high_risk', False),
            'exceeds_form_fields':       event.get('exceeds_form_fields', False),
            'should_update_read_status': event.get('should_update_read_status', False),
            'action':                    event.get('action', 'NOTIFY_ONLY'),
            'status':                    'OPEN',
            'detected_at':               detected_at,
            'created_at':                now,
            'updated_at':                now,
        }

    incidents_table.put_item(Item=item)

    audit_table.put_item(Item={
        'log_id':      f"LOG-{incident_id}-CREATE",
        'incident_id': incident_id,
        'action':      'INCIDENT_CREATED',
        'item_type':   item_type,
        'timestamp':   now,
    })

    print(f"Incident {incident_id} created for {item_type}")
    return event   # pass everything to next state
