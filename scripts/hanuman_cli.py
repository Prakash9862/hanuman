#!/usr/bin/env python3
import json

import requests

BASE_URL = "http://127.0.0.1:8000"


def send_one(path: str):
    data = {"path": path}
    r = requests.post(f"{BASE_URL}/obsidian/sync_one", json=data)
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))


def send_many(paths: list[str]):
    data = {"paths": paths}
    r = requests.post(f"{BASE_URL}/obsidian/sync_many", json=data)
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    # Exemple : envoie un seul fichier
    send_one("Privé/Entre Orient et Occident/Nana.md")

    # Exemple : pour plusieurs fichiers, décommente ci-dessous
    # send_many([
    #     "Privé/Entre Orient et Occident/Nana.md",
    #     "Privé/Entre Orient et Occident/Journal.md"
    # ])
