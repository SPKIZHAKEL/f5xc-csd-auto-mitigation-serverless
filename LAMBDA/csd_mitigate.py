import json
import boto3
import requests
from datetime import datetime, timezone

secrets_client  = boto3.client('secretsmanager', region_name='us-east-1')
dynamodb        = boto3.resource('dynamodb',      region_name='us-east-1')
audit_table     = dynamodb.Table('CSDauditLog')
incidents_table = dynamodb.Table('CSDIncidents')

def load_secrets():
    raw = secrets_client.get_secret_value(SecretId='f5-csd-soar')
    return json.loads(raw['SecretString'])

SECRETS   = load_secrets()
BASE      = SECRETS['base_url']
NAMESPACE = SECRETS['namespace']
HEADERS   = {
    'Authorization': f"APIToken {SECRETS['token']}",
    'Content-Type':  'application/json',
}

def safe_post(path, body):
    try:
        r = requests.post(
            f"{BASE}/api/shape/csd/namespaces/{NAMESPACE}{path}",
            headers=HEADERS,
            json=body,
            timeout=15
        )
        r.raise_for_status()
        print(f"POST {path} succeeded: {r.status_code}")
        return r.json()
    except Exception as e:
        print(f"POST {path} failed: {e}")
        return None

def safe_put(path, body):
    try:
        r = requests.put(
            f"{BASE}/api/shape/csd/namespaces/{NAMESPACE}{path}",
            headers=HEADERS,
            json=body,
            timeout=15
        )
        r.raise_for_status()
        print(f"PUT {path} succeeded: {r.status_code}")
        return r.json()
    except Exception as e:
        print(f"PUT {path} failed: {e}")
        return None

def lambda_handler(event, context):
    item_type   = event.get('item_type')
    incident_id = event.get('incident_id')
    now         = datetime.now(timezone.utc).isoformat()
    action_taken = 'NONE'

    # ── DOMAIN: always block ──────────────────────────────
    if item_type == 'domain':
        domain_name = event.get('domain_name', 'unknown')
        print(f"  Blocking domain: {domain_name}")

        # POST to mitigated_domains
        # Endpoint: POST /api/shape/csd/namespaces/{ns}/mitigated_domains
        result = safe_post('/mitigated_domains', {
            'metadata': {
                'namespace': NAMESPACE,
                'name':      domain_name,
            },
            'spec': {
                'mitigated_domain': domain_name,
            },
        })

        action_taken = 'DOMAIN_BLOCKED' if result is not None else 'DOMAIN_BLOCK_FAILED'
        print(f"  Domain mitigation result: {action_taken}")

    # ── SCRIPT: update read status only if threshold met ──
    elif item_type == 'script':
        script_id              = event.get('script_id', 'unknown')
        should_update          = event.get('should_update_read_status', False)
        risk_level             = event.get('risk_level', 'unknown')
        form_fields_read       = event.get('form_fields_read', 0)

        if should_update:
            print(
                f"  Updating read status for script: {script_id} "
                f"(risk_level='{risk_level}', form_fields_read={form_fields_read})"
            )

            # POST to UpdateScriptReadStatus
            # Endpoint: POST /api/shape/csd/namespaces/{ns}/script_read_status
            result = safe_post(f'scripts/{script_id}/readStatus', {
                'namespace': NAMESPACE,
                'name':      script_id,
                'type':"BLOCK"
            })

            action_taken = (
                'SCRIPT_READ_STATUS_UPDATED'
                if result is not None
                else 'SCRIPT_READ_STATUS_FAILED'
            )
        else:
            print(
                f"  Skipping read status update for script: {script_id} "
                f"(risk_level='{risk_level}', form_fields_read={form_fields_read} — below threshold)"
            )
            action_taken = 'SCRIPT_READ_STATUS_SKIPPED'

    # ── Update incident status in DynamoDB ────────────────
    incidents_table.update_item(
        Key={'incident_id': incident_id},
        UpdateExpression='SET action_taken = :at, #s = :s, updated_at = :ua',
        ExpressionAttributeNames={'#s': 'status'},
        ExpressionAttributeValues={
            ':at': action_taken,
            ':s':  'CLOSED',
            ':ua': now,
        }
    )

    # ── Audit log ─────────────────────────────────────────
    audit_table.put_item(Item={
        'log_id':      f"LOG-{incident_id}-MITIGATE",
        'incident_id': incident_id,
        'action':      action_taken,
        'item_type':   item_type,
        'timestamp':   now,
    })

    return {**event, 'action_taken': action_taken, 'incident_status': 'CLOSED'}
