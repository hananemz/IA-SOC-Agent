# ==============================================================================
# ES|QL queries to track dashboard modifications
# Run these after Kibana audit logs are shipped to Elasticsearch
# Index: kibana-audit-*
# ==============================================================================

# 1. All dashboard modifications in the last 24h
from kibana-audit-*
| where kibana.audit.event.action in ("saved_object_create", "saved_object_update", "saved_object_delete")
  and kibana.audit.config.object_type == "dashboard"
| sort @timestamp desc
| keep @timestamp, kibana.audit.event.action, kibana.audit.config.object_id,
       kibana.audit.config.title, user.name, source.ip

# 2. Dashboard deletions only
from kibana-audit-*
| where kibana.audit.event.action == "saved_object_delete"
  and kibana.audit.config.object_type == "dashboard"
| sort @timestamp desc
| keep @timestamp, kibana.audit.config.title, user.name, source.ip, trace.id

# 3. Per-user activity summary (last 7 days)
from kibana-audit-*
| where kibana.audit.event.action in ("saved_object_create", "saved_object_update", "saved_object_delete")
  and kibana.audit.config.object_type == "dashboard"
| stats count() by user.name, kibana.audit.event.action
| sort count_ desc

# 4. Correlate with Elasticsearch audit using trace.id
# Replace ${TRACE_ID} with the trace.id from a Kibana audit event
from .security-audit-*
| where trace.id == "${TRACE_ID}"
| sort @timestamp asc
| keep @timestamp, event.action, user.name, source.ip
