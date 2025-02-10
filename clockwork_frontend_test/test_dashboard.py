from playwright.sync_api import Page, expect

from clockwork_frontend_test.utils import (
    BASE_URL,
    get_fake_data,
    get_default_display_date,
)


# Expected dashboard table content for first columns (cluster, job ID, job name [:20], job state, submit time).
# NB: Time zone may differ inside and outside Docker.
# Using `python -c "import datetime; print(datetime.datetime.now().astimezone().tzinfo)"`,
# we get "UTC" in docker and "EST" outside. So, dates like "submit time" are not the same
# when accessing server pages either inside or outside Docker.
# For tests, we use dates inside Docker.

# Retrieve data we are interested in from the fake data
fake_data = get_fake_data()

DASHBOARD_TABLE_CONTENT = []
for job in fake_data["jobs"]:
    if job["cw"]["mila_email_username"] == "student00@mila.quebec":
        # This element could be an array of states, or a simple string.
        # For now, each array we encountered contained only one element.
        job_states = job["slurm"]["job_state"]

        DASHBOARD_TABLE_CONTENT.append(
            [
                job["slurm"]["cluster_name"],
                int(
                    job["slurm"]["job_id"]
                ),  # job ID is currently handled as a numeric value
                job["slurm"]["name"],
                job_states[0].lower()
                if isinstance(job_states, list)
                else job_states.lower(),
                get_default_display_date(job["slurm"]["submit_time"]),
                get_default_display_date(job["slurm"]["start_time"]),
                get_default_display_date(job["slurm"]["end_time"]),
                # Then, there is the "Links" column: we don't add content yet,
                # but here is a placeholder for future testing
            ]
        )

# SORTED_CONTENT is saved between two clicks on the dashboard
# This variable keeps its current state
SORTED_CONTENT = DASHBOARD_TABLE_CONTENT

"""
Example of DASHBOARD_TABLE_CONTENT:

DASHBOARD_TABLE_CONTENT = [
    ["graham", "213472", "somejobname_689441", "timeout", "2023/04/08 23:44"],
    ["mila", "914405", "somejobname_240391", "running", "2021/02/19 14:04"],
    ["narval", "429092", "somejobname_23649", "pending", "2023/04/13 15:41"],
    ["mila", "988661", "somejobname_989621", "cancelled", "2023/06/02 06:32"],
    ["mila", "688953", "somejobname_414417", "cancelled", "2023/05/29 01:33"],
]
"""


def test_login_and_logout(page: Page):
    """Test logout button in top right menu."""
    # Check we are logged in.
    page.goto(f"{BASE_URL}/login/testing?user_id=student00@mila.quebec")
    header_title = page.locator("#formBlock > .container .title.float-start h1")
    expect(header_title).to_contain_text("Welcome back student00 !")
    # We should not find logout text in page.
    assert not page.get_by_text(
        "Please log in with your @mila.quebec account. This will create a key for the REST API automatically."
    ).count()

    # Logout and check.
    login_menu = page.locator(".container-fluid .col.login .btn-group.dropstart")
    expect(login_menu).to_have_count(1)
    login_menu.click()
    logout_button = login_menu.locator(".dropdown-menu.show a.btn")
    expect(logout_button).to_be_visible()
    expect(logout_button).to_contain_text("Logout?")
    logout_button.click()

    expect(page).to_have_url(f"{BASE_URL}/")
    # We must then find logout text in page.
    assert page.get_by_text(
        "Please log in with your @mila.quebec account. This will create a key for the REST API automatically."
    ).count()


def test_button_see_all_jobs(page: Page):
    """Test that clicking on button `see all jobs` opens page jobs/search."""
    page.goto(f"{BASE_URL}/login/testing?user_id=student00@mila.quebec")
    expect(page.get_by_text("search")).to_have_count(0)

    button = page.locator("#formBlock > .container .row.dashboard_job .btn.btn-red")
    expect(button).to_have_count(1)
    expect(button).to_contain_text("See all jobs")
    button.click()
    expect(page).to_have_url(f"{BASE_URL}/jobs/search")
    assert page.get_by_text("search").count()


