from __future__ import annotations

import hashlib
import io
import re
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import median

import chess
import chess.pgn
import yaml

from hanuman.models.chess import ChessGame, chess_game_note_link, chess_game_path
from hanuman.models.chess_insight import ChessInsight
from hanuman.services.atomic_write_service import atomic_write_text
from hanuman.services.chess_analysis_summary_service import read_analysis_summary
from hanuman.services.chess_insight_storage_service import parse_insight_block
from hanuman.services.chess_insight_view_service import position_identity
from hanuman.services.chess_path_safety_service import resolve_safe_destination

PGN_PATTERN = re.compile(r"```pgn\s*(.*?)```", re.DOTALL | re.IGNORECASE)
ECO_FILENAME = re.compile(r"^[A-E]\d{2}\.md$")
GENERATED_START = "<!-- HANUMAN:GENERATED:START -->"
PROTOTYPES = frozenset({"eco_test.md", "eco_test2.md", "eco_test3.md", "eco_test4.md"})
OPENING_EXIT_FAVORABLE_CP = 50
OPENING_EXIT_UNFAVORABLE_CP = -50
SECTION_HEADINGS = (
    "## 👑 Vue d'ensemble",
    "## 📖 Mon répertoire",
    "### ⭐ Variante principale",
    "### 📚 Variantes secondaires",
    "### 📖 Référence théorique",
    "## ❤️ Santé de l'ouverture",
    "### Analyse générale",
    "### Position de référence de sortie d'ouverture",
    "## 📈 Évolution",
    "## ❌ Gaffes récurrentes",
    "## 💡 Opportunités manquées",
    "## 🎯 Conclusion",
    "## 🗂️ Parties",
)


@dataclass(frozen=True)
class EcoGame:
    game: ChessGame
    path: Path
    san: tuple[str, ...]
    pgn: str
    headers: dict[str, str]


@dataclass(frozen=True)
class Variant:
    san: tuple[str, ...]
    games: tuple[EcoGame, ...]

    @property
    def wins(self) -> int:
        return sum(item.game.result == "win" for item in self.games)

    @property
    def draws(self) -> int:
        return sum(item.game.result == "draw" for item in self.games)

    @property
    def losses(self) -> int:
        return sum(item.game.result == "loss" for item in self.games)

    @property
    def success_rate(self) -> float:
        return _success(self.wins, self.draws, self.losses)

    @property
    def win_rate(self) -> float:
        return round(self.wins / len(self.games) * 100, 1)

    @property
    def color(self) -> str:
        counts = Counter(item.game.color for item in self.games)
        return sorted(counts, key=lambda value: (-counts[value], value))[0]


@dataclass(frozen=True)
class EcoTheory:
    official_name: str
    reference_san: tuple[str, ...]
    source_complete: bool


@dataclass(frozen=True)
class EcoGenerationReport:
    pages_written: int
    widgets_generated: int
    ecos_generated: tuple[str, ...]
    games_total: int
    analysed_games: int
    theory_lines_available: int
    theory_lines_missing: int


def resolve_eco_reference_pdf() -> Path:
    chess_docs = Path(__file__).resolve().parents[3] / "docs" / "chess"
    expected = chess_docs / "File_ECOMast-Codes_ECO.pdf"
    if expected.is_file():
        return expected
    candidates = sorted(chess_docs.glob("*ECOMast*Codes_ECO.pdf"))
    if len(candidates) != 1:
        raise FileNotFoundError("Référence ECO unique introuvable dans docs/chess.")
    return candidates[0]


def _success(wins: int, draws: int, losses: int) -> float:
    total = wins + draws + losses
    return round((wins + draws / 2) / total * 100, 1) if total else 0.0


def _note_pgn(markdown: str) -> str:
    match = PGN_PATTERN.search(markdown)
    if not match:
        return ""
    return "\n".join(
        re.sub(r"^\s*>\s?", "", line) for line in match.group(1).strip().splitlines()
    ).strip()


def _parse_pgn(pgn: str) -> tuple[tuple[str, ...], dict[str, str]]:
    if not pgn:
        return (), {}
    parsed = chess.pgn.read_game(io.StringIO(pgn))
    if parsed is None:
        return (), {}
    board = parsed.board()
    san: list[str] = []
    try:
        for move in parsed.mainline_moves():
            san.append(board.san(move))
            board.push(move)
    except (ValueError, AssertionError):
        return (), {str(key): str(value) for key, value in parsed.headers.items()}
    return tuple(san), {str(key): str(value) for key, value in parsed.headers.items()}


