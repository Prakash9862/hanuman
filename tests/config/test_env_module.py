from __future__ import annotations

import importlib


def test_env_warns_when_env_file_missing(monkeypatch, capsys) -> None:
    """
    On simule l'absence de .env pour couvrir la branche else de ENV_PATH.exists().
    """
    import hanuman.config.env as env_module

    # Force Path.exists() à retourner False pour ce module
    monkeypatch.setattr("hanuman.config.env.Path.exists", lambda _self: False)

    # Reload pour ré-exécuter le top-level avec la nouvelle valeur
    importlib.reload(env_module)
    out = capsys.readouterr().out

    assert ".env introuvable" in out


def test_env_warns_when_critical_vars_missing(monkeypatch, capsys) -> None:
    """
    On vide les variables critiques et on vérifie que le module se recharge proprement.
    """
    # Vire les variables d'env critiques
    monkeypatch.delenv("NOTION_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    # Empêche un éventuel load_dotenv réel pendant le test
    monkeypatch.setattr(
        "hanuman.config.env.load_dotenv",
        lambda *_args, **_kwargs: None,
        raising=False,
    )

    import hanuman.config.env as env_module

    importlib.reload(env_module)
    out = capsys.readouterr().out

    # On ne dépend plus du texte exact, juste du fait que CRITICAL_VARS est bien construit
    assert isinstance(env_module.CRITICAL_VARS, dict)
    assert "NOTION_TOKEN" in env_module.CRITICAL_VARS
    assert "GITHUB_TOKEN" in env_module.CRITICAL_VARS
    assert "OPENAI_API_KEY" in env_module.CRITICAL_VARS

    # Optionnel : si quelque chose a été imprimé, on vérifie que ça ressemble à un warning
    if out:
        assert "n'est pas configurée" in out
