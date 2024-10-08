from playwright.sync_api import Page, expect

from clockwork_frontend_test.utils import BASE_URL, get_fake_data
from clockwork_web.core.jobs_helper import get_inferred_job_state

current_username = "student06@mila.quebec"

# Retrieve data we are interested in from the fake data
fake_data = get_fake_data()

# Sorts the jobs by submit time
sorted_jobs = sorted(
    fake_data["jobs"], key=lambda j: (-j["slurm"]["submit_time"], j["slurm"]["job_id"])
)

sorted_mila_jobs = []
for job in sorted_jobs:
    if (
        job["slurm"]["cluster_name"] == "mila"
    ):  # student06@mila.quebec has access to the Mila cluster only
        sorted_mila_jobs.append(job)

# Get all the jobs visible by student06 and format them for our tests
MILA_JOBS = []
for job in sorted_mila_jobs:
    MILA_JOBS.append(
        [
            job["slurm"]["cluster_name"],
            (
                job["cw"]["mila_email_username"].replace("@", " @")
                if job["cw"]["mila_email_username"] is not None
                else ""
            ),
            job["slurm"]["job_id"],
        ]
    )

# Expected jobs table content for first columns (cluster, user (@mila.quebec), job ID).
JOBS_SEARCH_DEFAULT_TABLE = MILA_JOBS[:40]


def _load_jobs_search_page(page: Page):
    """Login with student06 and go to jobs search page."""
    # Login
    page.goto(f"{BASE_URL}/login/testing?user_id=student06@mila.quebec")
    # Go to jobs/search page
    page.goto(f"{BASE_URL}/jobs/search")


def _check_jobs_table(page: Page, table_content: list):
    """Check jobs table contains expected table content.

    table_content is a list or rows, each row is a list of texts expected in related columns.
    """
    table = page.locator("table#search_table")
    expect(table).to_have_count(1)
    rows = table.locator("tbody tr")
    expect(rows).to_have_count(len(table_content))
    for index_row, content_row in enumerate(table_content):
        cols = rows.nth(index_row).locator("td")
        assert cols.count() >= len(content_row)
        for index_col, content_col in enumerate(content_row):
            expect(cols.nth(index_col)).to_contain_text(content_col)


def _get_search_button(page: Page):
    """Get search button in jobs search page."""
    search_button = page.get_by_text("Run search")
    expect(search_button).to_be_visible()
    expect(search_button).to_have_attribute("type", "submit")
    return search_button


def test_jobs_search_default(page: Page):
    """Test default table content in jobs/search page."""
    _load_jobs_search_page(page)
    # Check table
    table = page.locator("table#search_table")
    expect(table).to_be_visible()
    # Check table headers
    headers = table.locator("thead th")
    expect(headers).to_have_count(10)
    expect(headers.nth(0)).to_contain_text("Cluster")
    expect(headers.nth(1)).to_contain_text("User (@mila.quebec)")
    expect(headers.nth(2)).to_contain_text("Job ID")
    expect(headers.nth(3)).to_contain_text("Job array")
    expect(headers.nth(4)).to_contain_text("Job name [:20]")
    expect(headers.nth(5)).to_contain_text("Job state")
    expect(headers.nth(6)).to_contain_text("Submit time")
    expect(headers.nth(7)).to_contain_text("Start time")
    expect(headers.nth(8)).to_contain_text("End time")
    expect(headers.nth(9)).to_contain_text("Links")
    # Check table content
    _check_jobs_table(page, JOBS_SEARCH_DEFAULT_TABLE)


