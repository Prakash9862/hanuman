from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from hanuman.services.chess_analysis_service import AnalysisConfig, GameAnalysis, analyse_pgn

PGN_PATTERN = re.compile(r"```pgn\s*(.*?)```", re.DOTALL | re.IGNORECASE)
START_MARKER = "<!-- HANUMAN_CHESS_ANALYSIS_START -->"
END_MARKER = "<!-- HANUMAN_CHESS_ANALYSIS_END -->"


def _vault_root() -> Path:
    configured = os.environ.get("OBSIDIAN_VAULT_PATH")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path("/home/vince/Prakash/projets/Obsidian_Priv").resolve()


def _chess_root() -> Path:
    configured = os.environ.get("CHESS_OBSIDIAN_PATH")
    if configured:
        return Path(configured).expanduser().resolve()
    return _vault_root() / "Echecs"


def extract_pgn(markdown: str) -> str | None:
    match = PGN_PATTERN.search(markdown)
    return match.group(1).strip() if match else None


def quality_tags(analysis: GameAnalysis) -> list[str]:
    tags: list[str] = []
    mapping = {
        "blunders": "chess/quality/blunder",
        "mistakes": "chess/quality/mistake",
        "dubious": "chess/quality/dubious",
        "excellent": "chess/quality/excellent",
        "missed_excellent": "chess/quality/missed-excellent",
    }
    for key, tag in mapping.items():
        if analysis.counts.get(key, 0):
            tags.append(tag)
    return tags


def _move_label(move: Any) -> str:
    separator = "." if move.color == "white" else "..."
    return f"{move.move_number}{separator}{move.san}{move.annotation}"


def render_analysis_markdown(analysis: GameAnalysis) -> str:
    critical = [
        move
        for move in analysis.moves
        if move.classification in {"blunder", "mistake", "excellent"}
        or move.missed_excellent
    ]
    lines = [
        START_MARKER,
        "## Analyse Hanuman / Stockfish",
        "",
        f"- **Moteur :** {analysis.engine}",
        f"- **Profondeur :** {analysis.depth}",
        f"- **Perte moyenne :** {analysis.average_centipawn_loss} cp/coup",
        f"- **Pire coup :** {analysis.worst_move or '—'}",
        f"- **Gaffes `??` :** {analysis.counts['blunders']}",
        f"- **Erreurs `?` :** {analysis.counts['mistakes']}",
        f"- **Coups douteux `?!` :** {analysis.counts['dubious']}",
        f"- **Excellents `!!` :** {analysis.counts['excellent']}",
        f"- **Excellents coups manqués :** {analysis.counts['missed_excellent']}",
        "",
        "### Moments critiques",
        "",
    ]
    if not critical:
        lines.append("- Aucun moment critique détecté avec les seuils actuels.")
    for move in critical:
        detail = f"perte {move.loss_cp} cp"
        if move.excellent:
            detail = "coup excellent détecté"
        elif move.missed_excellent:
            detail += " · occasion tactique forte manquée"
        best = f" · meilleur : `{move.best_move_san}`" if move.best_move_san else ""
        opening = " · phase d’ouverture" if move.opening_phase else ""
        lines.append(f"- **{_move_label(move)}** — {detail}{best}{opening}")
    lines.extend(["", END_MARKER])
    return "\n".join(lines)


def inject_analysis(markdown: str, rendered: str) -> str:
    if START_MARKER in markdown and END_MARKER in markdown:
        before, rest = markdown.split(START_MARKER, 1)
        _, after = rest.split(END_MARKER, 1)
        return before.rstrip() + "\n\n" + rendered + after
    return markdown.rstrip() + "\n\n" + rendered + "\n"


