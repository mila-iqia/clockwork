import os
import pytest
from playwright.sync_api import Page, expect


# Generate base url depending on whether we are inside docker container or not.
IN_DOCKER = os.environ.get("WE_ARE_IN_DOCKER", False)
BASE_URL = f"http://127.0.0.1:{5000 if IN_DOCKER else 15000}"


def test_login(page: Page):
    """Test login with student00 and verify page contains expected welcome message."""
    page.goto(f"{BASE_URL}/login/testing?user_id=student00@mila.quebec")
    header_title = page.locator("#formBlock > .container .title.float-start h1")
    expect(header_title).to_contain_text("Welcome back student00 !")


def test_bad_assertion_on_header_title(page: Page):
    """Verify that test fails if we look for an unexpected welcome message."""
    page.goto(f"{BASE_URL}/login/testing?user_id=student00@mila.quebec")
    header_title = page.locator("#formBlock > .container .title.float-start h1")
    with pytest.raises(AssertionError):
        expect(header_title).to_contain_text("Welcome back student01 !")


def test_see_all_jobs(page: Page):
    """Test click on `see all jobs` button."""
    page.goto(f"{BASE_URL}/login/testing?user_id=student00@mila.quebec")
    expect(page.get_by_text("search")).to_have_count(0)

    button = page.locator("#formBlock > .container .row.dashboard_job .btn.btn-red")
    expect(button).to_have_count(1)
    expect(button).to_contain_text("See all jobs")
    button.click()
    expect(page).to_have_url(f"{BASE_URL}/jobs/search")
    assert page.get_by_text("search").count()
