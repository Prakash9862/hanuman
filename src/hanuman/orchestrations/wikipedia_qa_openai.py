from __future__ import annotations

import argparse
import os
from typing import Sequence

from openai import OpenAI  # <- IMPORTANT

from hanuman.services.core.wikipedia_service import WikipediaPage, WikipediaService


def build_wikipedia_context(page: WikipediaPage, max_chars: int = 8000) -> str:
    """Construit un contexte texte à partir d'une WikipediaPage.

    On assemble :
    - titre + URL
    - résumé
    - infobox (si présente)
    - sections avec leur contenu

    Le tout est éventuellement tronqué à max_chars pour éviter d'exploser le contexte du modèle.
    """
    parts: list[str] = []

    parts.append(f"Titre: {page.title}\nURL: {page.url}\n")

    if getattr(page, "summary", None):
        parts.append("Résumé:\n" + page.summary + "\n")

    if getattr(page, "infobox", None):
        parts.append("Infobox:")
        for item in page.infobox:
            parts.append(f"- {item.label}: {item.value}")
        parts.append("")

    if getattr(page, "sections", None):
        for section in page.sections:
            if not section.content:
                continue
            parts.append(f"## {section.title}\n{section.content}\n")

    context = "\n".join(parts).strip()

    if len(context) > max_chars:
        return (
            context[:max_chars]
            + "\n\n[Contexte tronqué pour respecter la limite max_chars]"
        )
    return context


def ask_wikipedia_question(
    topic: str,
    question: str,
    *,
    model: str = "gpt-4.1-mini",
    max_context_chars: int = 8000,
) -> str:
    """Récupère une page Wikipedia et pose une question dessus via OpenAI.

    - topic : titre ou URL de la page Wikipedia
    - question : question en langage naturel
    - model : modèle OpenAI à utiliser
    - max_context_chars : borne de sécurité pour la taille du contexte Wikipedia
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set")

    # 1) Récupération de la page Wikipedia
    wiki = WikipediaService()
    page: WikipediaPage = wiki.fetch_page(topic)

    # 2) Construction du contexte texte
    context = build_wikipedia_context(page, max_chars=max_context_chars)

    # 3) Appel OpenAI avec le nouveau client
    client = OpenAI(api_key=api_key)

    system_prompt = (
        "Tu es un assistant qui répond STRICTEMENT à partir du contexte Wikipédia fourni.\n"
        "Si une information n'est pas présente dans ce contexte, tu expliques que ce n'est "
        "pas précisé dans ces extraits."
    )

    user_prompt = (
        f"CONTEXTE WIKIPEDIA:\n{context}\n\n"
        f"QUESTION:\n{question}\n\n"
        "Réponds en français, de manière structurée, en mentionnant le titre de l'article."
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )

    content = response.choices[0].message.content
    # Selon la version du SDK, content peut être une str ou une liste de segments
    if isinstance(content, list):
        text = "".join(part.text or "" for part in content)
    else:
        text = content or ""

    return text.strip()


def build_parser() -> argparse.ArgumentParser:
    """Construis le parser CLI pour l'orchestration Wikipedia Q&A."""
    parser = argparse.ArgumentParser(
        prog="hanuman.orchestrations.wikipedia_qa_openai",
        description=(
            "Pose une question sur un article Wikipedia et répond via OpenAI "
            "en se basant uniquement sur le contenu de la page."
        ),
    )
    parser.add_argument(
        "--topic",
        required=True,
        help="Titre ou URL de la page Wikipédia à utiliser comme contexte (ex: 'OpenAI').",
    )
    parser.add_argument(
        "--question",
        required=True,
        help="Question à poser à partir de cette page Wikipédia.",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="Nom du modèle OpenAI à utiliser (par défaut: gpt-4o-mini).",
    )
    parser.add_argument(
        "--max-context-chars",
        type=int,
        default=8000,
        help="Longueur maximale du contexte Wikipédia envoyé au modèle.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    """Point d'entrée CLI.

    Exemple :

        poetry run python -m hanuman.orchestrations.wikipedia_qa_openai \
            --topic "OpenAI" \
            --question "Quels sont les objectifs principaux de ce laboratoire ?"
    """
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    answer = ask_wikipedia_question(
        topic=args.topic,
        question=args.question,
        model=args.model,
        max_context_chars=args.max_context_chars,
    )

    print(answer)


if __name__ == "__main__":
    main()