def test_filter_by_user_only_me(page: Page):
    _load_jobs_search_page(page)
    radio_button_only_me = page.locator("input#user_option_only_me")
    expect(radio_button_only_me).to_be_visible()
    expect(radio_button_only_me).to_be_checked(checked=False)
    radio_button_only_me.click()
    expect(radio_button_only_me).to_be_checked(checked=True)
    _get_search_button(page).click()
    expect(page).to_have_url(
        f"{BASE_URL}/jobs/search?"
        f"username={current_username}"
        f"&cluster_name=mila"
        f"&aggregated_job_state=COMPLETED,RUNNING,PENDING,FAILED"
        f"&nbr_items_per_page=40"
        f"&sort_by=submit_time"
        f"&sort_asc=-1"
    )
    expected_results = [
        job for job in MILA_JOBS if job[1] == current_username.replace("@", " @")
    ][:40]
    _check_jobs_table(
        page,
        expected_results,
    )

    # Back to all users.
    radio_button_all_users = page.locator("input#user_option_all")
    expect(radio_button_all_users).to_be_visible()
    expect(radio_button_all_users).to_be_checked(checked=False)
    radio_button_all_users.click()
    expect(radio_button_all_users).to_be_checked(checked=True)
    _get_search_button(page).click()
    expect(page).to_have_url(
        f"{BASE_URL}/jobs/search?"
        f"cluster_name=mila"
        f"&aggregated_job_state=COMPLETED,RUNNING,PENDING,FAILED"
        f"&nbr_items_per_page=40"
        f"&sort_by=submit_time"
        f"&sort_asc=-1"
    )
    _check_jobs_table(page, JOBS_SEARCH_DEFAULT_TABLE)


def test_filter_by_user_other_user(page: Page):
    searched_username = "student05@mila.quebec"

    _load_jobs_search_page(page)
    radio_button_other_user = page.locator("input#user_option_other")
    expect(radio_button_other_user).to_be_visible()
    expect(radio_button_other_user).to_be_checked(checked=False)
    radio_button_other_user.click()
    expect(radio_button_other_user).to_be_checked(checked=True)

    input_other_user = page.locator("input#user_option_other_textarea")
    expect(input_other_user).to_be_visible()
    input_other_user.type("student05")

    _get_search_button(page).click()

    expect(page).to_have_url(
        f"{BASE_URL}/jobs/search?"
        f"username={searched_username}"
        f"&cluster_name=mila"
        f"&aggregated_job_state=COMPLETED,RUNNING,PENDING,FAILED"
        f"&nbr_items_per_page=40"
        f"&sort_by=submit_time"
        f"&sort_asc=-1"
    )

    expected_results = [
        job for job in MILA_JOBS if job[1] == searched_username.replace("@", " @")
    ][:40]
    _check_jobs_table(
        page,
        expected_results,
    )

    # Back to all users.
    radio_button_all_users = page.locator("input#user_option_all")
    expect(radio_button_all_users).to_be_visible()
    expect(radio_button_all_users).to_be_checked(checked=False)
    radio_button_all_users.click()
    expect(radio_button_all_users).to_be_checked(checked=True)
    _get_search_button(page).click()
    expect(page).to_have_url(
        f"{BASE_URL}/jobs/search?"
        f"cluster_name=mila"
        f"&aggregated_job_state=COMPLETED,RUNNING,PENDING,FAILED"
        f"&nbr_items_per_page=40"
        f"&sort_by=submit_time"
        f"&sort_asc=-1"
    )
    _check_jobs_table(page, JOBS_SEARCH_DEFAULT_TABLE)


def test_filter_by_cluster_except_one(page: Page):
    # Ignore cluster mila
    _load_jobs_search_page(page)
    check_box_cluster_mila = page.locator("input#cluster_toggle_lever_mila")
    expect(check_box_cluster_mila).to_be_visible()
    expect(check_box_cluster_mila).to_have_attribute("type", "checkbox")
    expect(check_box_cluster_mila).to_be_checked(checked=True)
    check_box_cluster_mila.click()
    expect(check_box_cluster_mila).to_be_checked(checked=False)

    _get_search_button(page).click()
    expect(page).to_have_url(
        f"{BASE_URL}/jobs/search?"
        f"cluster_name="
        f"&aggregated_job_state=COMPLETED,RUNNING,PENDING,FAILED"
        f"&nbr_items_per_page=40&"
        f"sort_by=submit_time"
        f"&sort_asc=-1"
    )
    # When no cluster is selected, table is not filtered.
    _check_jobs_table(page, JOBS_SEARCH_DEFAULT_TABLE)

    # As table is not filtered, cluster mila is already checked.
    check_box_cluster_mila_2 = page.locator("input#cluster_toggle_lever_mila")
    expect(check_box_cluster_mila_2).to_be_visible()
    expect(check_box_cluster_mila_2).to_be_checked(checked=True)


