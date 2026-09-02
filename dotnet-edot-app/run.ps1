# EDOT .NET - Script de démarrage PowerShell
# Variables d'environnement OpenTelemetry
$env:OTEL_SERVICE_NAME="mon-app-dotnet"
$env:OTEL_EXPORTER_OTLP_ENDPOINT="https://votre-endpoint-otlp:443"
$env:OTEL_EXPORTER_OTLP_HEADERS="Authorization=ApiKey votre-api-key"

# Remplacez la version du package NuGet avant de construire
# ⚠️ La version dans csproj est un placeholder non vérifié
dotnet restore
dotnet run --project dotnet-edot-app.csproj
