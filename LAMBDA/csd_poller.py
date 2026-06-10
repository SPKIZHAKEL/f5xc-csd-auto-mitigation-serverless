import json
import boto3
import requests
import uuid
from datetime import datetime, timezone

# ── AWS clients ───────────────────────────────────────────
secrets_client = boto3.client('secretsmanager', region_name='us-east-1')
dynamodb       = boto3.resource('dynamodb',      region_name='us-east-1')
stepfunctions  = boto3.client('stepfunctions',   region_name='us-east-1')

known_table = dynamodb.Table('CSDKnownItems')

end_time = int(time.time())
start_time = end_time - (7 * 24 * 60 * 60)
  
# ── Load secrets once at cold start ──────────────────────
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

# Replace with your Step Functions ARN after you create it in Phase 6
STEP_FUNCTIONS_ARN = 'arn:aws:states:us-east-1:YOUR_ACCOUNT_ID:stateMachine:CSD-Playbook'

# ── API helper ────────────────────────────────────────────
def safe_get(path):
    try:
        r = requests.get(
            f"{BASE}/api/shape/csd/namespaces/{NAMESPACE}{path}",
            headers=HEADERS,
            timeout=15
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"GET {path} failed: {e}")
        return {}

# ── DynamoDB helpers ──────────────────────────────────────
def is_known(item_id):
    resp = known_table.get_item(Key={'item_id': item_id})
    return 'Item' in resp

def mark_known(item_id, item_type, extra=None):
    known_table.put_item(Item={
        'item_id':    item_id,
        'item_type':  item_type,
        'first_seen': datetime.now(timezone.utc).isoformat(),
        **(extra or {}),
    })

# ── Main handler ──────────────────────────────────────────
def lambda_handler(event, context):
    print(f"[{datetime.now(timezone.utc).isoformat()}] Poller started")

    new_detections = 0

    # ── 1. Poll domains ───────────────────────────────────
    domains_data = safe_get('/detected_domains',{
        "duration":7,
        "start_time": start_time,
        "end_time": end_time,
        "limit": 100
    })
    domains = domains_data['domains_list']
    if not isinstance(domains, list):
        domains = []

    print(f"Domains returned: {len(domains)}")

    for domain in domains:
        domain_name = domain.get('domain')
        if not domain_name:
            continue

        item_id = f"domain::{domain_name}"

        if not is_known(item_id):
            print(f"  NEW DOMAIN: {domain_name}")
            mark_known(item_id, 'domain', {
                'domain_name': domain_name,
                'raw':         json.dumps(domain),
            })

            payload = {
                'incident_id':   f"INC-{uuid.uuid4().hex[:8].upper()}",
                'item_type':     'domain',
                'domain_name':   domain_name,
                'domain_object': domain,
                'detected_at':   datetime.now(timezone.utc).isoformat(),
                # Domains are always blocked — no condition check
                'action':        'BLOCK_DOMAIN',
            }

            stepfunctions.start_execution(
                stateMachineArn=STEP_FUNCTIONS_ARN,
                name=f"domain-{uuid.uuid4().hex[:8]}",
                input=json.dumps(payload),
            )
            new_detections += 1

    # ── 2. Poll scripts ───────────────────────────────────
    scripts_data = safe_get('/scripts',{
    "start_time": "1780395200",
    "end_time": "1781112600",
})
    scripts = scripts_data['scripts']
    if not isinstance(scripts, list):
        scripts = []

    print(f"Scripts returned: {len(scripts)}")

    for script in scripts:
         script_id = script.get('id') 
        if not script_id:
            continue

        item_id = f"script::{script_id}"

        if not is_known(item_id):
            print(f"  NEW SCRIPT: {script_id}")

            # ── Decision logic (exact as specified) ───────
            risk_level       = str(script.get('risk_level', '')).strip()
            form_fields_read = int(script.get('form_fields_read', 0) or 0)

            is_high_risk        = risk_level == 'High Risk'
            exceeds_form_fields = form_fields_read > 1

            should_update_read_status = is_high_risk or exceeds_form_fields

            print(
                f"    risk_level='{risk_level}' "
                f"form_fields_read={form_fields_read} "
                f"should_update_read_status={should_update_read_status}"
            )

            mark_known(item_id, 'script', {
                'script_id':       script_id,
                'risk_level':      risk_level,
                'form_fields_read': form_fields_read,
            })

            payload = {
                'incident_id':             f"INC-{uuid.uuid4().hex[:8].upper()}",
                'item_type':               'script',
                'script_id':               script_id,
                'script_object':           script,
                'risk_level':              risk_level,
                'form_fields_read':        form_fields_read,
                'is_high_risk':            is_high_risk,
                'exceeds_form_fields':     exceeds_form_fields,
                'should_update_read_status': should_update_read_status,
                'detected_at':             datetime.now(timezone.utc).isoformat(),
                'action': 'UPDATE_READ_STATUS' if should_update_read_status else 'NOTIFY_ONLY',
            }

            stepfunctions.start_execution(
                stateMachineArn=STEP_FUNCTIONS_ARN,
                name=f"script-{uuid.uuid4().hex[:8]}",
                input=json.dumps(payload),
            )
            new_detections += 1

    print(f"Poller complete. New detections: {new_detections}")
    return {'new_detections': new_detections}
