# Flask App instrumentée avec EDOT (Elastic Distribution of OpenTelemetry)

Application Python Flask envoyant **traces** et **logs** vers Elasticsearch via OpenTelemetry.

## Architecture

```
┌──────────────────┐         OTLP/HTTP          ┌──────────────────┐
│  Flask App       │ ─────────────────────────▶ │  Elasticsearch   │
│  + EDOT SDK      │   traces + logs + metrics  │  + Kibana        │
└──────────────────┘                            └──────────────────┘
```

Les instructions ici suivent les conventions suivantes :
- **Export** : OTLP direct vers l'endpoint OTLP d'Elasticsearch (pas d'APM Server ni Elastic Agent).
- **Config** : Seules les 3 variables `OTEL_*` requises, sans code SDK dans l'application.
- **Instrumentation** : `opentelemetry-instrument` obligatoire au démarrage.

---

## Prérequis

- Python 3.9+
- Un projet Elastic Cloud Serverless (Observability ou Elasticsearch)
- Une API Key Elastic Cloud avec accès en écriture aux indices

---

## Installation rapide

```bash
# 1. Créez un environnement virtuel
python -m venv venv
source venv/bin/activate        # Linux/macOS
# ou
.\venv\Scripts\Activate.ps1     # PowerShell / Windows

# 2. Installez les dépendances
pip install -r requirements.txt

# 3. Installez les instrumentations automatiques pour les bibliothèques détectées
edot-bootstrap --action=install
```

## Configuration

3 variables d'environnement sont obligatoires :

| Variable | Description | Exemple |
|---|---|---|
| `OTEL_SERVICE_NAME` | Nom du service dans Kibana | `mon-app-flask` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | **Endpoint OTLP** (pas URL APM Server) | `https://projete.xxx.us-east-1.aws.cloud.es.io:443` |
| `OTEL_EXPORTER_OTLP_HEADERS` | Auth (API Key ou Bearer token) | `Authorization=ApiKey <your-key>` |

Pour trouver votre **OTLP endpoint** :
1. Connectez-vous à Elastic Cloud → votre projet
2. Allez dans **Management → OpenTelemetry**
3. Copiez l'endpoint OTLP (format `https://...:443`)

Ne **pas** définir `OTEL_TRACES_EXPORTER`, `OTEL_METRICS_EXPORTER`, ou `OTEL_LOGS_EXPORTER` — les défauts sont déjà corrects.

Copiez `.env.example` vers `.env` et remplissez les valeurs :
```bash
cp .env.example .env
# Éditez .env avec vos credentials
```

## Démarrage

```bash
# PowerShell (Windows)
.\run.ps1

# Bash (Linux/macOS)
chmod +x run.sh
./run.sh

# Ou manuellement :
$env:OTEL_SERVICE_NAME="mon-app-flask"
$env:OTEL_EXPORTER_OTLP_ENDPOINT="https://votre-endpoint:443"
$env:OTEL_EXPORTER_OTLP_HEADERS="Authorization=ApiKey votre-key"
opentelemetry-instrument python app.py
```

⚠️ **Important** : Le lancement **doit** passer par `opentelemetry-instrument`. Sans ce wrapper, aucune télémétrie n'est collectée.

### Docker

```bash
docker build -t flask-edot .
docker run -p 5000:5000 \
  -e OTEL_SERVICE_NAME=flask-edot-app \
  -e OTEL_EXPORTER_OTLP_ENDPOINT=https://votre-endpoint:443 \
  -e OTEL_EXPORTER_OTLP_HEADERS="Authorization=ApiKey votre-key" \
  flask-edot
```

## Routes

| Méthode | Path | Description |
|---|---|---|
| GET | `/` | Page d'accueil |
| GET | `/health` | Probe de santé |
| GET | `/users` | Liste des utilistateurs |
| GET | `/users/<id>` | Détail d'un utilisateur |
| POST | `/users` | Créer un utilisateur |

## Vérifier dans Kibana

1. Ouvrez **Kibana → Observability → Traces**
2. Recherchez votre service par `OTEL_SERVICE_NAME`
3. Les logs apparaissent dans **Logs → Discover**
4. Les requêtes HTTP sont tracées automatiquement grâce aux instrumentations Flask/WSGI

---

## Architecture des fichiers

```
flask-edot-app/
├── app.py              # Application Flask (sans code SDK OTel)
├── requirements.txt    # Dépendances Python
├── .env.example        # Template variables d'environnement
├── run.ps1             # Script de démarrage PowerShell
├── run.sh              # Script de démarrage Bash
├── Dockerfile          # Image Docker pré-configurée
├── .gitignore          # Exclusions Git
└── README.md           # Ce fichier
```

## Notes

- **Pas de code OpenTelemetry dans `app.py`** — `opentelemetry-instrument` gère tout automatiquement.
- **JAMAIS** ne faites tourner `elastic-apm` et EDOT sur la même application.
- Les logs Python sont automatiquement corrélés aux traces via l'instrumentation logging OpenTelemetry.