def test_filter_by_cluster_except_two(page: Page):
    # Ignore clusters mila and cedar.
    _load_jobs_search_page(page)
    check_box_cluster_mila = page.locator("input#cluster_toggle_lever_mila")
    check_box_cluster_cedar = page.locator("input#cluster_toggle_lever_cedar")
    expect(check_box_cluster_mila).to_be_visible()
    expect(check_box_cluster_cedar).to_be_visible()
    expect(check_box_cluster_mila).to_have_attribute("type", "checkbox")
    expect(check_box_cluster_cedar).to_have_attribute("type", "checkbox")

    expect(check_box_cluster_mila).to_be_checked(checked=True)
    check_box_cluster_mila.click()
    expect(check_box_cluster_mila).to_be_checked(checked=False)

    # Cluster cedar cannot be filtered.
    expect(check_box_cluster_cedar).to_be_checked(checked=False)
    expect(check_box_cluster_cedar).to_have_attribute("disabled", "disabled")

    _get_search_button(page).click()
    # Table is not filtered.
    expect(page).to_have_url(
        f"{BASE_URL}/jobs/search?"
        f"cluster_name="
        f"&aggregated_job_state=COMPLETED,RUNNING,PENDING,FAILED"
        f"&nbr_items_per_page=40&"
        f"sort_by=submit_time"
        f"&sort_asc=-1"
    )
    _check_jobs_table(page, JOBS_SEARCH_DEFAULT_TABLE)

    check_box_cluster_mila_2 = page.locator("input#cluster_toggle_lever_mila")
    expect(check_box_cluster_mila_2).to_be_visible()
    expect(check_box_cluster_mila_2).to_be_checked(checked=True)


def test_filter_by_status_except_one(page: Page):
    # Ignore status running.
    _load_jobs_search_page(page)
    check_box_status_running = page.locator("input#status_toggle_lever_running")
    expect(check_box_status_running).to_be_visible()
    expect(check_box_status_running).to_have_attribute("type", "checkbox")
    expect(check_box_status_running).to_be_checked(checked=True)
    check_box_status_running.click()
    expect(check_box_status_running).to_be_checked(checked=False)

    _get_search_button(page).click()
    expect(page).to_have_url(
        f"{BASE_URL}/jobs/search?"
        f"cluster_name=mila"
        f"&aggregated_job_state=COMPLETED,PENDING,FAILED"
        f"&nbr_items_per_page=40"
        f"&sort_by=submit_time"
        f"&sort_asc=-1"
    )

    expected_results = [
        [
            job["slurm"]["cluster_name"],
            (
                job["cw"]["mila_email_username"].replace("@", " @")
                if job["cw"]["mila_email_username"] is not None
                else ""
            ),
            job["slurm"]["job_id"],
        ]
        for job in sorted_mila_jobs
        if "RUNNING" != get_inferred_job_state(job["slurm"]["job_state"])
    ][:40]
    _check_jobs_table(
        page,
        expected_results,
    )

    # Back to all statuses.
    check_box_status_running_2 = page.locator("input#status_toggle_lever_running")
    expect(check_box_status_running_2).to_be_visible()
    expect(check_box_status_running_2).to_be_checked(checked=False)
    check_box_status_running_2.click()
    expect(check_box_status_running_2).to_be_checked(checked=True)
    _get_search_button(page).click()
    expect(page).to_have_url(
        f"{BASE_URL}/jobs/search?"
        f"cluster_name=mila"
        f"&aggregated_job_state=COMPLETED,RUNNING,PENDING,FAILED"
        f"&nbr_items_per_page=40"
        f"&sort_by=submit_time"
        f"&sort_asc=-1"
    )
    _check_jobs_table(page, JOBS_SEARCH_DEFAULT_TABLE)


