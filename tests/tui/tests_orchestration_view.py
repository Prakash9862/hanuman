import pytest
from textual.widgets import Static

from hanuman.tui.app import OrchestrationTable, OrchestrationView


class DummyEvent:
    """Événement minimal pour simuler RowHighlighted."""

    def __init__(self, row_key: object) -> None:
        self.row_key = row_key


class DummyOrchestrationTable(OrchestrationTable):
    """Table factice qui expose un cursor_row contrôlé."""

    def __init__(self, cursor_row: int | None) -> None:
        super().__init__()
        self._cursor_row = cursor_row

    @property
    def cursor_row(self) -> int | None:  # type: ignore[override]
        return self._cursor_row


def test_on_row_highlighted_updates_log_box(monkeypatch: pytest.MonkeyPatch) -> None:
    """Vérifie que le log_box est mis à jour avec la ligne courante."""

    view = OrchestrationView()

    # On prépare un log pour la ligne 0
    view._logs = {0: "poetry run python -m hanuman.orchestrations.github_to_notion_sync"}

    dummy_table = DummyOrchestrationTable(cursor_row=0)
    log_box = Static("initial")

    def fake_query_one(selector, *args, **kwargs):  # type: ignore[no-untyped-def]
        # On simule les deux appels attendus :
        # - query_one(OrchestrationTable)
        # - query_one("#orch-log-box", Static)
        if selector is OrchestrationTable:
            return dummy_table
        if selector == "#orch-log-box":
            return log_box
        raise AssertionError(f"query_one appelé avec un sélecteur inattendu: {selector!r}")

    # On remplace la méthode query_one de cette instance de vue
    monkeypatch.setattr(view, "query_one", fake_query_one)

    event = DummyEvent(row_key=0)

    # Appel de la méthode à tester
    view.on_data_table_row_highlighted(event)

    # Static stocke son contenu dans .renderable
    assert str(log_box.renderable) == (
        "poetry run python -m hanuman.orchestrations.github_to_notion_sync"
    )


def test_on_row_highlighted_with_no_cursor_does_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Si aucune ligne n'est sélectionnée, le log_box ne doit pas changer."""

    view = OrchestrationView()

    view._logs = {0: "doit rester ignoré"}

    dummy_table = DummyOrchestrationTable(cursor_row=None)
    log_box = Static("initial")

    def fake_query_one(selector, *args, **kwargs):  # type: ignore[no-untyped-def]
        if selector is OrchestrationTable:
            return dummy_table
        if selector == "#orch-log-box":
            return log_box
        raise AssertionError(f"query_one appelé avec un sélecteur inattendu: {selector!r}")

    monkeypatch.setattr(view, "query_one", fake_query_one)

    event = DummyEvent(row_key=0)

    view.on_data_table_row_highlighted(event)

    # Comme cursor_row est None, on ne doit pas toucher au log_box
    assert str(log_box.renderable) == "initial"
