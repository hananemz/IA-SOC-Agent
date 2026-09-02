# ==============================================================================
# Query Elasticsearch audit logs for access_denied (permission denied) events
# ==============================================================================

$EsUrl = "https://host.docker.internal:9200"
$Auth = "Basic " + [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("elastic:changeme"))
$Headers = @{ "Authorization" = $Auth; "Content-Type" = "application/json" }

# ------------------------------------------------------------------
# 1. All access_denied events in the last 24 hours
# ------------------------------------------------------------------
$Query = @{
  size = 50
  query = @{
    bool = @{
      filter = @(
        @{ "terms" = @{ "event.action" = @("access_denied", "anonymous_access_denied", "run_as_denied", "connection_denied") } },
        @{ "range" = @{ "@timestamp" = @{ "gte" = "now-24h" } } }
      )
    }
  }
  sort = @( @{ "@timestamp" = @{ "order" = "desc" } } )
} | ConvertTo-Json -Depth 5

Write-Host "`n=== Access Denied Events (last 24h) ===" -ForegroundColor Yellow
$Result = Invoke-RestMethod -Uri "$EsUrl/.security-audit-*/_search" -Method Post -Headers $Headers `
  -Body $Query -UseBasicParsing

Write-Host "Total hits: $($Result.hits.total.value)" -ForegroundColor Cyan

foreach ($hit in $Result.hits.hits) {
  $src = $hit._source
  Write-Host "`n  Time  : $($src.'@timestamp')"
  Write-Host "  Action: $($src.event.action)"
  Write-Host "  User  : $($src.user.name)"
  Write-Host "  IP    : $($src.source.ip)"
  if ($src.indices) { Write-Host "  Index : $($src.indices -join ', ')" }
  if ($src.rejected) { Write-Host "  Reason: $($src.rejected.privileges | ForEach-Object { $_.index + ':' + $_.privileges } | Sort-Object -Unique)" }
}

# ------------------------------------------------------------------
# 2. Summary by user
# ------------------------------------------------------------------
$AggQuery = @{
  size = 0
  query = @{
    bool = @{
      filter = @(
        @{ "terms" = @{ "event.action" = @("access_denied", "anonymous_access_denied") } },
        @{ "range" = @{ "@timestamp" = @{ "gte" = "now-24h" } } }
      )
    }
  }
  aggs = @{
    by_user = @{
      terms = @{ field = "user.name"; size = 20 }
    }
  }
} | ConvertTo-Json -Depth 5

Write-Host "`n=== Denial Count by User ===" -ForegroundColor Yellow
$AggResult = Invoke-RestMethod -Uri "$EsUrl/.security-audit-*/_search" -Method Post -Headers $Headers `
  -Body $AggQuery -UseBasicParsing

foreach ($bucket in $AggResult.aggregations.by_user.buckets) {
  Write-Host "  $($bucket.key): $($bucket.doc_count) denials"
}
