from __future__ import annotations

import argparse
import datetime as dt
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

from hanuman.core.config import settings  # config Pydantic (chess_com_username)
from hanuman.services.core.chess_service import ChessService


# =========================
#  Modèle de données
# =========================


@dataclass
class ChessGame:
    game_id: str
    end_time: dt.datetime
    white: str
    black: str
    result: str  # "win" / "loss" / "draw"
    color: str  # "white" / "black" (ton point de vue)
    opening_name: str
    eco: str
    time_control: str  # "blitz", "rapid", etc.
    url: str


# =========================
#  Helpers
# =========================


def _slugify(value: str) -> str:
    """Transforme une chaîne en nom de fichier safe."""
    return (
        value.lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("–", "-")
        .replace("—", "-")
    )
def _build_opening_key(game: ChessGame) -> str:
    """Construit une clé d'ouverture propre à partir d'une partie.

    - Normalise l'ECO (C20, D02, etc.)
    - Nettoie le nom d'ouverture
    - Évite les doublons du type 'C20 C20'
    """
    eco = (game.eco or "").strip().upper()
    name = (game.opening_name or "").strip()

    # Si pas de nom → on tombe au moins sur l'ECO ou "Unknown"
    if not name:
        name = eco or "Unknown"

    # Si le nom est exactement l'ECO (ex: "C20"), on ne double pas
    if eco and name.upper() != eco:
        return f"{eco} {name}"

    # Sinon : juste le nom (qui peut être "C20" ou un vrai nom)
    return name


def _group_by_opening(games: Iterable[ChessGame]) -> Dict[str, List[ChessGame]]:
    """Regroupe les parties par clé d’ouverture (ECO + nom nettoyés)."""
    groups: Dict[str, List[ChessGame]] = {}
    for g in games:
        key = _build_opening_key(g)
        groups.setdefault(key, []).append(g)
    return groups



def _format_game_line(game: ChessGame) -> str:
    """Formate une ligne du tableau Markdown pour une partie avec tags Obsidian."""
    date = game.end_time.strftime("%Y-%m-%d")
    res_symbol = {"win": "✅", "loss": "❌", "draw": "½"}.get(game.result, "?")

    # Tags pour la vue graphique
    color_tag = "#white" if game.color == "white" else "#black"
    result_tag_map = {"win": "#win", "loss": "#loss", "draw": "#draw"}
    result_tag = result_tag_map.get(game.result, "")

    tc_tag = f"#tc/{game.time_control}" if game.time_control else ""

    opponent = game.white if game.color == "black" else game.black

    # Affichage ECO + nom d’ouverture
    eco = (game.eco or "").strip()
    opening_name = (game.opening_name or "").strip()

    if eco and opening_name:
        opening_cell = f"`{eco}` {opening_name}"
    elif eco:
        opening_cell = f"`{eco}`"
    elif opening_name:
        opening_cell = opening_name
    else:
        opening_cell = "—"

    return (
        f"| {date} | {color_tag} | {res_symbol} {result_tag} | "
        f"{tc_tag or game.time_control} | {opening_cell} | "
        f"vs **{opponent}** | [Lien]({game.url}) |"
    )





def _split_opening_key(opening_key: str) -> tuple[str, str]:
    """Sépare 'ECO Nom' en (ECO, Nom)."""
    if " " in opening_key:
        eco, name = opening_key.split(" ", 1)
    else:
        eco, name = "", opening_key
    return eco, name


def _build_opening_note(opening_key: str, games: List[ChessGame]) -> str:
    """Construit le contenu Markdown pour une ouverture donnée."""
    eco, name = _split_opening_key(opening_key)

    # 🔁 Fallback : si l'ECO est vide, on le prend sur la première partie
    if not eco and games:
        eco = (games[0].eco or "").strip().upper()

    # 🔁 Fallback : si le nom est vide, on prend au moins l'ECO ou la clé
    if not name:
        name = eco or opening_key

    tags: List[str] = ["#chess", "#ouverture"]
    if eco:
        tags.append(f"#eco/{eco}")

    title = f"{eco} {name}" if eco and eco not in name else name

    header_lines: List[str] = [
        "---",
        f'title: "{title}"',
        f"eco: {eco!r}",
        "tags:",
        *[f"  - {t}" for t in tags],
        f"games_count: {len(games)}",
        "---",
        "",
        f"# {title}",
        "",
    ]


    if eco:
        header_lines.append(f"**ECO**: `{eco}`")
        header_lines.append("")

    header_lines.extend(
    [
        "## Parties liées",
        "",
        "| Date | Couleur | Résultat | Cadence | ECO / Ouverture | Adversaire | Lien |",
        "|------|---------|----------|---------|------------------|------------|------|",
    ]
)


    lines: List[str] = header_lines.copy()

    # Tri par date décroissante
    for g in sorted(games, key=lambda x: x.end_time, reverse=True):
        lines.append(_format_game_line(g))

    lines.append("")
    lines.append("## Notes personnelles")
    lines.append("")
    lines.append("> Ajoute ici tes idées, plans, erreurs récurrentes, etc.")
    lines.append("")

    return "\n".join(lines)


