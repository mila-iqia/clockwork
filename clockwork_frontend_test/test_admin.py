from slurm_state.mongo_client import get_mongo_client
from slurm_state.config import get_config
from playwright.sync_api import Page, expect

from clockwork_frontend_test.utils import BASE_URL
from clockwork_web.core.users_helper import get_account_fields


class UsersFactory:
    def __init__(self):
        client = get_mongo_client()
        db = client[get_config("mongo.database_name")]
        self.users_collection = db["users"]

    def _get_users(self) -> list[dict]:
        return sorted(
            self.users_collection.find({}), key=lambda user: user["mila_email_username"]
        )

    def get_an_admin_user(self) -> dict:
        admin_users = [
            user for user in self._get_users() if user.get("admin_access", False)
        ]
        return admin_users[0]

    def get_a_non_admin_user(self, exclude=()):
        users = [
            user for user in self._get_users() if not user.get("admin_access", False)
        ]
        if exclude:
            users = [
                user for user in users if user["mila_email_username"] not in exclude
            ]
        return users[0]


def test_admin_access_for_admin(page: Page):
    users_factory = UsersFactory()
    admin_user = users_factory.get_an_admin_user()
    admin_email = admin_user["mila_email_username"]
    random_user = users_factory.get_a_non_admin_user(exclude=admin_email)
    # login
    page.goto(f"{BASE_URL}/login/testing?user_id={admin_email}")
    # Go to settings to set language to english if necessary.
    page.goto(f"{BASE_URL}/settings/")
    # Get language select.
    select = page.locator("select#language_selection")
    # Switch to english.
    lang = select.input_value()
    if lang != "en":
        select.select_option("en")
        # Check english is selected.
        expect(select).to_have_value("en")

    page.goto(f"{BASE_URL}/admin/panel")
    expect(page.get_by_text("Administration panel")).to_have_count(1)
    page.goto(f"{BASE_URL}/admin/users")
    expect(page.get_by_text("Administration panel / Users")).to_have_count(1)
    page.goto(f"{BASE_URL}/admin/user?username={random_user['mila_email_username']}")
    expect(
        page.get_by_text(
            f"Administration panel / Users / {random_user['mila_email_username']}"
        )
    ).to_have_count(1)

    # Back to default language
    if lang != "en":
        page.goto(f"{BASE_URL}/settings/")
        select = page.locator("select#language_selection")
        select.select_option(lang)
        expect(select).to_have_value(lang)


def test_admin_access_for_admin_french(page: Page):
    users_factory = UsersFactory()
    admin_user = users_factory.get_an_admin_user()
    admin_email = admin_user["mila_email_username"]
    random_user = users_factory.get_a_non_admin_user(exclude=admin_email)
    # login
    page.goto(f"{BASE_URL}/login/testing?user_id={admin_email}")
    # Go to settings to set language to english if necessary.
    page.goto(f"{BASE_URL}/settings/")
    # Get language select.
    select = page.locator("select#language_selection")
    # Switch to French.
    lang = select.input_value()
    if lang != "fr":
        select.select_option("fr")
        # Check english is selected.
        expect(select).to_have_value("fr")

    page.goto(f"{BASE_URL}/admin/panel")
    expect(page.get_by_text("Panneau d'administration")).to_have_count(1)
    page.goto(f"{BASE_URL}/admin/users")
    expect(page.get_by_text("Panneau d'administration / Utilisateurs")).to_have_count(1)
    page.goto(f"{BASE_URL}/admin/user?username={random_user['mila_email_username']}")
    expect(
        page.get_by_text(
            f"Panneau d'administration / Utilisateurs / {random_user['mila_email_username']}"
        )
    ).to_have_count(1)

    # Back to default language
    if lang != "fr":
        page.goto(f"{BASE_URL}/settings/")
        select = page.locator("select#language_selection")
        select.select_option(lang)
        expect(select).to_have_value(lang)


def test_admin_access_for_non_admin(page: Page):
    users_factory = UsersFactory()
    random_user = users_factory.get_a_non_admin_user()
    random_email = random_user["mila_email_username"]
    # Login
    page.goto(f"{BASE_URL}/login/testing?user_id={random_email}")
    # Go to settings to set language to english if necessary.
    page.goto(f"{BASE_URL}/settings/")
    # Get language select.
    select = page.locator("select#language_selection")
    # Switch to english.
    lang = select.input_value()
    if lang != "en":
        select.select_option("en")
        # Check english is selected.
        expect(select).to_have_value("en")

    page.goto(f"{BASE_URL}/admin/panel")
    expect(page.get_by_text("Administration panel")).to_have_count(0)
    expect(page.get_by_text("Authorization error.")).to_have_count(1)
    page.goto(f"{BASE_URL}/admin/users")
    expect(page.get_by_text("Administration panel / Users")).to_have_count(0)
    expect(page.get_by_text("Authorization error.")).to_have_count(1)
    page.goto(f"{BASE_URL}/admin/user?username={random_user['mila_email_username']}")
    expect(
        page.get_by_text(
            f"Administration panel / Users / {random_user['mila_email_username']}"
        )
    ).to_have_count(0)
    expect(page.get_by_text("Authorization error.")).to_have_count(1)

    # Back to default language
    if lang != "en":
        page.goto(f"{BASE_URL}/settings/")
        select = page.locator("select#language_selection")
        select.select_option(lang)
        expect(select).to_have_value(lang)


