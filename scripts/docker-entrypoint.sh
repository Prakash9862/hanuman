#!/bin/bash

export PYTHONPATH="/app/src"

echo "🚀 Lancement de l'API Hanuman dans le conteneur Docker"

# Lancer Uvicorn avec ou sans reload
exec poetry run uvicorn src.hanuman.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    ${RELOAD:+--reload}
