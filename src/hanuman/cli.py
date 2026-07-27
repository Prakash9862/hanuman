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
from hanuman.orchestrations.github_project_memory_notion import (
    apply_github_project_memory,
)


def _add_project_memory_arguments(command: argparse.ArgumentParser) -> None:
    command.add_argument("--repository", required=True, help="Dépôt autorisé au format owner/name.")
    command.add_argument("--branch", help="Branche ou ref ; branche par défaut si absente.")
    command.add_argument(
        "--start-ref",
        help="SHA de départ exclusif ; doit être présent dans la plage bornée.",
    )
    command.add_argument(
        "--end-ref",
        help="SHA ou ref de fin inclusif ; la branche est utilisée si absent.",
    )
    command.add_argument(
        "--max-commits",
        type=int,
        default=50,
        help="Nombre maximal de commits collectés, entre 1 et 100 (défaut : 50).",
    )
    command.add_argument(
        "--session-window-hours",
        type=int,
        default=24,
        help="Fenêtre d'inactivité d'une session en heures (défaut : 24).",
    )
    command.add_argument(
        "--session-max-duration-hours",
        type=int,
        default=12,
        help="Durée maximale d'une session en heures (défaut : 12).",
    )
    command.add_argument(
        "--detailed-plan",
        action="store_true",
        help="Afficher les sessions, leurs commits et les effets planifiés.",
    )
    command.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Émettre le Run structuré en JSON.",
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hanuman", description="CLI du hub Hanuman.")
    commands = parser.add_subparsers(dest="command", required=True)
    flows = commands.add_parser("flows", help="Exécuter un Flux Hanuman.")
    flow_commands = flows.add_subparsers(dest="flow", required=True)
    project_memory = flow_commands.add_parser(
        "github-project-memory",
        help="Transformer une activité GitHub bornée en mémoire projet.",
    )
    actions = project_memory.add_subparsers(dest="action", required=True)
    plan = actions.add_parser(
        "plan",
        help="Calculer un plan déterministe sans aucune écriture Notion.",
    )
    apply = actions.add_parser(
        "apply",
        help="Créer les objets absents dans la cible Notion de test puis les vérifier.",
    )
    _add_project_memory_arguments(plan)
    _add_project_memory_arguments(apply)
    return parser


def _json_default(value: object) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Type non sérialisable : {type(value).__name__}")