def test_filter_by_status_except_two(page: Page):
    # Ignore statuses running and completed.
    _load_jobs_search_page(page)
    check_box_status_running = page.locator("input#status_toggle_lever_running")
    check_box_status_completed = page.locator("input#status_toggle_lever_completed")
    expect(check_box_status_running).to_be_visible()
    expect(check_box_status_running).to_have_attribute("type", "checkbox")
    expect(check_box_status_completed).to_be_visible()
    expect(check_box_status_completed).to_have_attribute("type", "checkbox")

    expect(check_box_status_running).to_be_checked(checked=True)
    check_box_status_running.click()
    expect(check_box_status_running).to_be_checked(checked=False)

    expect(check_box_status_completed).to_be_checked(checked=True)
    check_box_status_completed.click()
    expect(check_box_status_completed).to_be_checked(checked=False)

    _get_search_button(page).click()
    expect(page).to_have_url(
        f"{BASE_URL}/jobs/search?"
        f"cluster_name=mila"
        f"&aggregated_job_state=PENDING,FAILED"
        f"&nbr_items_per_page=40"
        f"&sort_by=submit_time"
        f"&sort_asc=-1"
    )

    expected_results = [
        [
            job["slurm"]["cluster_name"],
            (
                job["cw"]["mila_email_username"].replace("@", " @")
                if job["cw"]["mila_email_username"] is not None
                else ""
            ),
            job["slurm"]["job_id"],
        ]
        for job in sorted_mila_jobs
        if "PENDING" == get_inferred_job_state(job["slurm"]["job_state"])
        or "FAILED" == get_inferred_job_state(job["slurm"]["job_state"])
    ][:40]
    _check_jobs_table(
        page,
        expected_results,
    )

    # Back to all statuses.
    check_box_status_running_2 = page.locator("input#status_toggle_lever_running")
    check_box_status_completed_2 = page.locator("input#status_toggle_lever_completed")
    expect(check_box_status_running_2).to_be_visible()
    expect(check_box_status_completed_2).to_be_visible()
    expect(check_box_status_running_2).to_be_checked(checked=False)
    check_box_status_running_2.click()
    expect(check_box_status_running_2).to_be_checked(checked=True)

    expect(check_box_status_completed_2).to_be_checked(checked=False)
    check_box_status_completed_2.click()
    expect(check_box_status_completed_2).to_be_checked(checked=True)

    _get_search_button(page).click()
    expect(page).to_have_url(
        f"{BASE_URL}/jobs/search?"
        f"cluster_name=mila"
        f"&aggregated_job_state=COMPLETED,RUNNING,PENDING,FAILED"
        f"&nbr_items_per_page=40"
        f"&sort_by=submit_time"
        f"&sort_asc=-1"
    )
    _check_jobs_table(page, JOBS_SEARCH_DEFAULT_TABLE)


def test_multiple_filters(page: Page):
    # Only current user, and ignore cluster mila and status running.
    _load_jobs_search_page(page)
    radio_button_only_me = page.locator("input#user_option_only_me")
    radio_button_only_me.click()
    expect(radio_button_only_me).to_be_checked(checked=True)

    check_box_cluster_mila = page.locator("input#cluster_toggle_lever_mila")
    check_box_cluster_mila.click()
    expect(check_box_cluster_mila).to_be_checked(checked=False)

    check_box_status_running = page.locator("input#status_toggle_lever_running")
    check_box_status_running.click()
    expect(check_box_status_running).to_be_checked(checked=False)

    _get_search_button(page).click()

    expect(page).to_have_url(
        f"{BASE_URL}/jobs/search?"
        f"username=student06@mila.quebec"
        f"&cluster_name="
        f"&aggregated_job_state=COMPLETED,PENDING,FAILED"
        f"&nbr_items_per_page=40"
        f"&sort_by=submit_time"
        f"&sort_asc=-1"
    )

    expected_results = [
        [
            job["slurm"]["cluster_name"],
            (
                job["cw"]["mila_email_username"].replace("@", " @")
                if job["cw"]["mila_email_username"] is not None
                else ""
            ),
            job["slurm"]["job_id"],
        ]
        for job in sorted_jobs
        if job["cw"]["mila_email_username"] == "student06@mila.quebec"
        and get_inferred_job_state(job["slurm"]["job_state"])
        in ["COMPLETED", "PENDING", "FAILED"]
    ][:40]
    _check_jobs_table(
        page,
        expected_results,
    )

    # Reset all filters.

    radio_button_all_users = page.locator("input#user_option_all")
    radio_button_all_users.click()
    expect(radio_button_all_users).to_be_checked(checked=True)

    check_box_cluster_mila_2 = page.locator("input#cluster_toggle_lever_mila")
    expect(check_box_cluster_mila_2).to_be_checked(checked=True)

    check_box_status_running_2 = page.locator("input#status_toggle_lever_running")
    check_box_status_running_2.click()
    expect(check_box_status_running_2).to_be_checked(checked=True)

    _get_search_button(page).click()
    expect(page).to_have_url(
        f"{BASE_URL}/jobs/search?"
        f"cluster_name=mila"
        f"&aggregated_job_state=COMPLETED,RUNNING,PENDING,FAILED"
        f"&nbr_items_per_page=40"
        f"&sort_by=submit_time"
        f"&sort_asc=-1"
    )
    _check_jobs_table(page, JOBS_SEARCH_DEFAULT_TABLE)


