import pytest
from playwright.sync_api import Page, expect

from clockwork_frontend_test.utils import BASE_URL


def test_bad_assertion_on_header_title(page: Page):
    """Verify that test fails if we look for an unexpected welcome message."""
    page.goto(f"{BASE_URL}/login/testing?user_id=student00@mila.quebec")
    header_title = page.locator("#formBlock > .container .title.float-start h1")
    with pytest.raises(AssertionError):
        expect(header_title).to_contain_text("Welcome back student01 !")
