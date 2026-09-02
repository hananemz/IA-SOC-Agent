# ==============================================================================
# Elasticsearch DLS: Document-Level Security by team_id
#
# Each user gets a role that filters documents by their team_id.
# The team_id value is injected from user metadata via Mustache template.
#
# Prerequisites:
#   - Index(ies) must have a "team_id" field (keyword type recommended)
#   - Users must have metadata.team_id set
# ==============================================================================

# --- 1. Create the DLS role (generic, reusable per team) ---
#
# Replace "data-*" with your actual index pattern(s).
#
PUT /_security/role/team-isolated-reader
{
  "description": "Read-only access scoped to user's team via DLS",
  "indices": [
    {
      "names": ["data-*", "metrics-*", "logs-*"],
      "privileges": ["read", "view_index_metadata"],
      "query": {
        "enabled": true,
        "type": "always_include",
        "default": "{\"match_all\": {}}",
        "template": {
          "source": "{\"bool\":{\"filter\":{\"term\":{\"team_id\":\"{{_user.metadata.team_id}}\"}}}}"
        }
      }
    }
  ]
}

# --- 2. Example users with team metadata ---

POST /_security/user/alice
{
  "password": "X9k#mP2vL!qR7wZn",
  "roles": ["team-isolated-reader"],
  "metadata": {
    "team_id": "platform"
  }
}

POST /_security/user/bob
{
  "password": "aB4$nK8rT!mQ1vWx",
  "roles": ["team-isolated-reader"],
  "metadata": {
    "team_id": "security"
  }
}

# --- 3. Verify — search as Alice (should only see platform docs) ---
#
# GET /data-*/_search
#   Authorization: Basic alice:X9k#mP2vL!qR7wZn
#   {"query": {"match_all": {}}}

# --- 4. Verify — search as Bob (should only see security docs) ---
#
# GET /data-*/_search
#   Authorization: Basic bob:aB4$nK8rT!mQ1vWx
#   {"query": {"match_all": {}}}

# --- 5. Check role is active ---
GET /_security/role/team-isolated-reader

# --- 6. List users with their team_id metadata ---
GET /_security/user?filter_path=users.*.metadata,users.*.roles
