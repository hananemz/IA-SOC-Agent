FROM python:3.12-slim

WORKDIR /app

# Copiez les dépendances et installez-les
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Installez les instrumentations automatiques pour les bibliothèques détectées
RUN edot-bootstrap --action=install

# Copiez le code de l'application
COPY . .

# Variables d'environnement OpenTelemetry
# Les valeurs réelles sont injectées au démarrage (Docker runtime ou orchestrateur)
ENV OTEL_SERVICE_NAME=flask-edot-app
ENV OTEL_EXPORTER_OTLP_ENDPOINT=""
ENV OTEL_EXPORTER_OTLP_HEADERS=""

EXPOSE 5000

# Lancement via opentelemetry-instrument (OBLIGATOIRE pour la collecte de télémétrie)
CMD ["opentelemetry-instrument", "python", "app.py"]
