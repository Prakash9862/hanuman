from __future__ import annotations

import argparse
import os
from typing import Any, Dict, List, Sequence

import requests
from openai import OpenAI

from hanuman.services.core.wikipedia_service import WikipediaPage, WikipediaService

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

# On part sur Wikipédia FR par défaut (cohérent avec ton usage actuel).
WIKIPEDIA_API_URL = "https://fr.wikipedia.org/w/api.php"


# ---------------------------------------------------------------------------
# Construction du contexte Wikipédia
# ---------------------------------------------------------------------------


def build_wikipedia_context(page: WikipediaPage, max_chars: int = 8000) -> str:
    """Construit un contexte texte à partir d'une WikipediaPage.

    On assemble :
    - titre + URL
    - résumé
    - infobox (si présente)
    - sections avec leur contenu

    Le tout est éventuellement tronqué à max_chars pour éviter d'exploser le contexte.
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
        return context[:max_chars] + "\n\n[Contexte tronqué pour respecter la limite max_chars]"
    return context


# ---------------------------------------------------------------------------
# Appel OpenAI
# ---------------------------------------------------------------------------


def call_openai_with_context(
    context: str,
    question: str,
    *,
    model: str = "gpt-4o-mini",
) -> str:
    """Envoie le contexte Wikipédia + la question à OpenAI et renvoie la réponse texte."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set")

    client = OpenAI(api_key=api_key)

    system_prompt = (
        "Tu es un assistant qui répond STRICTEMENT à partir du contexte Wikipédia fourni.\n"
        "Si une information n'est pas présente dans ce contexte, tu expliques que ce n'est "
        "pas précisé dans ces extraits.\n"
        "Tu réponds en français, de manière structurée, et tu cites clairement les articles utilisés."
    )

    user_prompt = (
        f"CONTEXTE WIKIPEDIA:\n{context}\n\n"
        f"QUESTION:\n{question}\n\n"
        "Réponds en français, de manière structurée."
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
    if isinstance(content, list):
        # Selon les versions du SDK, content peut être une liste de segments
        text = "".join(part.text or "" for part in content)
    else:
        text = content or ""

    return text.strip()


# ---------------------------------------------------------------------------
# Recherche Wikipédia via l’API HTTP (sans toucher au WikipediaService)
# ---------------------------------------------------------------------------


def search_wikipedia(
    query: str,
    *,
    max_results: int = 5,
) -> List[Dict[str, Any]]:
    """Utilise directement l'API de Wikipédia pour trouver des pages pertinentes."""

    params: Dict[str, str] = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json",
        "srlimit": str(max_results),
        "utf8": "1",
    }

    headers = {"User-Agent": "HanumanBot/1.0 (https://github.com/Prakash9862/hanuman)"}

    try:
        resp = requests.get(
            WIKIPEDIA_API_URL,
            params=params,
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"Erreur lors de l'appel à l'API Wikipédia: {exc}") from exc

    data = resp.json()
    results_raw = data.get("query", {}).get("search", [])

    results: List[Dict[str, Any]] = []
    for item in results_raw:
        title = item.get("title", "")
        snippet = item.get("snippet", "")
        url = f"https://fr.wikipedia.org/wiki/{title.replace(' ', '_')}"
        results.append({"title": title, "snippet": snippet, "url": url})

    return results


def fetch_page_by_title(title: str) -> WikipediaPage:
    """Récupère une page complète via le WikipediaService existant."""
    wiki = WikipediaService()
    return wiki.fetch_page(title)


# ---------------------------------------------------------------------------
# Logique de Q&A « niveau 1 : une seule page »
# ---------------------------------------------------------------------------


def answer_from_single_page_title(
    title: str,
    question: str,
    *,
    model: str = "gpt-4o-mini",
    max_context_chars: int = 8000,
) -> tuple[str, str]:
    """Construit une réponse à partir d'un seul article Wikipédia (par son titre).

    Retourne (answer, source_url)
    """
    page = fetch_page_by_title(title)
    context = build_wikipedia_context(page, max_chars=max_context_chars)
    answer = call_openai_with_context(context, question, model=model)
    return answer, page.url


# ---------------------------------------------------------------------------
# Logique de Q&A « multi-articles » pour les mots-clés
# ---------------------------------------------------------------------------


