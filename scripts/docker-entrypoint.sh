#!/bin/bash

echo "🚀 Lancement de l'API Hanuman dans le conteneur Docker"

# Tu peux ici détecter le mode si tu veux :
# [ "$APP_ENV" = "prod" ] && echo "MODE PROD" || echo "MODE DEV"

# Lancer Uvicorn avec ou sans reload
exec poetry run uvicorn src.hanuman.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    ${RELOAD:+--reload}