def _print_run(run: FlowRun, *, detailed: bool, console: Console) -> None:
    console.print("[bold]GitHub Activity → Notion Project Memory[/bold]")
    if run.result.verification == "not_applied":
        console.print("[yellow]Phase 1 — plan uniquement, aucune écriture Notion[/yellow]\n")
    else:
        console.print("[yellow]Phase 2 — synchronisation incrémentale Notion[/yellow]\n")

    if run.result.plan is None:
        console.print(f"[red]Échec :[/red] {run.result.summary}")
    else:
        plan = run.result.plan
        console.print("[bold]Repository[/bold]")
        console.print(
            f"  identité : {plan.repository.full_name} (ID {plan.repository.repository_id})"
        )
        console.print(f"  branche : {plan.full_ref}")
        console.print(f"  borne : {plan.start_ref or 'début'} → {plan.end_ref}")
        console.print(f"  commits : {plan.commits_valid} valides, {plan.commits_skipped} ignorés\n")
        console.print("[bold]Development Sessions[/bold]")
        console.print(f"  {len(plan.sessions)} sessions calculées")
        console.print(f"  {plan.sessions_closed} clôturées")
        console.print(f"  {plan.sessions_open} ouvertes\n")
        console.print("[bold]Effets planifiés[/bold]")
        console.print(f"  {run.result.resources_created} créations planifiées")
        console.print(f"  {len(plan.commit_sessions)} commits à intégrer")
        console.print(f"  {plan.sessions_closed} fermetures")
        if run.result.verification == "not_applied":
            console.print("  0 écriture exécutée")
        else:
            console.print(f"  {run.metrics.get('external_writes', 0)} écriture(s) exécutée(s)")
        console.print(f"  empreinte : {plan.fingerprint}\n")

        if plan.sessions:
            table = Table(title="Sessions proposées")
            table.add_column("Titre")
            table.add_column("Branche")
            table.add_column("Début")
            table.add_column("Dernière activité")
            table.add_column("Durée")
            table.add_column("Ouverture")
            table.add_column("État")
            table.add_column("Commits", justify="right")
            for session in plan.sessions:
                table.add_row(
                    session.computed_title,
                    session.primary_ref,
                    session.started_at.isoformat(),
                    session.last_activity_at.isoformat(),
                    str(session.last_activity_at - session.started_at),
                    session.opening_reason,
                    session.status,
                    str(len(session.commit_ids)),
                )
            console.print(table)
            for session in plan.sessions:
                console.print(
                    f"\n[bold]{session.computed_title}[/bold] — {session.generated_summary}"
                )

        if detailed:
            commits_by_id = {commit.commit_id: commit for commit in plan.commits}
            console.print("\n[bold]Development Sessions — détail[/bold]")
            for index, session in enumerate(plan.sessions, start=1):
                console.print(f"\n  [bold]{index}. {session.computed_title}[/bold]")
                console.print(f"     session_id : {session.session_id}")
                console.print(f"     grouping_key : {session.grouping_key[:12]}…")
                console.print(f"     état : {session.status}")
                console.print(f"     début : {session.started_at.isoformat()}")
                console.print(f"     dernière activité : {session.last_activity_at.isoformat()}")
                console.print(f"     durée : {session.last_activity_at - session.started_at}")
                console.print(f"     ouverture : {session.opening_reason}")
                console.print(f"     commits : {len(session.commit_ids)}")
                for warning in session.warnings:
                    console.print(f"     [yellow]avertissement :[/yellow] {warning}")
                console.print("     [bold]Commits[/bold]")
                for commit_id in session.commit_ids:
                    commit = commits_by_id[commit_id]
                    author = commit.github_author or commit.git_author
                    console.print(
                        f"       - {commit.short_sha} | {commit.committed_at.isoformat()} | "
                        f"{commit.message_subject} | {author} | {commit.url}"
                    )

            grouped_effects: dict[str, list[Any]] = {
                "Repository": [],
                "Development Sessions": [],
                "Fermetures": [],
                "Sans changement": [],
            }
            for effect in plan.effects:
                if effect.effect_type == "repository.create":
                    grouped_effects["Repository"].append(effect)
                elif effect.effect_type == "development_session.close":
                    grouped_effects["Fermetures"].append(effect)
                elif effect.effect_type == "no_change":
                    grouped_effects["Sans changement"].append(effect)
                else:
                    grouped_effects["Development Sessions"].append(effect)
            console.print("\n[bold]Effets planifiés — détail[/bold]")
            for label, effects in grouped_effects.items():
                if not effects:
                    continue
                console.print(f"  [bold]{label}[/bold]")
                for effect in effects:
                    console.print(
                        f"    - {effect.effect_type} | {effect.identity} | " f"{effect.description}"
                    )

        for warning in plan.warnings:
            console.print(f"[yellow]Avertissement :[/yellow] {warning}")

        if run.result.verification != "not_applied":
            console.print("\n[bold]Apply / Verify[/bold]")
            effects = run.result.effects
            for label, prefix in (
                ("Repositories", "repository."),
                ("Development Sessions", "development_session."),
            ):
                console.print(f"  [bold]{label}[/bold]")
                console.print(
                    f"    created : {sum(e.effect_type == prefix + 'create' for e in effects)}"
                )
                console.print(
                    f"    updated : {sum(e.effect_type == prefix + 'update' for e in effects)}"
                )
                console.print(
                    "    unchanged : "
                    f"{sum(e.effect_type == prefix + 'no_change' for e in effects)}"
                )
            console.print("  [bold]Commits[/bold]")
            console.print(f"    added : {run.metrics.get('commits_added', 0)}")
            console.print(f"    already present : {run.metrics.get('commits_already_present', 0)}")
            console.print(f"    ignored : {run.metrics.get('commits_ignored', 0)}")
            console.print("  [bold]Verification[/bold]")
            console.print(f"    {run.result.verification}")
            for effect in run.result.effects:
                console.print(
                    f"  - {effect.effect_type} | {effect.identity} | {effect.description}"
                )
            for detail in run.result.verification_details:
                console.print(f"  {detail}")

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
        session_max_duration_hours=args.session_max_duration_hours,
        allowed_repositories=GITHUB_ALLOWED_REPOSITORIES,
    )
    run = (
        apply_github_project_memory(flow_input)
        if args.action == "apply"
        else plan_github_project_memory(flow_input)
    )
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
