import pytest
from dotenv import load_dotenv
load_dotenv()

from hanuman.services.orchestrations import github_sync_notion_services

@pytest.mark.asyncio
async def test_get_open_issues_returns_list():
    issues = await github_sync_notion_services.get_open_issues()
    assert isinstance(issues, list)
    if issues:
        assert "title" in issues[0]
        assert "html_url" in issues[0]
        assert "number" in issues[0]