def _build_overview_note(groups: Mapping[str, List[ChessGame]]) -> str:
    """Construit la note Overview.md (vue globale des ouvertures)."""
    lines: List[str] = [
        "---",
        'title: "Chess Openings Overview"',
        "tags:",
        "  - #chess",
        "  - #overview",
        f"openings_count: {len(groups)}",
        "---",
        "",
        "# Vue d’ensemble des ouvertures",
        "",
        "| Ouverture | Parties | Dernière partie | Fichier |",
        "|----------|---------|-----------------|---------|",
    ]

    # Tri par nombre de parties décroissant
    for opening_key, games in sorted(
        groups.items(), key=lambda item: len(item[1]), reverse=True
    ):
        eco, name = _split_opening_key(opening_key)
        last_game = max(games, key=lambda g: g.end_time)
        date_str = last_game.end_time.strftime("%Y-%m-%d")
        slug = _slugify(opening_key)
        note_name = f"{slug}.md"
        display_name = f"{opening_key} ({len(games)} parties)"

        lines.append(
            f"| [[Openings/{note_name}|{display_name}]] | "
            f"{len(games)} | {date_str} | `Openings/{note_name}` |"
        )

    lines.append("")
    lines.append("## Idées")
    lines.append("")
    lines.append("- Focalise-toi sur les ouvertures avec le plus de défaites.")
    lines.append("- Repère les schémas qui se répètent.")
    lines.append("")

    return "\n".join(lines)


# =========================
#  Orchestration principale
# =========================


def sync_chess_to_obsidian(limit: int = 200) -> None:
    """
    Orchestration principale.

    - Récupère les parties Chess.com
    - Regroupe par ouverture
    - Écrit / met à jour les notes Obsidian dans le dossier Echecs.
    """
    chess_username = settings.chess_com_username  # à définir dans ta config
    obsidian_root = Path("/home/prakash/Prakash/obsidian/Echecs")
    openings_dir = obsidian_root / "Openings"

    # S'assure que les dossiers existent
    obsidian_root.mkdir(parents=True, exist_ok=True)
    openings_dir.mkdir(parents=True, exist_ok=True)

    chess = ChessService()

    # TODO: adapte le nom de méthode à ton service réel
    raw_games: List[Dict[str, Any]] = chess.get_latest_games(
        username=chess_username,
        limit=limit,
    )

    games: List[ChessGame] = []
    for g in raw_games:
        # ICI: adapte aux champs renvoyés par ChessService
        try:
            games.append(
                ChessGame(
                    game_id=g["id"],
                    end_time=g["end_time"],
                    white=g["white"],
                    black=g["black"],
                    result=g["result"],  # "win" / "loss" / "draw" (normalisé côté service)
                    color=g["color"],  # "white" / "black" pour TOI
                    opening_name=g["opening_name"],
                    eco=g.get("eco", ""),
                    time_control=g.get("time_control", ""),
                    url=g.get("url", ""),
                )
            )
        except KeyError:
            # Si une partie est incomplète, on l'ignore
            continue

    groups = _group_by_opening(games)

    # 1) Notes par ouverture
    for opening_key, ogames in groups.items():
        slug = _slugify(opening_key)
        note_path = openings_dir / f"{slug}.md"
        note_path.parent.mkdir(parents=True, exist_ok=True)
        content = _build_opening_note(opening_key, ogames)
        note_path.write_text(content, encoding="utf-8")

    # 2) Note d’overview
    overview_path = obsidian_root / "Overview.md"
    overview_content = _build_overview_note(groups)
    overview_path.parent.mkdir(parents=True, exist_ok=True)
    overview_path.write_text(overview_content, encoding="utf-8")

    # 3) Feedback console
    print(
        f"[chess→obsidian] {len(games)} parties traitées, "
        f"{len(groups)} ouvertures, notes écrites dans {obsidian_root}"
    )


# =========================
#  CLI
# =========================


def build_parser() -> argparse.ArgumentParser:
    """CLI pour l'orchestration Chess.com → Obsidian."""
    parser = argparse.ArgumentParser(
        prog="hanuman.orchestrations.chess_to_obsidian",
        description="Synchronise les parties Chess.com dans le vault Obsidian (dossier Echecs).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=200,
        help="Nombre maximum de parties à récupérer sur Chess.com",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """Point d'entrée CLI.

    Exemple :
        poetry run python -m hanuman.orchestrations.chess_to_obsidian --limit 50
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    sync_chess_to_obsidian(limit=args.limit)


if __name__ == "__main__":
    main()
