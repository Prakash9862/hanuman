"""
Compat shim (temporaire) — redirige les imports legacy vers services.orchestrations.
À supprimer après migration complète.
"""

from hanuman.services.orchestrations.github_sync_notion_services import *  # noqa: F401,F403