def read_eco_games(root: Path, games: list[ChessGame]) -> tuple[EcoGame, ...]:
    result = []
    for game in sorted(games, key=lambda item: (item.game_id, item.note_filename)):
        path = chess_game_path(root, game)
        markdown = path.read_text(encoding="utf-8")
        pgn = _note_pgn(markdown)
        san, headers = _parse_pgn(pgn)
        result.append(EcoGame(game, path, san, pgn, headers))
    return tuple(result)


def _variant_prefixes(games: tuple[EcoGame, ...]) -> tuple[Variant, ...]:
    """Partitionne par préfixe SAN maximal partagé par au moins trois parties."""

    prefix_counts: Counter[tuple[str, ...]] = Counter()
    for item in games:
        for length in range(1, min(len(item.san), 16) + 1):
            prefix_counts[item.san[:length]] += 1

    grouped: dict[tuple[str, ...], list[EcoGame]] = defaultdict(list)
    for item in games:
        candidates = [
            prefix
            for prefix, count in prefix_counts.items()
            if count >= 3 and len(prefix) >= 2 and item.san[: len(prefix)] == prefix
        ]
        prefix = max(
            candidates, key=lambda value: (len(value), value), default=item.san[:2]
        )
        grouped[prefix].append(item)

    variants = [Variant(san, tuple(items)) for san, items in grouped.items() if san]
    return tuple(
        sorted(
            variants,
            key=lambda item: (-len(item.games), -item.success_rate, item.san),
        )
    )


def _french_to_san(line: str) -> tuple[str, ...]:
    tokens = re.findall(
        r"(?:\d+\.(?:\.\.)?)?([a-hCFTDR][a-h1-8x=+#O-]*[+#]?)",
        line,
        flags=re.IGNORECASE,
    )
    translation = str.maketrans({"C": "N", "F": "B", "T": "R", "D": "Q", "R": "K"})
    return tuple(token.translate(translation) for token in tokens)


def load_eco_theory(pdf_path: Path) -> dict[str, tuple[EcoTheory, ...]]:
    completed = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    physical = completed.stdout.replace("\f", "\n").splitlines()
    logical: list[str] = []
    for line in physical:
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r"^[A-E]\d{2}(?:/\d+)?\s", stripped):
            logical.append(stripped)
        elif logical and re.match(r"^\d+\.", stripped):
            logical[-1] += " " + stripped

    choices: dict[str, list[tuple[int, str, tuple[str, ...]]]] = defaultdict(list)
    for line in logical:
        match = re.match(r"^([A-E]\d{2})(?:/\d+)?\s+(.+?)(?=\s+1\.)", line)
        if not match:
            continue
        eco, name = match.groups()
        reference = _french_to_san(line[match.end() :])
        choices[eco].append((len(reference), name.strip(), reference))

    result: dict[str, tuple[EcoTheory, ...]] = {}
    for eco, entries in choices.items():
        result[eco] = tuple(
            EcoTheory(name, reference, bool(reference))
            for _, name, reference in sorted(
                entries, key=lambda item: (item[1], item[2])
            )
        )
    return result


def _matching_theory(
    entries: tuple[EcoTheory, ...],
    played: tuple[str, ...],
) -> EcoTheory | None:
    if not entries:
        return None

    def common_prefix(entry: EcoTheory) -> int:
        return next(
            (
                index
                for index, (expected, actual) in enumerate(
                    zip(entry.reference_san, played)
                )
                if expected != actual
            ),
            min(len(entry.reference_san), len(played)),
        )

    return sorted(
        entries,
        key=lambda entry: (
            -common_prefix(entry),
            -min(len(entry.reference_san), len(played)),
            entry.official_name,
            entry.reference_san,
        ),
    )[0]


def _result_counts(games: tuple[EcoGame, ...]) -> tuple[int, int, int]:
    return (
        sum(item.game.result == "win" for item in games),
        sum(item.game.result == "draw" for item in games),
        sum(item.game.result == "loss" for item in games),
    )


def _line(san: tuple[str, ...]) -> str:
    return " ".join(san) if san else "Ligne indisponible dans les PGN persistés"


def _numbered_line(san: tuple[str, ...]) -> str:
    parts = []
    for index, move in enumerate(san):
        if index % 2 == 0:
            parts.append(f"{index // 2 + 1}.{move}")
        else:
            parts.append(move)
    return " ".join(parts)


