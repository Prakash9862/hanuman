from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any, Literal

from hanuman.models.chess_insight import (
    CHESS_INSIGHT_SCHEMA_VERSION,
    ChessInsightEnvelope,
)
from hanuman.services.atomic_write_service import atomic_write_text
from hanuman.services.chess_analysis_service import (
    AnalysisConfig,
    GameAnalysis,
    StockfishAnalyzer,
)
from hanuman.services.chess_insight_service import build_chess_insights
from hanuman.services.chess_insight_storage_service import (
    inject_insight_block,
    parse_chess_note_insight_metadata,
)
from hanuman.services.chess_path_safety_service import resolve_safe_destination
from hanuman.services.delimited_zone_service import (
    DelimitedZoneError,
    replace_delimited_zone,
)

CHESS_USERNAME = os.environ.get("CHESS_COM_USERNAME", "").strip()
if not CHESS_USERNAME:
    raise RuntimeError("CHESS_COM_USERNAME manquant dans l'environnement")

PGN_PATTERN = re.compile(r"```pgn\s*(.*?)```", re.DOTALL | re.IGNORECASE)
START_MARKER = "<!-- HANUMAN_CHESS_ANALYSIS_START -->"
END_MARKER = "<!-- HANUMAN_CHESS_ANALYSIS_END -->"
LEGACY_ANALYSIS_PATTERN = re.compile(r"\n## Analyse personnelle\s*.*\Z", re.DOTALL)


class ChessAnalysisBlockError(ValueError):
    """Signale des marqueurs d’analyse visibles ambigus."""


def _vault_root() -> Path:
    configured = os.environ.get("OBSIDIAN_VAULT_PATH")
    if configured:
        return Path(configured).expanduser()
    return Path("/home/vince/Prakash/projets/Obsidian_Priv-")


def _chess_root() -> Path:
    configured = os.environ.get("CHESS_OBSIDIAN_PATH")
    if configured:
        return Path(configured).expanduser()
    return _vault_root() / "Echecs"


def _validated_chess_root() -> Path:
    root = _chess_root()
    return resolve_safe_destination(root, root)


def extract_pgn(markdown: str) -> str | None:
    match = PGN_PATTERN.search(markdown)
    if not match:
        return None

    raw_pgn = match.group(1).strip()

    # Les PGN importés dans Obsidian peuvent être placés dans une citation
    # Markdown, ce qui préfixe chaque ligne par "> ". Ce préfixe ne fait pas
    # partie du format PGN et doit être retiré avant le parsing python-chess.
    cleaned_lines = [re.sub(r"^\s*>\s?", "", line) for line in raw_pgn.splitlines()]

    return "\n".join(cleaned_lines).strip()


def _move_label(move: Any) -> str:
    separator = "." if move.color == "white" else "..."
    return f"{move.move_number}{separator}{move.san}{move.annotation}"


def _format_eval(value_cp: int) -> str:
    return f"{value_cp / 100:+.2f}"


def _player_color(analysis: GameAnalysis) -> Literal["white", "black"]:
    if analysis.white.lower() == CHESS_USERNAME.lower():
        return "white"
    if analysis.black.lower() == CHESS_USERNAME.lower():
        return "black"
    raise ValueError(f"{CHESS_USERNAME} absent de la partie")


def _player_moves(analysis: GameAnalysis) -> list[Any]:
    color = _player_color(analysis)
    return [move for move in analysis.moves if move.color == color]


def _opponent_moves(analysis: GameAnalysis) -> list[Any]:
    color = _player_color(analysis)
    return [move for move in analysis.moves if move.color != color]


def _player_critical(analysis: GameAnalysis) -> list[Any]:
    return [
        move
        for move in _player_moves(analysis)
        if move.classification in {"blunder", "mistake", "dubious", "excellent"}
        or move.missed_excellent
    ]


def _opponent_highlights(analysis: GameAnalysis) -> list[Any]:
    return [
        move
        for move in _opponent_moves(analysis)
        if move.classification == "blunder" or move.excellent
    ]


