# 📘 Obsidian → Notion

### **Synchronisation Markdown vers Notion — Hanuman v5**

Cette orchestration permet d’envoyer automatiquement un fichier **Markdown Obsidian** vers une **page Notion**, en respectant les contraintes de l’API Notion (version 2025-09-03) et la structure interne du fichier (titres, listes, citations, code blocks, front-matter…).

C’est l’une des fonctionnalités cœur de **Hanuman v5-dev**, pensée pour un usage personnel avancé, propre, typé (`mypy`), testé (`pytest`), et documenté.

---

# 🧠 1. Principe général

L’orchestration :

1. Lit un fichier `.md` dans ton vault Obsidian
2. Parse proprement :

   - **Front-matter YAML**
   - **Titres** (H1→H6)
   - **Paragraphes**
   - **Listes** (ordonnées & à puces)
   - **Citations**
   - **Code blocks**
   - **Lignes longues** (> 2000 caractères)

3. Convertit tout en **blocs Notion** (JSON)
4. Envoie la donnée à **Notion API** via `pages.create`
5. Crée ou remplace la page dans ton workspace

---

# 📦 2. Installation & Pré-requis

## 2.1. Variables d’environnement (`.env`)

Ton `.env` doit contenir :

```ini
NOTION_TOKEN=secret_...
NOTION_VERSION=2025-09-03
NOTION_PARENT_PAGE_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
# ou :
# NOTION_PARENT_ID=...
```

To check :

```bash
set -a; source .env; set +a
```

Verifier le parent :

```bash
echo $NOTION_PARENT_PAGE_ID
```

Il doit afficher un UUID valide.

---

# 📁 3. Chemin des fichiers

Tu dois passer un chemin absolu :

Exemples :

```bash
/home/prakash/Prakash/obsidian/Privé/Nana.md
/home/prakash/Prakash/obsidian/Travail/ProjetX/Note.md
```

---

# 🚀 4. Usage CLI

Lancer l’orchestration directement en ligne de commande :

```bash
poetry run python -m hanuman.orchestrations.obsidian_to_notion \
  --path "/chemin/vers/fichier.md" \
  --parent-id "$NOTION_PARENT_PAGE_ID"
```

### Sans option `--parent-id`

Si ton `.env` contient `NOTION_PARENT_PAGE_ID`, tu peux simplifier :

```bash
poetry run python -m hanuman.orchestrations.obsidian_to_notion \
  --path "/chemin/vers/fichier.md"
```

Hanuman récupère automatiquement l’ID parent.

---

# ⚡ 5. Via l’API Hanuman (FastAPI)

Depuis ton API :

```bash
make run
```

Endpoint disponible :

```
POST /orchestrations/obsidian-to-notion
```

### Exemple curl

```bash
curl -X POST http://127.0.0.1:8000/orchestrations/obsidian-to-notion \
  -H "Content-Type: application/json" \
  -d '{"path": "/home/prakash/Prakash/obsidian/Privé/Nana.md"}'
```

Réponse JSON :

```json
{
  "status": "success",
  "page_id": "xxxx-xxxx-xxxx-xxxx"
}
```

---

# 🧩 6. Structure interne (technique)

### 6.1. Python module

Chemin :

```
src/hanuman/orchestrations/obsidian_to_notion.py
```

### 6.2. Étapes internes

- `_parse_markdown()`
- `_extract_front_matter()`
- `_convert_markdown_to_notion_blocks()`
- `_chunks()` : découpe < 2000 caractères (limite Notion)
- `_post_create_page()` : requête HTTP → Notion API
- `build_notion_body()` : structure complète (properties + children)
- `send_markdown_to_notion()` : orchestration finale

### 6.3. Standards respectés

- API Notion 2025-09-03
- Limite `2000 chars` / rich_text
- Découpage multi-blocs
- YAML front-matter
- Conversion complète Markdown → Notion Blocks

---

# 📝 7. Gestion du front-matter YAML

Exemple dans Obsidian :

```yaml
---
title: "Nana"
tags: ["famille", "Sri Lanka"]
summary: "Une note importante"
date: "2025-11-13"
custom_field: "Valeur spéciale"
---
```

Dans Notion :

- `title` → propriété `Title`
- `summary` → premier callout
- `tags` → ajoutés dans callout
- `date` → idem
- `custom_field` → listé dans callout
- Le reste → contenu Markdown converti

---

# 🚧 8. Limites actuelles

- Les **images** ne sont pas encore envoyées à Notion (affichées en texte)
- Les **liens internes Obsidian** `[[Page]]` ne sont pas résolus
- Le **merge/update** de pages existantes n’est pas encore géré
- Toujours création d’une nouvelle page

---

# 📈 9. Roadmap v5.1 / v5.2

- Upload automatique des **images**
- Conversion des **liens internes** Obsidian → Notion
- Templates configurables (header, icon, cover)
- Mode "update" (PATCH)
- Création dans une **database** Notion
- Commande courte : `hanuman obsidian-to-notion file.md`

---

# 🧪 10. Tests

Les tests Hanuman couvrent déjà :

- Parsing Markdown
- Fonctions ping
- Orchestrations GitHub→Notion
- Typage strict (`mypy`)
- Lint (`ruff`)
- Tests intégrés (`pytest`)

Obsidian→Notion sera couvert dans `tests/orchestrations/` en v5.1.

---

# 🎉 11. Exemple complet

```bash
set -a; source .env; set +a

poetry run python -m hanuman.orchestrations.obsidian_to_notion \
  --path "/home/prakash/Prakash/obsidian/Privé/Nana.md" \
  --parent-id "2a2e48e8-8d80-80de-9be6-cbd0d2f13b0f"
```

Sortie :

```
[OK] Page Notion créée : https://www.notion.so/Obsidian-xxxxxxxxxxxx
```

---

# ❤️ 12. Philosophie

Cette orchestration est à la fois :

- personnelle
- artisanale
- élégante
- stable
- extensible

Elle incarne la philosophie générale de **Hanuman** :

> "Créer un pont intelligent entre tous les univers de Vincent : Obsidian, Notion, GitHub, OpenAI… avec un code propre, typé, testé, et un style assumé."
