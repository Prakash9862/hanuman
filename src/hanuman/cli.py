from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import datetime
from typing import Any, Sequence

from rich.console import Console
from rich.table import Table

from hanuman.config.env import GITHUB_ALLOWED_REPOSITORIES
from hanuman.models.github_project_memory import FlowRun, GitHubProjectMemoryInput
from hanuman.orchestrations.github_project_memory import plan_github_project_memory


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hanuman", description="CLI du hub Hanuman.")
    commands = parser.add_subparsers(dest="command", required=True)
    flows = commands.add_parser("flows", help="Exécuter un Flux Hanuman.")
    flow_commands = flows.add_subparsers(dest="flow", required=True)
    project_memory = flow_commands.add_parser(
        "github-project-memory",
        help="Transformer une activité GitHub bornée en plan de mémoire projet.",
    )
    actions = project_memory.add_subparsers(dest="action", required=True)
    plan = actions.add_parser(
        "plan",
        help="Calculer un plan déterministe sans aucune écriture Notion.",
    )
    plan.add_argument("--repository", required=True, help="Dépôt autorisé au format owner/name.")
    plan.add_argument("--branch", help="Branche ou ref ; branche par défaut si absente.")
    plan.add_argument(
        "--start-ref",
        help="SHA de départ exclusif ; doit être présent dans la plage bornée.",
    )
    plan.add_argument(
        "--end-ref",
        help="SHA ou ref de fin inclusif ; la branche est utilisée si absent.",
    )
    plan.add_argument(
        "--max-commits",
        type=int,
        default=50,
        help="Nombre maximal de commits collectés, entre 1 et 100 (défaut : 50).",
    )
    plan.add_argument(
        "--session-window-hours",
        type=int,
        default=24,
        help="Fenêtre d'inactivité d'une session en heures (défaut : 24).",
    )
    plan.add_argument(
        "--detailed-plan",
        action="store_true",
        help="Afficher les identités, associations et effets planifiés.",
    )
    plan.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Émettre le Run structuré en JSON.",
    )
    return parser


def _json_default(value: object) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Type non sérialisable : {type(value).__name__}")


def _print_run(run: FlowRun, *, detailed: bool, console: Console) -> None:
    console.print("[bold]GitHub Activity → Notion Project Memory[/bold]")
    console.print("[yellow]Phase 1 — plan uniquement, aucune écriture Notion[/yellow]\n")

    if run.result.plan is None:
        console.print(f"[red]Échec :[/red] {run.result.summary}")
    else:
        plan = run.result.plan
        console.print("[bold]Repository[/bold]")
        console.print(f"  {plan.repository.full_name} (ID {plan.repository.repository_id})")
        console.print(f"  ref : {plan.full_ref}\n")
        console.print("[bold]Collecte[/bold]")
        console.print(f"  {plan.commits_read} commits lus")
        console.print(f"  {plan.commits_valid} commits valides")
        console.print(f"  {plan.commits_skipped} commits ignorés\n")
        console.print("[bold]Development Sessions[/bold]")
        console.print(f"  {len(plan.sessions)} sessions calculées")
        console.print(f"  {plan.sessions_closed} clôturées")
        console.print(f"  {plan.sessions_open} ouvertes\n")
        console.print("[bold]Plan[/bold]")
        console.print(f"  {run.result.resources_created} créations planifiées")
        console.print(f"  {len(plan.commit_sessions)} commits à intégrer")
        console.print("  0 écriture exécutée")
        console.print(f"  empreinte : {plan.fingerprint}\n")

        if plan.sessions:
            table = Table(title="Sessions proposées")
            table.add_column("Titre")
            table.add_column("Branche")
            table.add_column("Début")
            table.add_column("Dernière activité")
            table.add_column("État")
            table.add_column("Commits", justify="right")
            for session in plan.sessions:
                table.add_row(
                    session.computed_title,
                    session.primary_ref,
                    session.started_at.isoformat(),
                    session.last_activity_at.isoformat(),
                    session.status,
                    str(len(session.commit_ids)),
                )
            console.print(table)
            for session in plan.sessions:
                console.print(
                    f"\n[bold]{session.computed_title}[/bold] — {session.generated_summary}"
                )

        if detailed:
            detail = Table(title="Effets planifiés")
            detail.add_column("Type")
            detail.add_column("Identité")
            detail.add_column("Description")
            for effect in plan.effects:
                detail.add_row(effect.effect_type, effect.identity, effect.description)
            console.print()
            console.print(detail)
            console.print("\n[bold]Associations commit → session[/bold]")
            for commit_id, session_id in plan.commit_sessions.items():
                console.print(f"  {commit_id} → {session_id}")

        for warning in plan.warnings:
            console.print(f"[yellow]Avertissement :[/yellow] {warning}")

    console.print("\n[bold]Run[/bold]")
    console.print(f"  status : {run.status}")
    console.print(f"  résultat : {run.result.status}")
    console.print(f"  vérification : {run.result.verification}")
    console.print(f"  durée : {run.metrics.get('duration_ms', 0):.2f} ms")
    console.print(f"  idempotency_key : {run.idempotency_key}")


def run_cli(
    argv: Sequence[str] | None = None,
    *,
    console: Console | None = None,
) -> int:
    args = _parser().parse_args(argv)
    output = console or Console()
    flow_input = GitHubProjectMemoryInput(
        repository=args.repository,
        branch=args.branch,
        start_ref=args.start_ref,
        end_ref=args.end_ref,
        max_commits=args.max_commits,
        session_window_hours=args.session_window_hours,
        allowed_repositories=GITHUB_ALLOWED_REPOSITORIES,
    )
    run = plan_github_project_memory(flow_input)
    if args.as_json:
        payload: dict[str, Any] = asdict(run)
        output.print_json(json.dumps(payload, default=_json_default, ensure_ascii=False))
    else:
        _print_run(run, detailed=args.detailed_plan, console=output)
    return 0 if run.status in {"succeeded", "skipped"} else 1


def main() -> None:
    raise SystemExit(run_cli())


if __name__ == "__main__":
    main()
