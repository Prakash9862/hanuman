# src/hanuman/tui/app.py
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List

import httpx
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.reactive import reactive
from textual.widgets import DataTable, Header, Footer, Static

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------

API_BASE_URL = os.getenv("HANUMAN_API_URL", "http://127.0.0.1:8000")


@dataclass
class ServicePing:
    name: str       # nom logique du service (status, github, notion, ...)
    path: str       # chemin relatif pour le ping
    expects_ok: bool = True  # True si on s'attend à un champ "ok" dans la réponse JSON


SERVICES: List[ServicePing] = [
    ServicePing("status", "/status/ping", expects_ok=False),
    ServicePing("calendar", "/calendar/ping"),
    ServicePing("chess", "/chess/ping"),
    ServicePing("github", "/github/ping"),
    ServicePing("notion", "/notion/ping"),
    ServicePing("obsidian", "/obsidian/ping"),
    ServicePing("openai", "/openai/ping"),
    ServicePing("wikipedia", "/wikipedia/ping"),
]


# -------------------------------------------------------------------
# Widgets
# -------------------------------------------------------------------


class StatusTable(DataTable):
    """Tableau des services (nom, OK, résumé)."""

    def on_mount(self) -> None:
        self.add_columns("Service", "OK", "Détail")

    def clear_rows(self) -> None:
        self.clear()


class StatusView(Container):
    """Vue principale : état des services Hanuman."""

    loading: reactive[bool] = reactive(False)

    def __init__(self) -> None:
        super().__init__()
        # Détails complets JSON par service (clé = name)
        self._details: Dict[str, str] = {}

    def compose(self) -> ComposeResult:
        yield Static("Hanuman · Status", id="title")
        yield StatusTable(id="status-table")
        yield Static("", id="detail-box")
        yield Static("", id="status-help")

    async def on_mount(self) -> None:
        await self.refresh_status()

    async def refresh_status(self) -> None:
        """Interroge tous les /ping et met à jour la table + détails."""
        self.loading = True

        table = self.query_one(StatusTable)
        detail_box = self.query_one("#detail-box", Static)
        help_box = self.query_one("#status-help", Static)

        table.clear_rows()
        self._details.clear()
        detail_box.update("")

        rows: List[tuple[str, str, str, str]] = []  # (key, name, ok_symbol, summary, detail_json)

        async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=5.0) as client:
            for svc in SERVICES:
                try:
                    resp = await client.get(svc.path)
                except httpx.RequestError as exc:
                    name = svc.name
                    ok_symbol = "❌"
                    summary = f"Erreur réseau: {exc.__class__.__name__}"
                    detail_json = summary
                else:
                    # On essaie de parser le JSON, sinon texte brut
                    try:
                        data: Any = resp.json()
                    except Exception:
                        data = None

                    name = svc.name
                    ok_symbol = "❌"
                    summary = ""

                    if resp.status_code == 200 and isinstance(data, dict):
                        # statut logique
                        if svc.expects_ok:
                            ok_symbol = "✅" if bool(data.get("ok")) else "❌"
                        else:
                            # pour /status/ping par exemple, on considère que 200 == OK
                            ok_symbol = "✅"

                        # résumé : on privilégie "error", "status", ou un mini champ pertinent
                        if not bool(data.get("ok", True)) and "error" in data:
                            summary = str(data["error"])
                        elif "status" in data:
                            summary = f"status={data['status']}"
                        elif "detail" in data and isinstance(data["detail"], dict):
                            # exemple: notion -> detail["user"]["object"]
                            detail_obj = data["detail"]
                            maybe = detail_obj.get("object") or detail_obj.get("name") or ""
                            summary = str(maybe)
                        else:
                            summary = "OK"

                        # détail JSON pretty
                        detail_json = json.dumps(
                            data, indent=2, ensure_ascii=False
                        )[:4000]
                    else:
                        ok_symbol = "❌"
                        summary = f"HTTP {resp.status_code}"
                        detail_json = resp.text[:4000]

                rows.append((svc.name, name, ok_symbol, summary, detail_json))

        # Remplissage de la table + enregistrement des détails
        for key, name, ok_symbol, summary, detail_json in rows:
            table.add_row(name, ok_symbol, summary, key=key)
            self._details[key] = detail_json

        # sélectionne la première ligne si dispo
        if rows:
            table.cursor_type = "row"
            table.focus()
            table.move_cursor(row=0, column=0)
            first_key = rows[0][0]
            detail_box.update(self._details.get(first_key, ""))

        help_box.update(
            f"API base URL: {API_BASE_URL} · [r] rafraîchir · [q] quitter · [↑/↓] sélectionner un service"
        )
        self.loading = False

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Quand on change de ligne, on affiche le détail en bas."""
        key = str(event.row_key)
        detail = self._details.get(key, "")
        detail_box = self.query_one("#detail-box", Static)
        detail_box.update(detail)


# -------------------------------------------------------------------
# Application principale
# -------------------------------------------------------------------


class HanumanTUI(App):
    """Cockpit TUI Hanuman (Status)."""

    CSS = """
    #title {
        height: 3;
        content-align: center middle;
        text-style: bold;
        border-bottom: solid #666666;
    }

    #status-table {
        height: 1fr;
    }

    #detail-box {
        height: 8;
        border-top: solid #444444;
        padding: 0 1;
        overflow: auto;
    }

    #status-help {
        height: 3;
        border-top: solid #666666;
        content-align: center middle;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quitter"),
        ("r", "refresh", "Rafraîchir"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield StatusView()
        yield Footer()

    async def action_refresh(self) -> None:
        view = self.query_one(StatusView)
        await view.refresh_status()


def main() -> None:
    app = HanumanTUI()
    app.run()


if __name__ == "__main__":
    main()
