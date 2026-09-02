# ==============================================================================
# Quick test: seed sample docs with team_id, then verify DLS isolation
# Run from terminal with curl against your ES cluster.
# ==============================================================================

$EsHost = "host.docker.internal:9200"
$Cred = New-Object PSCredential("elastic", (ConvertTo-SecureString "changeme" -AsPlainText -Force))

# Create a test index with team_id as keyword
Invoke-RestMethod -Uri "https://$EsHost/dls-test" -Method Put -UseBasicParsing -Credential $Cred -ContentType "application/json" -Body '{"mappings":{"properties":{"team_id":{"type":"keyword"},"message":{"type":"text"}}}}'

# Index 3 docs - 2 platform, 1 security
@(@{team_id="platform";message="platform-internal-1"},@{team_id="platform";message="platform-internal-2"},@{team_id="security";message="security-internal-1"}) | ForEach-Object {
  Invoke-RestMethod -Uri "https://$EsHost/dls-test/_doc" -Method Post -UseBasicParsing -Credential $Cred -ContentType "application/json" -Body ($_ | ConvertTo-Json)
}

Write-Host "Test data seeded. Apply the DLS role from elasticsearch-dls-teamid.md"
Write-Host "Then test: curl -s -u alice:PASSWORD https://$EsHost/dls-test/_search"