def test_admin_pages(page: Page):
    users_factory = UsersFactory()
    admin_user = users_factory.get_an_admin_user()
    admin_email = admin_user["mila_email_username"]

    # Login
    page.goto(f"{BASE_URL}/login/testing?user_id={admin_email}")
    # Go to settings to set language to english if necessary.
    page.goto(f"{BASE_URL}/settings/")
    # Get language select.
    select = page.locator("select#language_selection")
    # Switch to english.
    lang = select.input_value()
    if lang != "en":
        select.select_option("en")
        # Check english is selected.
        expect(select).to_have_value("en")

    # Select "Admin" menu and click on it
    menu_external = page.locator(
        "#navbarSupportedContent li.nav-item.dropdown", has_text="EXTERNAL"
    )
    expect(menu_external).to_have_count(1)
    menu_external.click()
    link_admin = menu_external.locator(
        "ul.dropdown-menu.show li a.dropdown-item", has_text="Admin"
    )
    expect(link_admin).to_have_count(1)
    # CLicking on "Admin" link opens a new page we must capture.
    # Playwright doc here: https://playwright.dev/python/docs/pages#handling-new-pages
    with page.context.expect_page() as new_page_info:
        link_admin.click()
    new_page = new_page_info.value
    expect(new_page).to_have_url(f"{BASE_URL}/admin/panel")

    # Go to page "Manage users"
    link_manage_users = new_page.locator("a.btn", has_text="Manage users")
    expect(link_manage_users).to_have_count(1)
    link_manage_users.click()
    expect(new_page).to_have_url(f"{BASE_URL}/admin/users")

    # Select user data from table first row
    rows = new_page.locator("table tbody tr")
    row = rows.nth(0)
    expect(row).to_have_count(1)
    columns = row.locator("td")
    user_email = columns.nth(0).text_content().strip()
    user_edit_button = columns.last.locator("a")
    assert user_email.endswith("@mila.quebec")
    expect(user_edit_button).to_have_text("edit")

    # Go to edition page for selected user
    user_edit_button.click()
    expect(new_page).to_have_url(f"{BASE_URL}/admin/user?username={user_email}")

    # Get default usernames
    account_fields = get_account_fields()
    old_usernames = {}
    for user_field in account_fields:
        user_input = new_page.locator(f"form table input[name={user_field}]")
        expect(user_input).to_have_count(1)
        old_usernames[user_field] = user_input.input_value()

    # Edit user
    new_usernames = {
        user_field: f"{username}_new" for user_field, username in old_usernames.items()
    }
    for user_field in account_fields:
        new_page.locator(f"form table input[name={user_field}]").fill(
            new_usernames[user_field]
        )
    # Submit form
    button_submit = new_page.locator("button", has_text="Save")
    expect(button_submit).to_have_count(1)
    button_submit.click()
    expect(new_page).to_have_url(f"{BASE_URL}/admin/user?username={user_email}")
    expect(new_page.get_by_text("User successfully updated.")).to_have_count(1)

    # Check new input values
    for user_field in account_fields:
        user_input = new_page.locator(f"form table input[name={user_field}]")
        expect(user_input).to_have_value(new_usernames[user_field])

    # Edit user back to default values
    for user_field in account_fields:
        new_page.locator(f"form table input[name={user_field}]").fill(
            old_usernames[user_field]
        )
    new_page.locator("button", has_text="Save").click()
    expect(new_page).to_have_url(f"{BASE_URL}/admin/user?username={user_email}")
    expect(new_page.get_by_text("User successfully updated.")).to_have_count(1)
    for user_field in account_fields:
        user_input = new_page.locator(f"form table input[name={user_field}]")
        expect(user_input).to_have_value(old_usernames[user_field])

    # Check what happens when submitting form with default values
    new_page.locator("button", has_text="Save").click()
    expect(new_page).to_have_url(f"{BASE_URL}/admin/user?username={user_email}")
    expect(new_page.get_by_text("No change for this user.")).to_have_count(1)
    for user_field in account_fields:
        user_input = new_page.locator(f"form table input[name={user_field}]")
        expect(user_input).to_have_value(old_usernames[user_field])

    # Back to default language
    if lang != "en":
        page.goto(f"{BASE_URL}/settings/")
        select = page.locator("select#language_selection")
        select.select_option(lang)
        expect(select).to_have_value(lang)
