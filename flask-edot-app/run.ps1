# 1. Créez un environnement virtuel (si pas encore fait)
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. Installez les dépendances
pip install -r requirements.txt

# 3. Installez les paquets d'instrumentation automatique pour les bibliothèques détectées
edot-bootstrap --action=install

# 4. Configurez les variables d'environnement
$env:OTEL_SERVICE_NAME="mon-app-flask"
$env:OTEL_EXPORTER_OTLP_ENDPOINT="https://votre-endpoint-otlp:443"
$env:OTEL_EXPORTER_OTLP_HEADERS="Authorization=ApiKey votre-api-key"

# 5. Démarrez l'application avec opentelemetry-instrument (OBLIGATOIRE)
opentelemetry-instrument python app.py
