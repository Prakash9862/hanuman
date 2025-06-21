import httpx
from hanuman.core.logging import get_logger
from hanuman.core.token_manager import load_token_json

logger = get_logger(__name__)

GITHUB_API_URL = "https://api.github.com"
NOTION_API_URL = "https://api.notion.com/v1/pages"

REPO_OWNER = "Prakash9862"
REPO_NAME = "hanuman"
NOTION_VERSION = "2022-06-28"

# ========================
# 📥 GitHub API
# ========================

async def get_open_issues():
    url = f"{GITHUB_API_URL}/repos/{REPO_OWNER}/{REPO_NAME}/issues"
    headers = {
            "Authorization": f"Bearer {load_token_json('github')['token']}",
    "Accept": "application/vnd.github+json",
    "User-Agent": "hanuman-sync"
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params={"state": "open"})
        response.raise_for_status()
        issues = response.json()
        logger.info("📥 Issues GitHub récupérées", count=len(issues))
        return issues

# ========================
# 🔁 Transformation
# ========================

def transform_issue_for_notion(issue: dict) -> dict:
    return {
        "parent": {"database_id": load_token_json("notion_db_github_issues")['token']},
        "properties": {
            "Name": {
                "title": [{
                    "text": {
                        "content": issue.get("title", "Issue sans titre")
                    }
                }]
            },
            "URL": {
                "url": issue.get("html_url")
            },
            "Etat": {
                "select": {
                    "name": issue.get("state", "open")
                }
            },
            "Numéro": {
                "number": issue.get("number")
            }
        }
    }

# ========================
# 📤 Notion API
# ========================

async def send_to_notion(payload: dict) -> bool:
    headers = {
        "Authorization": f"Bearer {load_token_json('notion')['token']}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(NOTION_API_URL, headers=headers, json=payload)
        if response.status_code >= 400:
            logger.warning("❌ Échec création page Notion", status=response.status_code, detail=response.text)
            return False
        logger.info("✅ Page Notion créée", status=response.status_code)
        return True

# ========================
# 🎯 Orchestration
# ========================

async def sync_issues_to_notion():
    logger.info("🚀 Début de synchronisation GitHub → Notion")

    try:
        issues = await get_open_issues()
        created = 0

        for issue in issues:
            payload = transform_issue_for_notion(issue)
            success = await send_to_notion(payload)
            if success:
                created += 1

        logger.info("🏁 Synchronisation terminée", total=len(issues), succès=created)
        return {"status": "ok", "total": len(issues), "succès": created}

    except Exception as e:
        logger.error("🔥 Erreur de synchronisation", error=str(e))
        return {"status": "error", "message": str(e)}
