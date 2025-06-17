# src/hanuman/utils/log_helpers.py

from fastapi import Request


def get_ip(request: Request | None) -> str:
    """
    Récupère l'adresse IP du client si possible.
    Retourne "no-request" si la requête est absente,
    "no-client" si le client est introuvable.
    """
    if request is None:
        return "no-request"
    if request.client is None:
        return "no-client"
    return request.client.host


def get_method(request: Request | None) -> str:
    """
    Récupère la méthode HTTP de la requête.
    """
    return request.method if request else "unknown"


def get_path(request: Request | None) -> str:
    """
    Récupère le chemin de la requête.
    """
    return request.url.path if request else "unknown"