def _first_divergence(theory: tuple[str, ...], played: tuple[str, ...]) -> str:
    for index, (expected, actual) in enumerate(zip(theory, played)):
        if expected != actual:
            move = f"{index // 2 + 1}{'.' if index % 2 == 0 else '...'}"
            return f"{move} : théorie `{expected}`, répertoire `{actual}`"
    if not theory:
        return "Indéterminable : ligne théorique absente du PDF"
    if len(played) < len(theory):
        return f"{len(played) // 2 + 1} : ligne réellement jouée plus courte"
    return "Aucun dans la portion documentée"


def _board_after(san: tuple[str, ...]) -> chess.Board | None:
    board = chess.Board()
    try:
        for token in san:
            board.push_san(token)
    except ValueError:
        return None
    return board


def _svg(board: chess.Board, orientation: str) -> str:
    symbols = {
        "r": "♜",
        "n": "♞",
        "b": "♝",
        "q": "♛",
        "k": "♚",
        "p": "♟",
        "R": "♖",
        "N": "♘",
        "B": "♗",
        "Q": "♕",
        "K": "♔",
        "P": "♙",
    }
    ranks = list(range(7, -1, -1)) if orientation == "white" else list(range(8))
    files = list(range(8)) if orientation == "white" else list(range(7, -1, -1))
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 440 440" '
        'role="img" aria-label="Position de référence" '
        'style="max-width:440px;width:100%;height:auto">',
        '<rect width="440" height="440" rx="12" fill="#1f2430"/>',
    ]
    for row, rank in enumerate(ranks):
        for column, file in enumerate(files):
            x, y = 28 + column * 48, 28 + row * 48
            fill = "#e8d7b9" if (file + rank) % 2 else "#8b5e3c"
            lines.append(
                f'<rect x="{x}" y="{y}" width="48" height="48" fill="{fill}"/>'
            )
            piece = board.piece_at(chess.square(file, rank))
            if piece:
                lines.append(
                    f'<text x="{x + 24}" y="{y + 36}" text-anchor="middle" '
                    f'font-size="38" font-family="DejaVu Sans, serif">'
                    f"{symbols[piece.symbol()]}</text>"
                )
    visible_files = "abcdefgh" if orientation == "white" else "hgfedcba"
    visible_ranks = "87654321" if orientation == "white" else "12345678"
    for index, label in enumerate(visible_files):
        lines.append(
            f'<text x="{52 + index * 48}" y="428" text-anchor="middle" '
            f'fill="#d9dde7" font-size="14">{label}</text>'
        )
    for index, label in enumerate(visible_ranks):
        lines.append(
            f'<text x="14" y="{59 + index * 48}" text-anchor="middle" '
            f'fill="#d9dde7" font-size="14">{label}</text>'
        )
    lines.append("</svg>")
    return "\n".join(lines)


def _widget_pgn(eco: str, name: str, san: tuple[str, ...]) -> str:
    board = chess.Board()
    game = chess.pgn.Game()
    game.headers["Event"] = "Hanuman Opening Widget"
    game.headers["Site"] = "Hanuman"
    game.headers["Result"] = "*"
    game.headers["ECO"] = eco
    game.headers["Opening"] = name
    node: chess.pgn.GameNode = game
    for token in san:
        move = board.parse_san(token)
        node = node.add_variation(move)
        board.push(move)
    exporter = chess.pgn.StringExporter(headers=True, variations=False, comments=False)
    return game.accept(exporter)


