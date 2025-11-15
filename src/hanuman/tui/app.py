from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List
import shlex
import subprocess
import httpx
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.reactive import reactive
from textual.widgets import DataTable, Footer, Header, Static

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------

API_BASE_URL = os.getenv("HANUMAN_API_URL", "http://127.0.0.1:8000")


@dataclass
class ServicePing:
    """Description d'un service /ping à interroger."""

    name: str  # nom logique du service (status, github, notion, ...)
    path: str  # chemin relatif pour le ping
    expects_ok: bool = True  # True si on s'attend à un champ "ok" dans la réponse JSON


@dataclass
class OrchestrationSpec:
    """Description d'une orchestration disponible dans Hanuman."""

    label: str    # libellé affiché dans le TUI
    slug: str     # identifiant interne
    command: str  # commande shell suggérée pour la lancer



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

# NOTE : adapte les paths si tes routes réelles sont différentes.
ORCHESTRATIONS: List[OrchestrationSpec] = [
    OrchestrationSpec(
        label="Github → Notion Sync",
        slug="github_to_notion_sync",
        command="poetry run python -m hanuman.orchestrations.github_to_notion_sync",
    ),
    OrchestrationSpec(
        label="Obsidian → Notion",
        slug="obsidian_to_notion",
        command="poetry run python -m hanuman.orchestrations.obsidian_to_notion",
    ),
    OrchestrationSpec(
        label="Chess → Obsidian (limit 500)",
        slug="chess_to_obsidian",
        command="poetry run python -m hanuman.orchestrations.chess_to_obsidian --limit 500",
    ),
]



ORCHESTRATIONS_BY_SLUG: Dict[str, OrchestrationSpec] = {
    o.slug: o for o in ORCHESTRATIONS
}