def test_dashboard_table_default_content(page: Page):
    """Check default content for dashboard table"""
    page.goto(f"{BASE_URL}/login/testing?user_id=student00@mila.quebec")
    # Find table
    table = page.locator("table#dashboard_table")
    expect(table).to_have_count(1)
    # Check columns
    headers = table.locator("thead tr th")
    expect(headers).to_have_count(8)
    expect(headers.nth(0)).to_contain_text("Cluster")
    expect(headers.nth(1)).to_contain_text("Job ID")
    expect(headers.nth(2)).to_contain_text("Job name [:20]")
    expect(headers.nth(3)).to_contain_text("Job state")
    expect(headers.nth(4)).to_contain_text("Submit time")
    expect(headers.nth(5)).to_contain_text("Start time")
    expect(headers.nth(6)).to_contain_text("End time")
    expect(headers.nth(7)).to_contain_text("Links")
    # Check rows
    rows = table.locator("tbody tr")
    expect(rows).to_have_count(len(DASHBOARD_TABLE_CONTENT))

    for index_row, content_row in enumerate(DASHBOARD_TABLE_CONTENT):
        cols = rows.nth(index_row).locator("td")
        expect(cols).to_have_count(8)
        for index_col, content_col in enumerate(content_row):
            expect(cols.nth(index_col)).to_contain_text(str(content_col))


def test_dashboard_table_sorting(page: Page):
    """Test dashboard table are sorted when clicking on column headers."""
    page.goto(f"{BASE_URL}/login/testing?user_id=student00@mila.quebec")

    # Check default sorting
    _check_dashboard_table(page, DASHBOARD_TABLE_CONTENT)

    _check_dashboard_table_sorting(page, 0, "Cluster", False)
    _check_dashboard_table_sorting(page, 0, "Cluster", True)

    # NB: When clicking on column Job ID for first time, column will be sorted in reverse order because it's numbers.
    # This is inherited from Sortable tool (see function `onClickSortableColumn` in `dashboard.js`):
    # https://github.com/mila-iqia/clockwork/blob/9bea5246737bd5df407ea118359ab1da0b8caa9a/clockwork_web/static/js/dashboard.js#L424
    _check_dashboard_table_sorting(page, 1, "Job ID", True)
    _check_dashboard_table_sorting(page, 1, "Job ID", False)

    _check_dashboard_table_sorting(page, 2, "Job name [:20]", False)
    _check_dashboard_table_sorting(page, 2, "Job name [:20]", True)

    _check_dashboard_table_sorting(page, 3, "Job state", False)
    _check_dashboard_table_sorting(page, 3, "Job state", True)

    # NB: Submit time is also a number column, so first click will sort in reverse order.
    _check_dashboard_table_sorting(page, 4, "Submit time", True)
    _check_dashboard_table_sorting(page, 4, "Submit time", False)


def _check_dashboard_table_sorting(
    page: Page, column_id: int, column_text, reverse: bool
):
    """Click on relevant header to sort dashboard table according to given parameters, then check sorting.

    To check sorted table, we manually sort SORTED_CONTENT (initially DASHBOARD_TABLE_CONTENT) and use it as expected result.

    NB:
    Dashboard table content is sorted by Javascript tool `Sortable`,
    which takes into account initial row order, especially if
    sorted column contains a same value many times.
    So, to sort SORTED_CONTENT, we must use both sorted column and initial row order.
    """
    global SORTED_CONTENT
    # Create a temporary sortable content by adding initial row order at the end of each row,
    # then sort using column ID and row order (located in last column).
    sorted_content = sorted(
        [row + [index_row] for index_row, row in enumerate(SORTED_CONTENT)],
        key=lambda row: (row[column_id], row[-1]),
        reverse=reverse,
    )

    # Remove last column (row order) to get only expected content.
    content = [row[:-1] for row in sorted_content]
    SORTED_CONTENT = content

    # Expected content is now ready for checking.
    table = page.locator("table#dashboard_table")
    headers = table.locator("thead tr th")
    header = headers.nth(column_id)
    expect(header).to_contain_text(column_text)
    header.click()
    _check_dashboard_table(page, content, column_id=column_id)


def _check_dashboard_table(page: Page, table_content: list, column_id: int = None):
    """Check dashboard table contains expected table content.

    table_content is a list or rows, each row is a list of texts expected in related columns.
    """
    table = page.locator("table#dashboard_table")
    expect(table).to_have_count(1)
    rows = table.locator("tbody tr")
    expect(rows).to_have_count(len(DASHBOARD_TABLE_CONTENT))
    for index_row, content_row in enumerate(table_content):
        cols = rows.nth(index_row).locator("td")
        expect(cols).to_have_count(8)
        if column_id is None:
            for index_col, content_col in enumerate(content_row):
                expect(cols.nth(index_col)).to_contain_text(str(content_col))
        else:
            expect(cols.nth(column_id)).to_contain_text(str(content_row[column_id]))