def test_jobs_table_sorting_by_cluster(page: Page):
    _load_jobs_search_page(page)

    expected_results = [job for job in sorted(MILA_JOBS, key=lambda j: (j[0], j[2]))][
        :40
    ]
    _check_jobs_table_sorting(page, 0, "Cluster", "cluster_name", expected_results)


def test_jobs_table_sorting_by_job_id(page: Page):
    _load_jobs_search_page(page)
    expected_results = [
        job for job in sorted(MILA_JOBS, key=lambda j: (j[0], j[2]), reverse=True)
    ][:40]
    _check_jobs_table_sorting(
        page, 2, "Job ID", "job_id", expected_results, reverse=True
    )


def test_jobs_table_sorting_by_job_id_ascending(page: Page):
    _load_jobs_search_page(page)
    expected_results = [job for job in sorted(MILA_JOBS, key=lambda j: (j[0], j[2]))][
        :40
    ]
    _check_jobs_table_sorting(
        page, 2, "Job ID", "job_id", expected_results, double_click=True, reverse=False
    )


def test_jobs_table_sorting_by_end_time(page: Page):
    _load_jobs_search_page(page)
    expected_results = [
        [
            job["slurm"]["cluster_name"],
            (
                job["cw"]["mila_email_username"].replace("@", " @")
                if job["cw"]["mila_email_username"] is not None
                else ""
            ),
            job["slurm"]["job_id"],
        ]
        for job in sorted(
            sorted_mila_jobs,
            key=lambda j: (
                0 if j["slurm"]["end_time"] is None else -j["slurm"]["end_time"],
                j["slurm"]["job_id"],
            ),
        )
    ][:40]

    _check_jobs_table_sorting(
        page, 8, "End time", "end_time", expected_results, reverse=True
    )


def _check_jobs_table_sorting(
    page: Page,
    column_id: int,
    column_text: str,
    column_name: str,
    expected: list,
    *,
    double_click: bool = False,
    reverse: bool = False,
):
    """Click on relevant header to sort jobs table according to given parameters, then check sorting."""
    if double_click:
        seq_reverse = [not reverse, reverse]
    else:
        seq_reverse = [reverse]
    for reverse_value in seq_reverse:
        headers = page.locator("table#search_table thead tr th")
        header = headers.nth(column_id).locator("a")
        expect(header).to_contain_text(column_text)
        header.click()
        # page.wait_for_url(f"{BASE_URL}/jobs/search?sort_by={column_name}&sort_asc={-1 if reverse_value else 1}")
        expect(page).to_have_url(
            f"{BASE_URL}/jobs/search?sort_by={column_name}&sort_asc={-1 if reverse_value else 1}"
        )
    # _print_table(page, column_id, 3)
    _check_jobs_table(page, expected)


def _print_table(page: Page, column_id: int, nb_columns=None):
    """Print jobs table.

    NB: Currently unused, for debugging only.
    """
    rows = page.locator("table#search_table tbody tr")
    expect(rows).to_have_count(18)
    content = []
    nb_columns = max(3, column_id + 1) if nb_columns is None else nb_columns
    for i in range(18):
        row = rows.nth(i)
        cols = row.locator("td")
        assert cols.count() >= nb_columns
        row_content = []
        for j in range(nb_columns):
            row_content.append(cols.nth(j).text_content().strip(" \r\n\t"))
        content.append(row_content)
    print(content)