# -------------------------------------------------------------------
# Widgets : Status
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
        yield Static("", id="tab-bar")
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

        # (key, name, ok_symbol, summary, detail_json)
        rows: List[tuple[str, str, str, str, str]] = []

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
                            maybe = (
                                detail_obj.get("object") or detail_obj.get("name") or ""
                            )
                            summary = str(maybe)
                        else:
                            summary = "OK"

                        # détail JSON pretty
                        detail_json = json.dumps(data, indent=2, ensure_ascii=False)[
                            :4000
                        ]
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

        help_box.update(f"API base URL: {API_BASE_URL}")
        self.loading = False


    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Quand on change de ligne, on affiche le détail en bas."""
        key = str(event.row_key)
        detail = self._details.get(key, "")
        detail_box = self.query_one("#detail-box", Static)
        detail_box.update(detail)


# -------------------------------------------------------------------
# Widgets : Orchestrations
# -------------------------------------------------------------------


class OrchestrationTable(DataTable):
    """Tableau des orchestrations disponibles."""

    def on_mount(self) -> None:
        self.add_columns("Orchestration", "Dernier statut")


class OrchestrationView(Container):
    """Vue des orchestrations Hanuman."""

    loading: reactive[bool] = reactive(False)

    def __init__(self) -> None:
        super().__init__()
        # logs détaillés par ligne (clé = index de ligne)
        self._logs: Dict[int, str] = {}

    def compose(self) -> ComposeResult:
        yield Static("Hanuman · Orchestrations", id="title")
        yield Static("", id="tab-bar")
        yield OrchestrationTable(id="orch-table")
        yield Static("", id="orch-log-box")
        yield Static("", id="orch-help")

    async def on_mount(self) -> None:
        self._refresh_table()

    def _refresh_table(self) -> None:
        """Remplit la table des orchestrations sans les lancer."""
        table = self.query_one(OrchestrationTable)
        log_box = self.query_one("#orch-log-box", Static)
        help_box = self.query_one("#orch-help", Static)

        table.clear()
        self._logs.clear()
        log_box.update("")

        # Chaque orchestration correspond à une ligne (index = 0, 1, 2…)
        for idx, orch in enumerate(ORCHESTRATIONS):
            table.add_row(orch.label, "Jamais lancée")
            self._logs[idx] = "Jamais lancée"

        table.cursor_type = "row"
        if table.row_count > 0:
            table.focus()
            table.move_cursor(row=0, column=0)
            log_box.update(self._logs.get(0, ""))

        help_box.update(
            "↑/↓ : sélectionner · l : afficher la commande · r : rafraîchir · s/o : changer de vue"
        )

    async def run_selected(self) -> None:
        """Ouvre un nouveau kitty avec la commande pré-remplie pour l'orchestration sélectionnée."""
        table = self.query_one(OrchestrationTable)
        log_box = self.query_one("#orch-log-box", Static)

        if table.row_count == 0 or table.cursor_row is None:
            return

        row_index = table.cursor_row  # 0, 1, 2…
        if row_index < 0 or row_index >= len(ORCHESTRATIONS):
            return

        orch = ORCHESTRATIONS[row_index]
        cmd = orch.command

        # On affiche quand même la commande dans le TUI pour trace
        self._logs[row_index] = cmd
        log_box.update(f"Ouveture d'un nouveau kitty avec :\n{cmd}")

        # On prépare la commande shell pour bash + read -e -i
        quoted_cmd = shlex.quote(cmd)
        shell_snippet = (
            f"read -e -p '$ ' -i {quoted_cmd} usercmd; "
            "eval \"$usercmd\"; "
            "exec bash"
        )

        # Lance un nouveau kitty détaché
        try:
            subprocess.Popen(
                [
                    "kitty",
                    "--detach",
                    "bash",
                    "-ic",
                    shell_snippet,
                ]
            )
        except FileNotFoundError:
            # kitty pas trouvé : on le signale dans le TUI
            log_box.update(
                "Erreur : impossible de lancer 'kitty'.\n"
                "Vérifie que kitty est installé et accessible dans le PATH."
            )


    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Quand on change de ligne, on affiche le dernier log en bas."""
        try:
            idx = int(event.row_key)
        except Exception:
            return
        detail = self._logs.get(idx, "")
        log_box = self.query_one("#orch-log-box", Static)
        log_box.update(detail)



# -------------------------------------------------------------------
# Application principale
# -------------------------------------------------------------------

class HanumanTUI(App):
    """Cockpit TUI Hanuman : Status + Orchestrations."""

    CSS = """
    #title {
        height: 1;
        content-align: center middle;
        text-style: bold;
        border-bottom: solid #666666;
    }

    #tab-bar {
        height: 1;
        content-align: center middle;
        border-bottom: solid #444444;
    }

    #status-table, #orch-table {
        height: 1fr;
    }

    #detail-box, #orch-log-box {
        height: 8;
        border-top: solid #444444;
        padding: 0 1;
        overflow: auto;
    }

    #status-help, #orch-help {
        height: 3;
        border-top: solid #666666;
        content-align: center middle;
    }
    """

    # Vue active : "status" ou "orchestrations"
    active_view: reactive[str] = reactive("status")

    # On gardera les références aux vues ici
    status_view: StatusView  # seront assignées dans compose()
    orch_view: OrchestrationView

    BINDINGS = [
        ("q", "quit", "Quitter"),
        ("r", "refresh", "Rafraîchir"),
        ("s", "show_status", "Vue Status"),
        ("o", "show_orchestrations", "Vue Orchestrations"),
        ("l", "run", "Lancer sélection"),
    ]

    def compose(self) -> ComposeResult:
        """Construit l'interface Textual."""
        yield Header(show_clock=True)

        # On instancie les deux vues et on garde les références
        self.status_view = StatusView()
        self.orch_view = OrchestrationView()

        # On les yield dans l'ordre d'affichage
        yield self.status_view
        yield self.orch_view

        yield Footer()

    def on_mount(self) -> None:
        self._update_views_and_tabs()

    # --- Navigation entre vues -------------------------------------------------

    def watch_active_view(self, active_view: str) -> None:  # type: ignore[override]
        """Réagit au changement de vue active."""
        self._update_views_and_tabs()

    def _update_views_and_tabs(self) -> None:
        """Affiche/masque les vues et met à jour la barre d'onglets."""
        status_view = self.status_view
        orch_view = self.orch_view

        if self.active_view == "status":
            status_view.display = True
            orch_view.display = False
            # focus sur la table de status
            status_table = status_view.query_one(StatusTable)
            status_table.focus()
        else:
            status_view.display = False
            orch_view.display = True
            # focus sur la table des orchestrations
            orch_table = orch_view.query_one(OrchestrationTable)
            orch_table.focus()

        # Met à jour les tab-bars (les deux vues en ont une)
        status_tab = status_view.query_one("#tab-bar", Static)
        orch_tab = orch_view.query_one("#tab-bar", Static)

        tab_text = self._tab_bar_text()
        status_tab.update(tab_text)
        orch_tab.update(tab_text)


    def _tab_bar_text(self) -> str:
        """Construit le texte de la barre d'onglets."""
        if self.active_view == "status":
            status_label = "[b][Status][/b]"
            orch_label = "Orchestrations"
        else:
            status_label = "Status"
            orch_label = "[b][Orchestrations][/b]"

        return f"{status_label}  ·  {orch_label}"

    # --- Actions Textual -------------------------------------------------------

    async def action_refresh(self) -> None:
        """Rafraîchit la vue active."""
        if self.active_view == "status":
            await self.status_view.refresh_status()
        else:
            self.orch_view._refresh_table()

    async def action_show_status(self) -> None:
        self.active_view = "status"

    async def action_show_orchestrations(self) -> None:
        self.active_view = "orchestrations"

    async def action_run(self) -> None:
        """Lance l'action contextuelle : orchestrations uniquement."""
        if self.active_view == "orchestrations":
            await self.orch_view.run_selected()


def main() -> None:
    app = HanumanTUI()
    app.run()


if __name__ == "__main__":
    main()
