# ==============================================================================
# Elasticsearch Security Audit Logging
# Focus: Track permission denied (access_denied) events
# ==============================================================================
#
# Target: https://host.docker.internal:9200
# Run as: elastic (or a user with cluster:manage_cluster settings)
#
# Prerequisites:
#   - Gold, Platinum, Enterprise, or trial license
#   - Cluster settings API access (cluster:admin or cluster:manage)
# ==============================================================================

$EsUrl = "https://host.docker.internal:9200"
$Auth = "Basic " + [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("elastic:changeme"))
$Headers = @{
  "Authorization" = $Auth
  "Content-Type"  = "application/json"
}

# ------------------------------------------------------------------
# 1. Enable security audit logging - failure + denial events only
#    Captures all permission-denied events while keeping volume low.
# ------------------------------------------------------------------
$AuditConfig = @{
  persistent = @{
    "xpack.security.audit.enabled"                          = $true
    "xpack.security.audit.logfile.events.include"           = @(
      "access_denied",
      "anonymous_access_denied",
      "run_as_denied",
      "connection_denied",
      "tampered_request",
      "security_config_change"
    )
    "xpack.security.audit.logfile.log_index"                = $true
  }
} | ConvertTo-Json -Depth 5

Write-Host "[1/3] Applying audit config..." -ForegroundColor Cyan
$Result = Invoke-RestMethod -Uri "$EsUrl/_cluster/settings" -Method Put -Headers $Headers `
  -Body $AuditConfig -UseBasicParsing
Write-Host "[+] Done - acknowledged: $($Result.acknowledged)" -ForegroundColor Green

# ------------------------------------------------------------------
# 2. Configure filter policies to suppress noise from known users
# ------------------------------------------------------------------
$FilterConfig = @{
  persistent = @{
    "xpack.security.audit.filter.exclude_users"             = @(
      "kibana_system"
    )
  }
} | ConvertTo-Json -Depth 5

Write-Host "[2/3] Applying filter policies..." -ForegroundColor Cyan
$Result2 = Invoke-RestMethod -Uri "$EsUrl/_cluster/settings" -Method Put -Headers $Headers `
  -Body $FilterConfig -UseBasicParsing
Write-Host "[+] Done - acknowledged: $($Result2.acknowledged)" -ForegroundColor Green

# ------------------------------------------------------------------
# 3. Verify audit is enabled
# ------------------------------------------------------------------
Write-Host "[3/3] Verifying settings..." -ForegroundColor Cyan
$Verify = Invoke-RestMethod -Uri "$EsUrl/_cluster/settings?include_defaults=true&flat_settings=true" `
  -Method Get -Headers $Headers -UseBasicParsing

Write-Host "`n=== Active audit settings ===" -ForegroundColor Yellow
foreach ($prop in $Verify.defaults.PSObject.Properties) {
  if ($prop.Name -like "*security.audit*") {
    Write-Host "  $($prop.Name) = $($prop.Value)"
  }
}

Write-Host "`n[+] Audit logging configured. Events land in .security-audit-* indices." -ForegroundColor Green
Write-Host "[+] Wait ~30s for first events, then run query-audit-access-denied.ps1" -ForegroundColor Green
