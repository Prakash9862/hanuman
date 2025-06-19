#!/bin/bash

echo "🔧 [Hanuman Dev] Reconstruction de l’image..."
docker compose down

echo "🐳 [Hanuman Dev] Build de l’image Docker (target = dev)..."
docker compose build

echo "🚀 [Hanuman Dev] Démarrage du conteneur..."
docker compose up
