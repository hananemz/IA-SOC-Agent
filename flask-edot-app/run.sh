#!/usr/bin/env bash
set -euo pipefail

# 1. Créez un environnement virtuel (si pas encore fait)
python3 -m venv venv
source venv/bin/activate

# 2. Installez les dépendances
pip install -r requirements.txt

# 3. Installez les paquets d'instrumentation automatique
edot-bootstrap --action=install

# 4. Chargez les variables d'environnement depuis .env (si présent)
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# 5. Démarrez l'application avec opentelemetry-instrument (OBLIGATOIRE)
opentelemetry-instrument python app.py