def _persisted_envelope(item: EcoGame):
    try:
        return parse_insight_block(item.path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return None


def _opening_exit(item: EcoGame) -> dict[str, object] | None:
    envelope = _persisted_envelope(item)
    return envelope.opening_exit if envelope is not None else None


def _opening_exit_cp(item: EcoGame) -> int | None:
    exit_data = _opening_exit(item)
    value = exit_data.get("evaluation_value") if exit_data is not None else None
    if (
        exit_data is None
        or exit_data.get("evaluation_type") != "centipawn"
        or exit_data.get("evaluation_perspective") != "hanuman-player"
        or type(value) is not int
    ):
        return None
    return value


def _representative_exit(
    games: tuple[EcoGame, ...],
) -> tuple[EcoGame, dict[str, object], int] | None:
    positions: dict[str, list[tuple[EcoGame, dict[str, object]]]] = defaultdict(list)
    for item in games:
        exit_data = _opening_exit(item)
        fen = exit_data.get("fen") if exit_data is not None else None
        key = position_identity(fen if isinstance(fen, str) else None)
        if key is not None and exit_data is not None:
            positions[key].append((item, exit_data))
    if not positions:
        return None
    key, occurrences = sorted(
        positions.items(),
        key=lambda entry: (-len(entry[1]), entry[0]),
    )[0]
    del key
    representative = sorted(
        occurrences,
        key=lambda pair: (pair[0].game.end_time, pair[0].game.game_id),
        reverse=True,
    )[0]
    return representative[0], representative[1], len(occurrences)


def _eco_position_recurrences(games: tuple[EcoGame, ...], category: str) -> str:
    grouped: dict[str, list[tuple[EcoGame, ChessInsight]]] = defaultdict(list)
    total = 0
    for item in games:
        envelope = _persisted_envelope(item)
        if envelope is None:
            continue
        for insight in envelope.insights:
            if insight.category != category or insight.player_role != "player":
                continue
            total += 1
            key = position_identity(insight.fen_before)
            if key is not None:
                grouped[key].append((item, insight))
    recurrent = [
        occurrences
        for occurrences in grouped.values()
        if len({item.game.game_id for item, _ in occurrences}) >= 2
    ]
    recurrent.sort(
        key=lambda occurrences: (
            -len(occurrences),
            str(occurrences[0][1].fen_before),
        )
    )
    if not recurrent:
        return (
            f"> **{total} événement(s) V2 positionné(s)**. "
            "Aucune même position FEN dans au moins deux parties. "
            "Aucune récurrence ni aucun échiquier n’est fabriqué."
        )
    occurrences = recurrent[0]
    insight = occurrences[0][1]
    links = " · ".join(
        dict.fromkeys(chess_game_note_link(item.game) for item, _ in occurrences)
    )
    return (
        f"> [!example] Position réellement récurrente · {len(occurrences)} occurrences\n"
        f"> FEN avant le coup : `{insight.fen_before}`  \n"
        f"> Coup joué : `{insight.san}`"
        + (
            f" · meilleur coup : `{insight.best_move_san}`"
            if insight.best_move_san
            else ""
        )
        + f"  \n> Parties : {links}"
    )


def _monthly(games: tuple[EcoGame, ...]) -> list[tuple[str, int, int, int, int, float]]:
    grouped: dict[str, list[EcoGame]] = defaultdict(list)
    for item in games:
        grouped[item.game.end_time.strftime("%Y-%m")].append(item)
    rows = []
    for month, items in sorted(grouped.items()):
        wins, draws, losses = _result_counts(tuple(items))
        rows.append(
            (month, len(items), wins, draws, losses, _success(wins, draws, losses))
        )
    return rows


def _confidence_stars(count: int, *, high: int, medium: int) -> str:
    score = 4 if count >= high else 3 if count >= medium else 2 if count else 1
    return "★" * score + "☆" * (5 - score)


def build_eco_page(
    root: Path,
    eco: str,
    games: tuple[EcoGame, ...],
    theory: EcoTheory | None,
) -> str:
    variants = _variant_prefixes(games)
    main = variants[0] if variants else Variant((), games)
    secondaries = tuple(
        item
        for item in variants[1:]
        if len(item.games) >= 5 or (len(item.games) >= 3 and item.success_rate >= 80)
    )
    displayed = (main, *secondaries)
    health_variants = (main,) + tuple(
        item for item in secondaries if item.success_rate >= 80
    )
    health_ids = {
        item.game.game_id for variant in health_variants for item in variant.games
    }
    health_games = tuple(item for item in games if item.game.game_id in health_ids)
    analysed = tuple(
        item for item in games if read_analysis_summary(item.path).analysed
    )
    health_analysed = tuple(
        item for item in health_games if read_analysis_summary(item.path).analysed
    )
    wins, draws, losses = _result_counts(games)
    hw, hd, hl = _result_counts(health_games)
    colors = Counter(item.game.color for item in games)
    players = Counter(
        item.game.white if item.game.color == "white" else item.game.black
        for item in games
    )
    player = sorted(players, key=lambda value: (-players[value], value))[0]
    official_name = theory.official_name if theory else games[0].game.opening_name
    theory_line = theory.reference_san if theory else ()
    persisted_exit = _representative_exit(main.games)
    exit_item = persisted_exit[0] if persisted_exit else None
    exit_data = persisted_exit[1] if persisted_exit else None
    exit_frequency = persisted_exit[2] if persisted_exit else 0
    exit_fen = exit_data.get("fen") if exit_data else None
    board = (
        chess.Board(exit_fen) if isinstance(exit_fen, str) else _board_after(main.san)
    )
    orientation = main.color
    fen = board.fen() if board else ""
    digest = hashlib.sha256(f"{eco}|{' '.join(main.san)}|{fen}".encode()).hexdigest()[
        :12
    ]
    board_id = f"hanuman-board-{eco.lower()}-main-{digest}-v1"
    pgn = (
        exit_item.pgn
        if exit_item is not None
        else (_widget_pgn(eco, official_name, main.san) if board else "")
    )
    representative = (
        exit_item
        or sorted(
            main.games,
            key=lambda item: (item.game.end_time, item.game.game_id),
            reverse=True,
        )[0]
    )
    all_game_ids = sorted(item.game.game_id for item in main.games)
    exit_evaluations = [
        value for item in health_games if (value := _opening_exit_cp(item)) is not None
    ]
    exit_average = (
        round(sum(exit_evaluations) / len(exit_evaluations), 1)
        if exit_evaluations
        else None
    )
    exit_median = (
        round(float(median(exit_evaluations)), 1) if exit_evaluations else None
    )
    exit_favorable = sum(
        value > OPENING_EXIT_FAVORABLE_CP for value in exit_evaluations
    )
    exit_unfavorable = sum(
        value < OPENING_EXIT_UNFAVORABLE_CP for value in exit_evaluations
    )
    exit_balanced = len(exit_evaluations) - exit_favorable - exit_unfavorable
    months = _monthly(games)
    displayed_count = sum(len(item.games) for item in displayed)
    other_count = len(games) - displayed_count
    main_share = round(len(main.games) / len(games) * 100, 1)
    coverage = round(len(analysed) / len(games) * 100, 1)
    health_rate = _success(hw, hd, hl)
    health_exit_coverage = (
        round(len(exit_evaluations) / len(health_games) * 100, 1)
        if health_games
        else 0.0
    )
    raw_position_ply = exit_data.get("ply") if exit_data else None
    position_ply = raw_position_ply if type(raw_position_ply) is int else len(main.san)
    date_first = min(item.game.end_time for item in games).strftime("%Y-%m-%d")
    date_last = max(item.game.end_time for item in games).strftime("%Y-%m-%d")
    note_links = "\n".join(
        f"> - {chess_game_note_link(item.game)}"
        for item in sorted(
            games,
            key=lambda item: (item.game.end_time, item.game.game_id),
            reverse=True,
        )
    )
    widget_links = "\n".join(
        f"> - {chess_game_note_link(item.game)}"
        for item in sorted(
            main.games,
            key=lambda item: (item.game.end_time, item.game.game_id),
            reverse=True,
        )
    )

    yaml_data = {
        "type": "chess-opening",
        "schema_version": 1,
        "status": "generated",
        "generated_by": "Hanuman",
        "platform": "chess.com",
        "player": player,
        "eco": eco,
        "opening_name": official_name,
        "opening_name_source": "ECOMast Codes ECO",
        "aliases": sorted(
            {eco, official_name, *(item.game.opening_name for item in games)}
        ),
        "colors_played": {"white": colors["white"], "black": colors["black"]},
        "games": {
            "total": len(games),
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "success_rate": _success(wins, draws, losses),
        },
        "period": {"first_game": date_first, "last_game": date_last},
        "stockfish": {
            "analysed_games": len(analysed),
            "coverage_percent": coverage,
        },
        "repertoire": {
            "main_line": _line(main.san),
            "main_line_games": len(main.games),
            "main_line_success_rate": main.success_rate,
            "displayed_secondary_lines": len(secondaries),
            "displayed_lines_games": displayed_count,
            "other_attempts_games": other_count,
        },
        "health_scope": {
            "games": len(health_games),
            "wins": hw,
            "draws": hd,
            "losses": hl,
            "success_rate": health_rate,
            "analysed_games": len(health_analysed),
            "opening_exit_evaluable_games": len(exit_evaluations),
            "opening_exit_coverage_percent": health_exit_coverage,
            "opening_exit_average_cp": exit_average,
            "opening_exit_median_cp": exit_median,
            "opening_exit_distribution": {
                "favorable": exit_favorable,
                "balanced": exit_balanced,
                "unfavorable": exit_unfavorable,
            },
        },
        "theory": {
            "source": "docs/chess/File_ECOMast-Codes_ECO.pdf",
            "official_entry": f"{eco} {official_name}",
            "reference_line_san": _line(theory_line),
        },
        "evolution_metric": "monthly_success_rate",
        "tags": [
            "chess/opening",
            f"chess/opening/{eco}",
            "chess/repertoire",
            *(f"chess/color/{color}" for color in sorted(colors)),
        ],
        "boards": [
            {
                "id": board_id,
                "kind": "opening-position-widget",
                "position_role": (
                    "persisted-opening-exit"
                    if persisted_exit
                    else "repertoire-reference"
                ),
                "recurrent_position": exit_frequency >= 2,
                "eco": eco,
                "variant": "main-line",
                "variant_san": _line(main.san),
                "exit_move": (
                    str(exit_data.get("last_move_san", ""))
                    if exit_data
                    else main.san[-1]
                )
                if main.san
                else "",
                "position_after_ply": position_ply,
                "fen": fen,
                "pgn": pgn,
                "games_count": exit_frequency if persisted_exit else len(main.games),
                "player_color": main.color,
                "orientation": orientation,
                "game_ids": all_game_ids,
                "representative_note": str(representative.path.relative_to(root)),
                "uri": f"hanuman://chess/boards/{board_id}",
                "interaction_protocol": "hanuman-v1",
                "interaction_status": "active",
                "actions": [
                    "open-scid",
                    "open-games",
                    "copy-fen",
                    "copy-pgn",
                    "open-note",
                ],
            }
        ],
    }
    yaml_text = yaml.safe_dump(
        yaml_data, allow_unicode=True, sort_keys=False, default_flow_style=False
    ).rstrip()

    secondary_blocks = []
    for variant in secondaries:
        icon = "⚪" if variant.color == "white" else "⚫"
        reason = (
            "volume ≥ 5"
            if len(variant.games) >= 5
            else "≥ 3 parties et ≥ 80 % de réussite"
        )
        secondary_blocks.append(
            f"> [!abstract]- {icon} {variant.color.title()} · {len(variant.games)} parties "
            f"· {variant.success_rate:.1f} % de réussite\n"
            f"> **`{_line(variant.san)}`**  \n"
            f"> {variant.wins} V · {variant.draws} N · {variant.losses} D · sélection : {reason}"
        )
    secondary = "\n\n".join(secondary_blocks) or (
        "> [!info] Aucune variante secondaire ne franchit les seuils validés."
    )
    theory_display = (
        _numbered_line(theory_line) if theory_line else "Indisponible dans le PDF"
    )
    theory_limit = (
        "> [!info] Limite de la source\n"
        "> Le PDF ne fournit pas de ligne exploitable pour cette ECO ; aucun contenu n’est inventé."
        if not theory_line
        else "> [!info] Limite de la source\n"
        "> La comparaison est limitée à la portion explicitement documentée dans le PDF ECOMast."
    )
    if exit_evaluations:
        assert exit_average is not None and exit_median is not None
        if health_exit_coverage < 50:
            exit_finding = (
                "Couverture trop faible pour conclure sur la qualité habituelle."
            )
        elif exit_average is not None and exit_average > OPENING_EXIT_FAVORABLE_CP:
            exit_finding = (
                "La sortie est généralement favorable dans les parties évaluables."
            )
        elif exit_average is not None and exit_average < OPENING_EXIT_UNFAVORABLE_CP:
            exit_finding = "L’ouverture est souvent quittée en position défavorable."
        else:
            exit_finding = (
                "La sortie est généralement équilibrée dans les parties évaluables."
            )
        quality = (
            f"> **{len(exit_evaluations)} parties évaluables sur {len(health_games)}** "
            f"dans le périmètre de santé ({health_exit_coverage:.1f} %).  \n"
            f"> Évaluation joueur moyenne : **{exit_average / 100:+.2f}** · "
            f"médiane : **{exit_median / 100:+.2f}**.  \n"
            f"> Favorables : **{exit_favorable}** · équilibrées : **{exit_balanced}** · "
            f"défavorables : **{exit_unfavorable}** "
            f"(seuils : ±{OPENING_EXIT_FAVORABLE_CP} cp).  \n"
            f"> **Constat :** {exit_finding}"
        )
    else:
        quality = (
            f"> **0 partie évaluable sur {len(health_games)}** dans le périmètre de santé.  \n"
            "> Les analyses V1 restent lisibles, mais ne contiennent pas d’évaluation "
            "persistée de sortie ; aucune conclusion n’est produite."
        )
    position_move = (
        str(exit_data.get("last_move_san", "—"))
        if exit_data
        else (main.san[-1] if main.san else "—")
    )
    position_explanation = (
        f"FEN V2 réelle choisie parmi les sorties de la variante principale : "
        f"elle apparaît dans **{exit_frequency} partie(s)**. "
        + (
            "Cette position est récurrente."
            if exit_frequency >= 2
            else "Elle est représentative par départage déterministe, sans récurrence affirmée."
        )
        if persisted_exit
        else "Aucune sortie V2 disponible : repli V1 sur la ligne principale du répertoire."
    )
    blunder_positions = _eco_position_recurrences(games, "blunder")
    opportunity_positions = _eco_position_recurrences(games, "opportunity")
    chart_months = ", ".join(f'"{row[0]}"' for row in months)
    chart_rates = ", ".join(f"{row[5]:.1f}" for row in months)
    month_rows = "\n".join(
        f"| {month} | {count} | {mw} / {md} / {ml} | {rate:.1f} % |"
        for month, count, mw, md, ml, rate in months
    )
    health_names = "variante principale" + (
        f" et {len(health_variants) - 1} variante(s) secondaire(s) à ≥ 80 %"
        if len(health_variants) > 1
        else ""
    )
    action_links = " ".join(
        f'<a href="hanuman://chess/boards/{board_id}?action={action}">{label}</a>'
        for action, label in (
            ("open-scid", "♟️ SCID"),
            ("open-games", "🗂️ Parties"),
            ("copy-fen", "📋 FEN"),
            ("copy-pgn", "📋 PGN"),
            ("open-note", "📝 Note"),
        )
    )
    conclusion = (
        f"Le corpus {eco} compte **{len(games)} parties** ; la ligne principale représente "
        f"**{main_share:.1f} %** et les lignes retenues **{displayed_count / len(games) * 100:.1f} %**. "
        f"Le taux de réussite global est de **{_success(wins, draws, losses):.1f} %**."
    )
    body = f"""---
{yaml_text}
---

{GENERATED_START}
# {eco} — {official_name}

> [!chess] Référence visuelle Hanuman
> Page construite exclusivement depuis les **{len(games)} parties {eco}** du vault, leurs PGN et leurs analyses persistées.

---

## 👑 Vue d'ensemble

> [!summary] {eco} en un regard
> **{len(games)} parties** · 🟢 **{wins} V** · 🟡 **{draws} N** · 🔴 **{losses} D**  
> ⚪ **{colors["white"]} Blancs** · ⚫ **{colors["black"]} Noirs** · **{_success(wins, draws, losses):.1f} % de réussite** `(V + ½N)`{"  "}
> **{date_first} → {date_last}** · 🔬 **{len(analysed)}/{len(games)} analysées ({coverage:.1f} %)**

---

## 📖 Mon répertoire

### ⭐ Variante principale

> [!tip] {"⚪" if main.color == "white" else "⚫"} Ligne la plus fréquente
> **`{_line(main.san)}`**  
> **{len(main.games)} parties** · {main.wins} V · {main.draws} N · {main.losses} D · **{main.success_rate:.1f} % de réussite**

La ligne la plus fréquente représente **{main_share:.1f} %** des parties {eco}.

### 📚 Variantes secondaires

{secondary}

> [!note]- Autres essais · {other_count} parties
> Ces parties ne franchissent ni le seuil de **5 parties**, ni le seuil combiné de **3 parties et 80 % de victoires**.  
> Les lignes affichées couvrent **{displayed_count}/{len(games)} parties ({displayed_count / len(games) * 100:.1f} %)**.

### 📖 Référence théorique

| Référence | Ligne |
|---|---|
| **Nom officiel ECO** | {eco} — {official_name} |
| **Ligne ECOMast** | `{theory_display}` |
| **Ligne réellement jouée** | `{_numbered_line(main.san)}` |
| **Premier point de divergence** | {_first_divergence(theory_line, main.san)} |

{theory_limit}

---

## ❤️ Santé de l'ouverture

### Analyse générale

> [!heart] Périmètre strict · {len(health_games)} parties
> Résultats décrivant uniquement la {health_names} : **{hw} V · {hd} N · {hl} D · {health_rate:.1f} % de réussite**.

{quality}

### Position de référence de sortie d'ouverture

> [!info] Position de référence du répertoire
> {position_explanation}

<div class="hanuman-board-widget" data-hanuman-board-id="{board_id}" data-eco="{eco}" data-variant="main-line">
  <strong>♟️ Position de référence · {eco} · après {position_move} (ply {position_ply})</strong>
  <a href="hanuman://chess/boards/{board_id}?action=open-scid">
{_svg(board, orientation) if board else "> SVG indisponible : PGN principal illisible."}
  </a>
  <div>{action_links}</div>
  <div><strong>ID :</strong> <code>{board_id}</code><br/><strong>FEN :</strong> <code>{fen}</code></div>
</div>

> [!example]- 🗂️ Parties liées à cet échiquier · {len(main.games)}
{widget_links}

---

## 📈 Évolution

> [!chart] Taux de réussite mensuel
> Métrique : `(victoires + ½ nulles) / parties`. Les mois sans partie sont omis.

```mermaid
xychart-beta
    title "{eco} — taux de réussite mensuel (%)"
    x-axis [{chart_months}]
    y-axis "Réussite (%)" 0 --> 100
    line [{chart_rates}]
```

| Période | Parties | V / N / D | Réussite |
|---|---:|:---:|---:|
{month_rows}

---

## ❌ Gaffes récurrentes

{blunder_positions}

---

## 💡 Opportunités manquées

{opportunity_positions}

---

## 🎯 Conclusion

| Indicateur | Évaluation visuelle | Fondement |
|---|:---:|---|
| **Maîtrise** | Non notée | Aucun modèle de maîtrise validé |
| **Confiance résultats** | {_confidence_stars(len(games), high=30, medium=10)} | {len(games)} parties |
| **Confiance qualité** | {_confidence_stars(len(health_analysed), high=20, medium=5)} | {len(health_analysed)} analyse(s) dans le périmètre santé |

> [!success] Synthèse
> {conclusion}

---

## 🗂️ Parties

> [!example]- 🗂️ Voir les parties · {len(games)}
{note_links}
"""
    return body.rstrip() + "\n"


def _validate_page(content: str, eco: str, root: Path) -> None:
    if not content.startswith("---\n"):
        raise ValueError(f"{eco} : YAML absent.")
    end = content.find("\n---\n", 4)
    metadata = yaml.safe_load(content[4:end])
    if not isinstance(metadata, dict) or metadata.get("eco") != eco:
        raise ValueError(f"{eco} : YAML invalide.")
    positions = [content.find(heading) for heading in SECTION_HEADINGS]
    if any(position < 0 for position in positions) or positions != sorted(positions):
        raise ValueError(f"{eco} : ordre des sections invalide.")
    boards = metadata.get("boards")
    if not isinstance(boards, list) or len(boards) != 1:
        raise ValueError(f"{eco} : widget YAML absent.")
    board = boards[0]
    if not board.get("id") or board["id"] not in content or "<svg " not in content:
        raise ValueError(f"{eco} : widget incomplet.")
    if not all(
        action in board.get("actions", [])
        for action in ("open-scid", "open-games", "copy-fen", "copy-pgn", "open-note")
    ):
        raise ValueError(f"{eco} : actions Hanuman incomplètes.")
    for target in re.findall(r"\[\[Echecs/([^|\]#]+)", content):
        note = root / target
        if not note.is_file() and not note.with_suffix(".md").is_file():
            raise ValueError(f"{eco} : lien de partie invalide : {target}")


def write_eco_pages(
    root: Path,
    games: list[ChessGame],
    *,
    theory_pdf: Path,
) -> EcoGenerationReport:
    theory = load_eco_theory(theory_pdf)
    all_games = read_eco_games(root, games)
    grouped: dict[str, list[EcoGame]] = defaultdict(list)
    for item in all_games:
        grouped[item.game.eco].append(item)
    openings = resolve_safe_destination(root, root / "_Index" / "Ouvertures")
    openings.mkdir(parents=True, exist_ok=True)
    planned: list[tuple[Path, str]] = []
    widgets = available = missing = analysed_total = 0
    for eco, items in sorted(grouped.items()):
        if not re.fullmatch(r"[A-E]\d{2}", eco):
            continue
        variants = _variant_prefixes(tuple(items))
        main_san = variants[0].san if variants else ()
        selected_theory = _matching_theory(theory.get(eco, ()), main_san)
        content = build_eco_page(root, eco, tuple(items), selected_theory)
        _validate_page(content, eco, root)
        path = resolve_safe_destination(root, openings / f"{eco}.md")
        if path.name in PROTOTYPES:
            raise ValueError("Un prototype ECO ne peut pas être une destination.")
        if path.exists():
            current = path.read_text(encoding="utf-8")
            if GENERATED_START not in current and "type: chess-index" not in current:
                raise ValueError(f"Page ECO humaine protégée : {path}")
        planned.append((path, content))
        widgets += 1
        analysed_total += sum(
            read_analysis_summary(item.path).analysed for item in items
        )
        if selected_theory and selected_theory.reference_san:
            available += 1
        else:
            missing += 1
    for path, content in planned:
        atomic_write_text(path, content)
    return EcoGenerationReport(
        pages_written=len(planned),
        widgets_generated=widgets,
        ecos_generated=tuple(path.stem for path, _ in planned),
        games_total=len(all_games),
        analysed_games=analysed_total,
        theory_lines_available=available,
        theory_lines_missing=missing,
    )
