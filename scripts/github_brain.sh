#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="${BASE_DIR:-$HOME/GitHub}"
BRAIN_DIR="${BRAIN_DIR:-$HOME/.github_brain}"
ORG="${ORG:-}"
LIMIT="${LIMIT:-1000}"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Erreur: commande requise introuvable: $1" >&2
    exit 1
  fi
}

require_cmd gh
require_cmd jq
require_cmd git

mkdir -p "$BASE_DIR" "$BRAIN_DIR"

if [[ -n "$ORG" ]]; then
  repo_json=$(gh repo list "$ORG" --limit "$LIMIT" --json name,sshUrl,owner)
else
  repo_json=$(gh repo list --limit "$LIMIT" --json name,sshUrl,owner)
fi

echo "$repo_json" > "$BRAIN_DIR/repos.json"

echo "$repo_json" | jq -r '.[] | "\(.owner.login) \(.name) \(.sshUrl)"' | while read -r owner name ssh_url; do
  repo_path="$BASE_DIR/$owner/$name"
  if [[ -d "$repo_path/.git" ]]; then
    echo "Mise à jour: $owner/$name"
    git -C "$repo_path" pull --ff-only
  else
    echo "Clonage: $owner/$name"
    mkdir -p "$BASE_DIR/$owner"
    git clone "$ssh_url" "$repo_path"
  fi
done

{
  echo "date=$(date -Is)"
  echo "hostname=$(hostname)"
  echo "os=$(uname -a)"
  if command -v uptime >/dev/null 2>&1; then
    echo "uptime=$(uptime -p)"
  fi
  if command -v free >/dev/null 2>&1; then
    echo "memory"
    free -h
  fi
  echo "disk"
  df -h "$BASE_DIR"
} > "$BRAIN_DIR/system_status.txt"

echo "OK: dépôts synchronisés dans $BASE_DIR"
echo "OK: état système écrit dans $BRAIN_DIR/system_status.txt"