def answer_from_keywords(
    keywords: str,
    question: str,
    *,
    model: str = "gpt-4o-mini",
    max_results: int = 3,
    max_context_chars: int = 12000,
) -> tuple[str, List[str]]:
    """Recherche plusieurs articles à partir de mots-clés, agrège le contexte et répond.

    Retourne (answer, sources_urls)
    """
    search_results = search_wikipedia(keywords, max_results=max_results)
    if not search_results:
        raise RuntimeError(f"Aucun article trouvé pour les mots-clés: {keywords}")

    titles = [r["title"] for r in search_results]
    pages: List[WikipediaPage] = []

    wiki = WikipediaService()
    for title in titles:
        try:
            pages.append(wiki.fetch_page(title))
        except Exception:
            # On ignore silencieusement une page qui planterait
            continue

    if not pages:
        raise RuntimeError("Impossible de récupérer les pages Wikipédia correspondantes.")

    # Répartition grossière de la taille max par article
    per_page_limit = max(2000, max_context_chars // max(len(pages), 1))
    context_parts: List[str] = []
    urls: List[str] = []

    for page in pages:
        urls.append(page.url)
        ctx = build_wikipedia_context(page, max_chars=per_page_limit)
        context_parts.append(f"===== ARTICLE: {page.title} =====\n{ctx}")

    big_context = "\n\n".join(context_parts)
    answer = call_openai_with_context(big_context, question, model=model)
    return answer, urls


# ---------------------------------------------------------------------------
# CLI « historique » (topic explicite) pour compatibilité
# ---------------------------------------------------------------------------


def ask_wikipedia_question(
    topic: str,
    question: str,
    *,
    model: str = "gpt-4o-mini",
    max_context_chars: int = 8000,
) -> str:
    """Version simple : on passe un titre ou URL et une question (mode non interactif)."""
    page = fetch_page_by_title(topic)
    context = build_wikipedia_context(page, max_chars=max_context_chars)
    return call_openai_with_context(context, question, model=model)


def build_parser() -> argparse.ArgumentParser:
    """Parser CLI non interactif (optionnel).

    Si on appelle le module SANS argument -> mode interactif.
    Si on met --topic/--question -> mode non interactif.
    """
    parser = argparse.ArgumentParser(
        prog="hanuman.orchestrations.wikipedia_qa_openai",
        description=(
            "Pose une question sur Wikipédia en utilisant OpenAI. "
            "Peut être utilisé de manière interactive (par défaut) ou avec --topic/--question."
        ),
    )
    parser.add_argument(
        "--topic",
        help="Titre (ou URL) d'un article Wikipédia précis.",
    )
    parser.add_argument(
        "--question",
        help="Question à poser à partir de cette page.",
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


# ---------------------------------------------------------------------------
# Mode interactif terminal (ce que tu veux utiliser)
# ---------------------------------------------------------------------------


def run_interactive() -> None:
    """Boucle interactive dans le terminal.

    1 → tu poses UNE question libre, je cherche les articles pertinents.
    2 → tu donnes des mots-clés + une question, je croise plusieurs articles.
    ENTER → quitte.
    """
    print("=== Wikipedia Q&A (auto-search) ===")
    print("1 → Poser UNE question libre (je ne donne pas de titre d'article).")
    print("2 → Donner un ou plusieurs mots-clés, et poser une question.")
    print("ENTER directement → quitter.\n")

    while True:
        mode = input("Choisis un mode [1/2, ENTER pour quitter] : ").strip()
        if not mode:
            print("Bye 👋")
            return

        if mode not in {"1", "2"}:
            print("Mode invalide. Tape 1, 2 ou ENTER pour quitter.")
            continue

        if mode == "1":
            # Question libre → recherche automatique d'un article pertinent
            question = input("Ta question (ENTER pour quitter) : ").strip()
            if not question:
                print("Bye 👋")
                return

            print("\n🔎 Recherche des articles Wikipédia pertinents…")
            results = search_wikipedia(question, max_results=5)
            if not results:
                print("Aucun article trouvé pour cette question.")
                continue

            print("\nArticles trouvés :")
            for idx, r in enumerate(results, start=1):
                print(f"{idx}. {r['title']} — {r['url']}")

            choice_raw = input("\nChoisis un article [numéro, ENTER pour annuler] : ").strip()
            if not choice_raw:
                print("Annulé.\n")
                continue

            try:
                choice = int(choice_raw)
            except ValueError:
                print("Numéro invalide.\n")
                continue

            if choice < 1 or choice > len(results):
                print("Numéro hors limites.\n")
                continue

            selected = results[choice - 1]
            title = selected["title"]
            url = selected["url"]

            print(f"\n📚 Utilisation de l'article: {title} ({url})")
            try:
                answer, _ = answer_from_single_page_title(
                    title,
                    question,
                    model="gpt-4o-mini",
                    max_context_chars=8000,
                )
            except Exception as exc:  # noqa: BLE001
                print(f"Erreur lors de la génération de la réponse: {exc}\n")
                continue

            print("\n================= RÉPONSE =================")
            print(f"[Source principale: {url}]")
            print("------------------------------------------")
            print(answer)
            print("==========================================\n")

        else:
            # mode == "2" : mots-clés + question, multi-articles
            keywords = input("Mots-clés (séparés par des espaces, ENTER pour quitter) : ").strip()
            if not keywords:
                print("Bye 👋")
                return

            question = input("Question à partir de ces mots-clés : ").strip()
            if not question:
                print("Bye 👋")
                return

            print("\n🔎 Recherche de plusieurs articles Wikipédia…")
            try:
                answer, urls = answer_from_keywords(
                    keywords,
                    question,
                    model="gpt-4o-mini",
                    max_results=3,
                    max_context_chars=12000,
                )
            except Exception as exc:  # noqa: BLE001
                print(f"Erreur lors de la génération de la réponse: {exc}\n")
                continue

            print("\n================= RÉPONSE =================")
            print("Sources Wikipédia utilisées :")
            for u in urls:
                print(f"- {u}")
            print("------------------------------------------")
            print(answer)
            print("==========================================\n")


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> None:
    """
    - Si le module est appelé SANS arguments → mode interactif.
    - Si on passe des arguments CLI → mode non interactif (--topic / --question).
    """
    import sys

    raw_argv = list(sys.argv[1:] if argv is None else argv)
    if not raw_argv:
        # Mode interactif
        run_interactive()
        return

    # Mode non interactif « historique »
    parser = build_parser()
    args = parser.parse_args(raw_argv)

    if not args.topic or not args.question:
        parser.error("En mode non interactif, --topic et --question sont requis.")

    answer = ask_wikipedia_question(
        topic=args.topic,
        question=args.question,
        model=args.model,
        max_context_chars=args.max_context_chars,
    )
    print(answer)


if __name__ == "__main__":
    main()
