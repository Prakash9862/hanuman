from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any

THEME_NAME = "hanuman-chess"
GRAPH_GROUPS = [
    {"query": "path:Echecs/Dashboard", "color": {"a": 1, "rgb": 14070603}},
    {"query": "path:Echecs/_Index/Annees", "color": {"a": 1, "rgb": 6866904}},
    {"query": "path:Echecs/_Index/Mois", "color": {"a": 1, "rgb": 11044567}},
    {"query": "path:Echecs/_Index/Ouvertures", "color": {"a": 1, "rgb": 14051946}},
    {"query": "path:Echecs/_Index/Adversaires", "color": {"a": 1, "rgb": 6534268}},
    {"query": "tag:#chess/analysis/analysed", "color": {"a": 1, "rgb": 5814416}},
    {"query": "tag:#chess/analysis/pending", "color": {"a": 1, "rgb": 14197719}},
    {
        "query": "path:Echecs -path:Echecs/_Index -path:Echecs/Dashboard",
        "color": {"a": 1, "rgb": 5814448},
    },
]
HANUMAN_GRAPH_QUERIES = {str(group["query"]) for group in GRAPH_GROUPS}


def _vault_root() -> Path:
    configured = os.environ.get("OBSIDIAN_VAULT_PATH")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path("/home/vince/Prakash/projets/Obsidian_Priv-").expanduser().resolve()


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _install_graph_groups(path: Path) -> None:
    graph = _read_json(path)
    current = graph.get("colorGroups", [])
    if not isinstance(current, list):
        current = []

    preserved = [
        item
        for item in current
        if isinstance(item, dict) and str(item.get("query", "")) not in HANUMAN_GRAPH_QUERIES
    ]
    graph["colorGroups"] = [*GRAPH_GROUPS, *preserved]
    graph.setdefault("showTags", True)
    graph.setdefault("showAttachments", False)
    graph.setdefault("showOrphans", False)
    _write_json(path, graph)


def install() -> dict[str, str]:
    vault = _vault_root()
    source = _project_root() / "assets" / "obsidian" / f"{THEME_NAME}.css"
    if not source.exists():
        raise FileNotFoundError(f"Snippet source introuvable : {source}")
    if not vault.exists():
        raise FileNotFoundError(f"Vault Obsidian introuvable : {vault}")

    obsidian_dir = vault / ".obsidian"
    snippets_dir = obsidian_dir / "snippets"
    snippets_dir.mkdir(parents=True, exist_ok=True)

    destination = snippets_dir / source.name
    shutil.copy2(source, destination)

    appearance_path = obsidian_dir / "appearance.json"
    appearance = _read_json(appearance_path)
    enabled = appearance.get("enabledCssSnippets", [])
    if not isinstance(enabled, list):
        enabled = []
    enabled_names = [str(item) for item in enabled]
    if THEME_NAME not in enabled_names:
        enabled_names.append(THEME_NAME)
    appearance["enabledCssSnippets"] = enabled_names
    _write_json(appearance_path, appearance)

    graph_path = obsidian_dir / "graph.json"
    local_graph_path = obsidian_dir / "local-graph.json"
    _install_graph_groups(graph_path)
    _install_graph_groups(local_graph_path)

    return {
        "status": "ok",
        "vault": str(vault),
        "snippet": str(destination),
        "appearance": str(appearance_path),
        "graph": str(graph_path),
        "local_graph": str(local_graph_path),
        "enabled": THEME_NAME,
    }


if __name__ == "__main__":
    print(install())