def _counts(moves: list[Any]) -> dict[str, int]:
    return {
        "blunders": sum(move.classification == "blunder" for move in moves),
        "mistakes": sum(move.classification == "mistake" for move in moves),
        "dubious": sum(move.classification == "dubious" for move in moves),
        "excellent": sum(move.excellent for move in moves),
        "missed_excellent": sum(move.missed_excellent for move in moves),
    }


def _average_loss(moves: list[Any]) -> float:
    return round(sum(move.loss_cp for move in moves) / len(moves), 1) if moves else 0.0


def _turning_label(analysis: GameAnalysis) -> str:
    if analysis.turning_point_ply is None:
        return "aucune bascule détectée"
    move = next(
        (item for item in analysis.moves if item.ply == analysis.turning_point_ply),
        None,
    )
    return (
        _move_label(move)
        if move is not None
        else f"demi-coup {analysis.turning_point_ply}"
    )


def _quality(move: Any) -> str:
    quality = move.annotation or "—"
    if move.missed_excellent and not move.excellent:
        return f"{quality} · occasion manquée" if quality != "—" else "occasion manquée"
    return quality


def render_analysis_markdown(analysis: GameAnalysis) -> str:
    player_moves = _player_moves(analysis)
    critical = _player_critical(analysis)
    opponent = _opponent_highlights(analysis)
    counts = _counts(player_moves)
    worst = max(player_moves, key=lambda item: item.loss_cp, default=None)

    lines = [
        START_MARKER,
        "## Analyse Stockfish",
        "",
        "### Ton bilan",
        "",
        f"- **Moteur :** {analysis.engine}",
        f"- **Profondeur :** {analysis.depth}",
        f"- **Perte moyenne :** {_average_loss(player_moves)} cp par coup joué",
        f"- **Pire coup :** {_move_label(worst) if worst is not None else '—'}",
        f"- **Moment de bascule :** {_turning_label(analysis)}",
        "",
        "| Qualité | Nombre |",
        "|---|---:|",
        f"| `??` Gaffes | {counts['blunders']} |",
        f"| `?` Erreurs | {counts['mistakes']} |",
        f"| `?!` Coups douteux | {counts['dubious']} |",
        f"| `!!` Excellents coups | {counts['excellent']} |",
        f"| Excellents coups manqués | {counts['missed_excellent']} |",
        "",
        "### Tes coups critiques",
        "",
    ]

    if not critical:
        lines.append("Aucun de tes coups ne franchit les seuils critiques actuels.")
    else:
        lines.extend(
            [
                "| Coup | Qualité | Éval. avant | Éval. après | Perte | Meilleur coup |",
                "|---|:---:|---:|---:|---:|---|",
            ]
        )
        for move in critical:
            best = f"`{move.best_move_san}`" if move.best_move_san else "—"
            lines.append(
                f"| **{_move_label(move)}** | {_quality(move)} | "
                f"{_format_eval(move.eval_before_cp)} | {_format_eval(move.eval_after_cp)} | "
                f"{move.loss_cp} cp | {best} |"
            )

    lines.extend(["", "### Variantes critiques", ""])
    variants = [move for move in critical if move.principal_variation]
    if not variants:
        lines.append("Aucune variante critique disponible.")
    else:
        for move in variants:
            lines.extend(
                [
                    f"#### {_move_label(move)}",
                    "",
                    f"- **Meilleur coup :** `{move.best_move_san or '—'}`",
                    f"- **Perte :** {move.loss_cp} cp",
                    f"- **Phase :** {'ouverture' if move.opening_phase else 'milieu ou finale'}",
                    "",
                    "```text",
                    " ".join(move.principal_variation),
                    "```",
                    "",
                ]
            )

    lines.extend(["### Faits marquants de l’adversaire", ""])
    if not opponent:
        lines.append("Aucune gaffe ni coup excellent adverse détecté.")
    else:
        for move in opponent:
            description = (
                "gaffe" if move.classification == "blunder" else "coup excellent"
            )
            best = f" · meilleur : `{move.best_move_san}`" if move.best_move_san else ""
            lines.append(
                f"- **{_move_label(move)}** — {description}, perte {move.loss_cp} cp{best}"
            )

    lines.extend(
        [
            "",
            "### Seuils utilisés",
            "",
            "- `??` : perte d’au moins 200 cp",
            "- `?` : perte de 100 à 199 cp",
            "- `?!` : perte de 50 à 99 cp",
            "- `!!` : coup quasi unique, tactique ou sacrifice correct détecté avec forte confiance",
            "",
            END_MARKER,
        ]
    )
    return "\n".join(lines)


