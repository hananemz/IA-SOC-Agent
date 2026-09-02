# ==============================================================================
# Elasticsearch Security Audit — Apply & Verify
# Focus: Track permission denied (access_denied) events
# ==============================================================================
#
# Adjust variables below, then run the commands in order.
# Tested with curl on Linux/macOS/Windows Git Bash.
# ==============================================================================

ES_URL="https://host.docker.internal:9200"
ES_AUTH="elastic:changeme"

# --- 1. Enable audit logging (denial events only) ---
curl -s -u "$ES_AUTH" -X PUT "$ES_URL/_cluster/settings" \
  -H "Content-Type: application/json" \
  -d @es-audit-settings.json

echo ""

# --- 2. Trigger a test denial (will fail — that's the point) ---
curl -s -u "nobody:wrong" "$ES_URL/_cat/indices?v" 2>/dev/null || true

# --- 3. Wait for audit index to populate ---
echo "Waiting 15s for audit events..."
sleep 15

# --- 4. Query access_denied events ---
curl -s -u "$ES_AUTH" -X POST "$ES_URL/.security-audit-*/_search" \
  -H "Content-Type: application/json" \
  -d '{
  "size": 20,
  "query": {
    "bool": {
      "filter": [
        { "terms": { "event.action": ["access_denied", "anonymous_access_denied"] } },
        { "range": { "@timestamp": { "gte": "now-24h" } } }
      ]
    }
  },
  "sort": [{ "@timestamp": { "order": "desc" } }]
}' | python -m json.tool

# --- 5. Summary by user ---
curl -s -u "$ES_AUTH" -X POST "$ES_URL/.security-audit-*/_search" \
  -H "Content-Type: application/json" \
  -d '{
  "size": 0,
  "query": {
    "bool": {
      "filter": [
        { "terms": { "event.action": ["access_denied", "anonymous_access_denied"] } },
        { "range": { "@timestamp": { "gte": "now-24h" } } }
      ]
    }
  },
  "aggs": {
    "by_user": { "terms": { "field": "user.name", "size": 20 } },
    "by_reason": { "terms": { "field": "event.action", "size": 10 } }
  }
}' | python -m json.tool