def analyse_note(path: Path, config: AnalysisConfig) -> GameAnalysis | None:
    markdown = path.read_text(encoding="utf-8")
    pgn = extract_pgn(markdown)
    if not pgn:
        return None
    analysis = analyse_pgn(pgn, config)
    rendered = render_analysis_markdown(analysis)
    path.write_text(inject_analysis(markdown, rendered), encoding="utf-8")
    sidecar = path.with_suffix(".analysis.json")
    sidecar.write_text(
        json.dumps(analysis.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return analysis


def _quality_note(label: str, symbol: str, description: str) -> str:
    return f'''---
type: chess-quality
symbol: "{symbol}"
tags:
  - chess/quality
---

# {symbol} — {label}

{description}

## Parties liées

Les parties analysées portent des tags techniques stables dans leurs fichiers JSON et leurs résumés Hanuman.
'''


def write_quality_nodes(root: Path) -> None:
    quality_root = root / "Qualite"
    quality_root.mkdir(parents=True, exist_ok=True)
    nodes = {
        "Gaffe.md": ("Gaffe", "??", "Perte d’au moins 200 centipions par rapport au meilleur coup."),
        "Erreur.md": ("Erreur", "?", "Perte comprise entre 100 et 199 centipions."),
        "Douteux.md": ("Douteux", "?!", "Perte comprise entre 50 et 99 centipions."),
        "Excellent.md": ("Excellent", "!!", "Coup unique, tactique ou sacrifice correct détecté avec forte confiance."),
        "Excellent manque.md": ("Excellent coup manqué", "!!?", "Occasion tactique forte non jouée."),
    }
    for filename, values in nodes.items():
        (quality_root / filename).write_text(_quality_note(*values), encoding="utf-8")


def write_summary(root: Path, analyses: list[GameAnalysis]) -> None:
    counts: Counter[str] = Counter()
    by_eco: dict[str, Counter[str]] = defaultdict(Counter)
    for analysis in analyses:
        counts.update(analysis.counts)
        by_eco[analysis.eco].update(analysis.counts)

    rows = []
    for eco, values in sorted(by_eco.items(), key=lambda item: -item[1]["blunders"]):
        rows.append(
            f"| {eco} | {values['blunders']} | {values['mistakes']} | "
            f"{values['dubious']} | {values['excellent']} | {values['missed_excellent']} |"
        )

    summary = f'''---
type: chess-analysis-dashboard
tags:
  - chess/dashboard
  - chess/analysis
---

# Analyse Stockfish — synthèse

- **Parties analysées :** {len(analyses)}
- **Gaffes `??` :** {counts['blunders']}
- **Erreurs `?` :** {counts['mistakes']}
- **Douteux `?!` :** {counts['dubious']}
- **Excellents `!!` :** {counts['excellent']}
- **Excellents coups manqués :** {counts['missed_excellent']}

## Qualité des coups

- [[Qualite/Gaffe|?? Gaffe]]
- [[Qualite/Erreur|? Erreur]]
- [[Qualite/Douteux|?! Douteux]]
- [[Qualite/Excellent|!! Excellent]]
- [[Qualite/Excellent manque|Excellent coup manqué]]

## Répartition par ECO

| ECO | ?? | ? | ?! | !! | excellents manqués |
|---|---:|---:|---:|---:|---:|
{chr(10).join(rows)}
'''
    (root / "Analyse Stockfish.md").write_text(summary, encoding="utf-8")


def analyse_vault(limit: int | None = None, depth: int = 18) -> dict[str, Any]:
    root = _chess_root()
    parties = root / "Parties"
    if not parties.exists():
        raise FileNotFoundError(f"Dossier de parties introuvable : {parties}")

    config = AnalysisConfig(
        engine_path=os.environ.get("STOCKFISH_PATH"),
        depth=depth,
    )
    paths = sorted(parties.rglob("*.md"), reverse=True)
    if limit is not None:
        paths = paths[:limit]

    analyses: list[GameAnalysis] = []
    skipped = 0
    failed: list[dict[str, str]] = []
    for path in paths:
        try:
            analysis = analyse_note(path, config)
            if analysis is None:
                skipped += 1
            else:
                analyses.append(analysis)
        except Exception as exc:
            failed.append({"path": str(path), "error": str(exc)})

    write_quality_nodes(root)
    write_summary(root, analyses)
    return {
        "status": "ok" if not failed else "partial",
        "root": str(root),
        "analysed": len(analyses),
        "skipped": skipped,
        "failed": failed,
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Analyse les parties Obsidian avec Stockfish")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--depth", type=int, default=18)
    args = parser.parse_args(argv)
    print(json.dumps(analyse_vault(limit=args.limit, depth=args.depth), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