def inject_analysis(markdown: str, rendered: str) -> str:
    try:
        updated = replace_delimited_zone(
            markdown,
            rendered,
            START_MARKER,
            END_MARKER,
            label="d’analyse Chess",
        )
    except DelimitedZoneError as exc:
        raise ChessAnalysisBlockError(str(exc)) from exc
    if updated is not None:
        return updated
    without_legacy = LEGACY_ANALYSIS_PATTERN.sub("", markdown).rstrip()
    return without_legacy + "\n\n" + rendered + "\n"


def analyse_note(
    path: Path,
    analyzer: StockfishAnalyzer,
    *,
    root: Path | None = None,
) -> GameAnalysis | None:
    safe_path = resolve_safe_destination(root or path.parent, path)
    markdown = safe_path.read_text(encoding="utf-8")
    pgn = extract_pgn(markdown)
    if not pgn:
        return None
    analysis = analyzer.analyse_pgn(pgn)
    metadata = parse_chess_note_insight_metadata(markdown)
    player_color = metadata.player_color or _player_color(analysis)
    game_id = metadata.game_id
    eco = metadata.eco or analysis.eco
    insights = build_chess_insights(
        analysis,
        player_color=player_color,
        game_id=game_id,
        eco=eco,
    )
    envelope = ChessInsightEnvelope(
        schema_version=CHESS_INSIGHT_SCHEMA_VERSION,
        game_id=game_id,
        eco=eco,
        insights=insights,
        analysis_metadata=analysis.analysis_metadata(),
        opening_exit=(
            None
            if analysis.opening_exit is None
            else {
                "ply": analysis.opening_exit.ply,
                "move_number": analysis.opening_exit.move_number,
                "side_to_move": analysis.opening_exit.side_to_move,
                "last_move_san": analysis.opening_exit.last_move_san,
                "last_move_uci": analysis.opening_exit.last_move_uci,
                "fen": analysis.opening_exit.fen,
                "evaluation_value": analysis.opening_exit.evaluation_value,
                "evaluation_type": analysis.opening_exit.evaluation_type,
                "evaluation_perspective": analysis.opening_exit.evaluation_perspective,
                "depth_reached": analysis.opening_exit.depth_reached,
                "principal_variation": analysis.opening_exit.principal_variation,
            }
        ),
    )
    with_analysis = inject_analysis(markdown, render_analysis_markdown(analysis))
    atomic_write_text(
        safe_path,
        inject_insight_block(with_analysis, envelope),
    )
    return analysis


def _game_paths(root: Path) -> list[Path]:
    paths = list(root.glob("[0-9][0-9][0-9][0-9]/[0-9][0-9]/*.md"))
    return sorted(paths, key=lambda path: path.name, reverse=True)


def analyse_vault(limit: int | None = None, depth: int = 18) -> dict[str, Any]:
    root = _validated_chess_root()
    if not root.exists():
        raise FileNotFoundError(f"Dossier Echecs introuvable : {root}")

    paths = _game_paths(root)
    if limit is not None:
        paths = paths[:limit]

    config = AnalysisConfig(
        engine_path=os.environ.get("STOCKFISH_PATH"),
        depth=depth,
        player_name=CHESS_USERNAME,
    )
    analysed = 0
    skipped = 0
    failed: list[dict[str, str]] = []
    with StockfishAnalyzer(config) as analyzer:
        for path in paths:
            try:
                analysis = analyse_note(path, analyzer, root=root)
                if analysis is None:
                    skipped += 1
                else:
                    analysed += 1
            except Exception as exc:
                failed.append({"path": str(path), "error": str(exc)})

    return {
        "status": "ok" if not failed else "partial",
        "root": str(root),
        "analysed": analysed,
        "skipped": skipped,
        "failed": failed,
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Ajoute l’analyse Stockfish dans les notes chronologiques"
    )
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--depth", type=int, default=18)
    args = parser.parse_args(argv)
    result = analyse_vault(limit=args.limit, depth=args.depth)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
