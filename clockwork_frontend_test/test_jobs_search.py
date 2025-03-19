import pytest
from playwright.sync_api import Page, expect
from random import choice

from clockwork_frontend_test.utils import BASE_URL, get_fake_data
from clockwork_web.core.jobs_helper import get_inferred_job_state

# Retrieve data we are interested in from the fake data
fake_data = get_fake_data()

# Retrieve an admin from the fake_data
ADMIN_USERNAME = ""
NON_ADMIN_USERNAME = ""
for user in fake_data["users"]:
    if "admin_access" in user and user["admin_access"]:
        ADMIN_USERNAME = user["mila_email_username"]

    else:
        NON_ADMIN_USERNAME = user["mila_email_username"]

    if ADMIN_USERNAME != "" and NON_ADMIN_USERNAME != "":
        break

# Sorts the jobs by submit time
sorted_jobs = sorted(
    fake_data["jobs"], key=lambda j: (-j["slurm"]["submit_time"], j["slurm"]["job_id"])
)

# Expected jobs table content for first columns (cluster, user (@mila.quebec), job ID).
JOBS_SEARCH_DEFAULT_TABLE = []
for i in range(0, 40):
    job = sorted_jobs[i]
    JOBS_SEARCH_DEFAULT_TABLE.append(
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

ALL_JOBS = [
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
]


def _get_user_jobs_search_default_table(username):
    """
    Retrieve the 40 last submitted jobs of a specific user.

    Parameters:
        username:   The mail of the user, used as an ID

    Return:
        A list containing the 40 last submitted jobs of a specific user
    """

    return [
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
        if job["cw"]["mila_email_username"] == username
    ][:40]


def _load_jobs_search_page(page: Page, username: str):
    """Login and go to jobs search page."""
    # Login
    page.goto(f"{BASE_URL}/login/testing?user_id={username}")
    
    # Go to jobs/search page
    page.goto(f"{BASE_URL}/jobs/search")


def _load_all_jobs_search_page(page: Page, username: str):
    """Login and go to jobs search page."""
    # Login
    page.goto(f"{BASE_URL}/login/testing?user_id={username}")
    # Go to jobs/search page
    page.goto(f"{BASE_URL}/jobs/search?nbr_items_per_page={len(sorted_jobs)}")


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


@pytest.mark.parametrize(
    "username,expected_results",
    (
        (
            "student00@mila.quebec",
            _get_user_jobs_search_default_table("student00@mila.quebec"),
        ),  # A non-admin user can only see his/her own jobs
        (ADMIN_USERNAME, JOBS_SEARCH_DEFAULT_TABLE),  # An admin can see all the jobs
    ),
)
def test_jobs_search_default(page: Page, username, expected_results):
    """Test default table content in jobs/search page."""
    _load_jobs_search_page(page, username=username)
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
    _check_jobs_table(page, expected_results)


@pytest.mark.parametrize(
    "username,expected_restricted_results, expected_all_results",
    (
        (
            "student00@mila.quebec",
            _get_user_jobs_search_default_table("student00@mila.quebec"),
            _get_user_jobs_search_default_table("student00@mila.quebec"),
        ),  # A non-admin user can only see his/her own jobs, so it is normally irrelevant, but just in case...
        (
            ADMIN_USERNAME,
            _get_user_jobs_search_default_table(ADMIN_USERNAME),
            JOBS_SEARCH_DEFAULT_TABLE,
        ),  # An admin can see all the jobs, so this is the test we are looking for here
    ),
)
def test_filter_by_user_only_me(
    page: Page, username, expected_restricted_results, expected_all_results
):
    _load_jobs_search_page(page, username=username)
    radio_button_only_me = page.locator("input#user_option_only_me")
    expect(radio_button_only_me).to_be_visible()
    expect(radio_button_only_me).to_be_checked(checked=False)
    radio_button_only_me.click()
    expect(radio_button_only_me).to_be_checked(checked=True)
    _get_search_button(page).click()
    expect(page).to_have_url(
        f"{BASE_URL}/jobs/search?"
        f"username={username}"
        f"&cluster_name=mila,narval,cedar,beluga,graham"
        f"&aggregated_job_state=COMPLETED,RUNNING,PENDING,FAILED"
        f"&nbr_items_per_page=40"
        f"&sort_by=submit_time"
        f"&sort_asc=-1"
    )

    _check_jobs_table(
        page,
        expected_restricted_results,
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
        f"cluster_name=mila,narval,cedar,beluga,graham"
        f"&aggregated_job_state=COMPLETED,RUNNING,PENDING,FAILED"
        f"&nbr_items_per_page=40"
        f"&sort_by=submit_time"
        f"&sort_asc=-1"
    )
    _check_jobs_table(page, expected_all_results)


@pytest.mark.parametrize(
    "username, searched_username, expected_restricted_results, expected_all_results",
    (
        (
            "student00@mila.quebec",
            "student05@mila.quebec",
            [],
            _get_user_jobs_search_default_table("student00@mila.quebec"),
        ),  # A non-admin user can only see his/her own jobs, so it is normally irrelevant, but just in case...
        (
            ADMIN_USERNAME,
            "student00@mila.quebec",
            _get_user_jobs_search_default_table("student00@mila.quebec"),
            JOBS_SEARCH_DEFAULT_TABLE,
        ),  # An admin can see all the jobs, so this is the test we are looking for here
    ),
)
def test_filter_by_user_other_user(
    page: Page,
    username,
    searched_username,
    expected_restricted_results,
    expected_all_results,
):

    _load_jobs_search_page(page, username=username)
    radio_button_other_user = page.locator("input#user_option_other")
    expect(radio_button_other_user).to_be_visible()
    expect(radio_button_other_user).to_be_checked(checked=False)
    radio_button_other_user.click()
    expect(radio_button_other_user).to_be_checked(checked=True)

    input_other_user = page.locator("input#user_option_other_textarea")
    expect(input_other_user).to_be_visible()
    input_other_user.type(searched_username.split("@")[0])

    _get_search_button(page).click()

    expect(page).to_have_url(
        f"{BASE_URL}/jobs/search?"
        f"username={searched_username}"
        f"&cluster_name=mila,narval,cedar,beluga,graham"
        f"&aggregated_job_state=COMPLETED,RUNNING,PENDING,FAILED"
        f"&nbr_items_per_page=40"
        f"&sort_by=submit_time"
        f"&sort_asc=-1"
    )

    _check_jobs_table(
        page,
        expected_restricted_results,
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
        f"cluster_name=mila,narval,cedar,beluga,graham"
        f"&aggregated_job_state=COMPLETED,RUNNING,PENDING,FAILED"
        f"&nbr_items_per_page=40"
        f"&sort_by=submit_time"
        f"&sort_asc=-1"
    )
    _check_jobs_table(page, expected_all_results)


@pytest.mark.parametrize(
    "username, all_clusters_jobs",
    (
        (
            "student00@mila.quebec",
            _get_user_jobs_search_default_table("student00@mila.quebec"),
        ),  # A non-admin user can only see his/her own jobs, so it is normally irrelevant, but just in case...
        (
            ADMIN_USERNAME,
            JOBS_SEARCH_DEFAULT_TABLE,
        ),  # An admin can see all the jobs, so this is the test we are looking for here
    ),
)
def test_filter_by_cluster_except_one(page: Page, username, all_clusters_jobs):
    # Ignore cluster mila
    _load_jobs_search_page(page, username=username)
    check_box_cluster_mila = page.locator("input#cluster_toggle_lever_mila")
    expect(check_box_cluster_mila).to_be_visible()
    expect(check_box_cluster_mila).to_have_attribute("type", "checkbox")
    expect(check_box_cluster_mila).to_be_checked(checked=True)
    check_box_cluster_mila.click()
    expect(check_box_cluster_mila).to_be_checked(checked=False)

    _get_search_button(page).click()
    expect(page).to_have_url(
        f"{BASE_URL}/jobs/search?"
        f"cluster_name=narval,cedar,beluga,graham"
        f"&aggregated_job_state=COMPLETED,RUNNING,PENDING,FAILED"
        f"&nbr_items_per_page=40&"
        f"sort_by=submit_time"
        f"&sort_asc=-1"
    )

    expected_results = [job for job in all_clusters_jobs if job[0] != "mila"][:40]
    # Just check that first column (cluster) does not contain "mila".
    _check_jobs_table(
        page,
        expected_results,
    )

    # Back to all clusters.
    check_box_cluster_mila_2 = page.locator("input#cluster_toggle_lever_mila")
    expect(check_box_cluster_mila_2).to_be_visible()
    expect(check_box_cluster_mila_2).to_be_checked(checked=False)
    check_box_cluster_mila_2.click()
    expect(check_box_cluster_mila_2).to_be_checked(checked=True)
    _get_search_button(page).click()
    expect(page).to_have_url(
        f"{BASE_URL}/jobs/search?"
        f"cluster_name=mila,narval,cedar,beluga,graham"
        f"&aggregated_job_state=COMPLETED,RUNNING,PENDING,FAILED"
        f"&nbr_items_per_page=40"
        f"&sort_by=submit_time"
        f"&sort_asc=-1"
    )
    _check_jobs_table(page, all_clusters_jobs)


@pytest.mark.parametrize(
    "username, all_clusters_jobs",
    (
        (
            "student00@mila.quebec",
            _get_user_jobs_search_default_table("student00@mila.quebec"),
        ),  # A non-admin user can only see his/her own jobs, so it is normally irrelevant, but just in case...
        (
            ADMIN_USERNAME,
            JOBS_SEARCH_DEFAULT_TABLE,
        ),  # An admin can see all the jobs, so this is the test we are looking for here
    ),
)
def test_filter_by_cluster_except_two(page: Page, username, all_clusters_jobs):
    # Ignore clusters mila and cedar.
    _load_jobs_search_page(page, username=username)
    check_box_cluster_mila = page.locator("input#cluster_toggle_lever_mila")
    check_box_cluster_cedar = page.locator("input#cluster_toggle_lever_cedar")
    expect(check_box_cluster_mila).to_be_visible()
    expect(check_box_cluster_cedar).to_be_visible()
    expect(check_box_cluster_mila).to_have_attribute("type", "checkbox")
    expect(check_box_cluster_cedar).to_have_attribute("type", "checkbox")

    expect(check_box_cluster_mila).to_be_checked(checked=True)
    check_box_cluster_mila.click()
    expect(check_box_cluster_mila).to_be_checked(checked=False)

    expect(check_box_cluster_cedar).to_be_checked(checked=True)
    check_box_cluster_cedar.click()
    expect(check_box_cluster_cedar).to_be_checked(checked=False)

    _get_search_button(page).click()
    expect(page).to_have_url(
        f"{BASE_URL}/jobs/search?"
        f"cluster_name=narval,beluga,graham"
        f"&aggregated_job_state=COMPLETED,RUNNING,PENDING,FAILED"
        f"&nbr_items_per_page=40&"
        f"sort_by=submit_time"
        f"&sort_asc=-1"
    )
    # Just check first column (cluster) does not contain neither "mila" nor "cedar".
    expected_results = [
        job for job in all_clusters_jobs if job[0] != "mila" and job[0] != "cedar"
    ][:40]

    _check_jobs_table(
        page,
        expected_results,
    )

    # Back to all clusters.
    check_box_cluster_mila_2 = page.locator("input#cluster_toggle_lever_mila")
    check_box_cluster_cedar_2 = page.locator("input#cluster_toggle_lever_cedar")
    expect(check_box_cluster_mila_2).to_be_visible()
    expect(check_box_cluster_cedar_2).to_be_visible()
    expect(check_box_cluster_mila_2).to_be_checked(checked=False)
    check_box_cluster_mila_2.click()
    expect(check_box_cluster_mila_2).to_be_checked(checked=True)
    expect(check_box_cluster_cedar_2).to_be_checked(checked=False)
    check_box_cluster_cedar_2.click()
    expect(check_box_cluster_cedar_2).to_be_checked(checked=True)

    _get_search_button(page).click()
    expect(page).to_have_url(
        f"{BASE_URL}/jobs/search?"
        f"cluster_name=mila,narval,cedar,beluga,graham"
        f"&aggregated_job_state=COMPLETED,RUNNING,PENDING,FAILED"
        f"&nbr_items_per_page=40"
        f"&sort_by=submit_time"
        f"&sort_asc=-1"
    )
    _check_jobs_table(page, all_clusters_jobs)


@pytest.mark.parametrize(
    "username, restrict_jobs, all_status_jobs",
    (
        (
            "student00@mila.quebec",
            True,
            _get_user_jobs_search_default_table("student00@mila.quebec"),
        ),  # A non-admin user can only see his/her own jobs, so it is normally irrelevant, but just in case...
        (
            ADMIN_USERNAME,
            False,
            JOBS_SEARCH_DEFAULT_TABLE,
        ),  # An admin can see all the jobs, so this is the test we are looking for here
    ),
)
def test_filter_by_status_except_one(
    page: Page, username, restrict_jobs, all_status_jobs
):
    # Ignore status running.
    _load_jobs_search_page(page, username=username)
    check_box_status_running = page.locator("input#status_toggle_lever_running")
    expect(check_box_status_running).to_be_visible()
    expect(check_box_status_running).to_have_attribute("type", "checkbox")
    expect(check_box_status_running).to_be_checked(checked=True)
    check_box_status_running.click()
    expect(check_box_status_running).to_be_checked(checked=False)

    _get_search_button(page).click()
    expect(page).to_have_url(
        f"{BASE_URL}/jobs/search?"
        f"cluster_name=mila,narval,cedar,beluga,graham"
        f"&aggregated_job_state=COMPLETED,PENDING,FAILED"
        f"&nbr_items_per_page=40"
        f"&sort_by=submit_time"
        f"&sort_asc=-1"
    )

    if restrict_jobs:
        restriction_condition = lambda job: job["cw"]["mila_email_username"] == username
    else:
        restriction_condition = True

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
        if (get_inferred_job_state(job["slurm"]["job_state"]) != "RUNNING")
        and restriction_condition(job)
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
        f"cluster_name=mila,narval,cedar,beluga,graham"
        f"&aggregated_job_state=COMPLETED,RUNNING,PENDING,FAILED"
        f"&nbr_items_per_page=40"
        f"&sort_by=submit_time"
        f"&sort_asc=-1"
    )
    _check_jobs_table(page, all_status_jobs)


@pytest.mark.parametrize(
    "username, restrict_jobs, all_status_jobs",
    (
        (
            "student00@mila.quebec",
            True,
            _get_user_jobs_search_default_table("student00@mila.quebec"),
        ),  # A non-admin user can only see his/her own jobs, so it is normally irrelevant, but just in case...
        (
            ADMIN_USERNAME,
            False,
            JOBS_SEARCH_DEFAULT_TABLE,
        ),  # An admin can see all the jobs, so this is the test we are looking for here
    ),
)
def test_filter_by_status_except_two(
    page: Page, username, restrict_jobs, all_status_jobs
):
    # Ignore statuses running and completed.
    _load_jobs_search_page(page, username=username)
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
        f"cluster_name=mila,narval,cedar,beluga,graham"
        f"&aggregated_job_state=PENDING,FAILED"
        f"&nbr_items_per_page=40"
        f"&sort_by=submit_time"
        f"&sort_asc=-1"
    )

    if restrict_jobs:
        restriction_condition = lambda job: job["cw"]["mila_email_username"] == username
    else:
        restriction_condition = True

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
        if get_inferred_job_state(job["slurm"]["job_state"]) != "RUNNING"
        and get_inferred_job_state(job["slurm"]["job_state"]) != "COMPLETED"
        and restriction_condition(job)
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
        f"cluster_name=mila,narval,cedar,beluga,graham"
        f"&aggregated_job_state=COMPLETED,RUNNING,PENDING,FAILED"
        f"&nbr_items_per_page=40"
        f"&sort_by=submit_time"
        f"&sort_asc=-1"
    )
    _check_jobs_table(page, all_status_jobs)


@pytest.mark.parametrize(
    "username, restrict_jobs, all_base_jobs",
    (
        (
            "student00@mila.quebec",
            True,
            _get_user_jobs_search_default_table("student00@mila.quebec"),
        ),  # A non-admin user can only see his/her own jobs, so it is normally irrelevant, but just in case...
        (
            ADMIN_USERNAME,
            False,
            JOBS_SEARCH_DEFAULT_TABLE,
        ),  # An admin can see all the jobs, so this is the test we are looking for here
    ),
)
def test_multiple_filters(page: Page, username, restrict_jobs, all_base_jobs):
    # Only current user, and ignore cluster mila and status pending.
    _load_jobs_search_page(page, username=username)
    radio_button_only_me = page.locator("input#user_option_only_me")
    radio_button_only_me.click()
    expect(radio_button_only_me).to_be_checked(checked=True)

    check_box_cluster_mila = page.locator("input#cluster_toggle_lever_mila")
    check_box_cluster_mila.click()
    expect(check_box_cluster_mila).to_be_checked(checked=False)

    check_box_status_pending = page.locator("input#status_toggle_lever_pending")
    check_box_status_pending.click()
    expect(check_box_status_pending).to_be_checked(checked=False)

    _get_search_button(page).click()

    expect(page).to_have_url(
        f"{BASE_URL}/jobs/search?"
        f"username={username}"
        f"&cluster_name=narval,cedar,beluga,graham"
        f"&aggregated_job_state=COMPLETED,RUNNING,FAILED"
        f"&nbr_items_per_page=40"
        f"&sort_by=submit_time"
        f"&sort_asc=-1"
    )

    if restrict_jobs:
        restriction_condition = lambda job: job["cw"]["mila_email_username"] == username
    else:
        restriction_condition = True

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
        if job["cw"]["mila_email_username"] == username
        and job["slurm"]["cluster_name"] != "mila"
        and get_inferred_job_state(job["slurm"]["job_state"]) != "PENDING"
        and restriction_condition(job)
    ][:40]

    _check_jobs_table(page, expected_results)

    # Reset all filters.

    radio_button_all_users = page.locator("input#user_option_all")
    radio_button_all_users.click()
    expect(radio_button_all_users).to_be_checked(checked=True)

    check_box_cluster_mila_2 = page.locator("input#cluster_toggle_lever_mila")
    check_box_cluster_mila_2.click()
    expect(check_box_cluster_mila_2).to_be_checked(checked=True)

    check_box_status_pending_2 = page.locator("input#status_toggle_lever_pending")
    check_box_status_pending_2.click()
    expect(check_box_status_pending_2).to_be_checked(checked=True)

    _get_search_button(page).click()
    expect(page).to_have_url(
        f"{BASE_URL}/jobs/search?"
        f"cluster_name=mila,narval,cedar,beluga,graham"
        f"&aggregated_job_state=COMPLETED,RUNNING,PENDING,FAILED"
        f"&nbr_items_per_page=40"
        f"&sort_by=submit_time"
        f"&sort_asc=-1"
    )
    _check_jobs_table(page, all_base_jobs)


@pytest.mark.parametrize(
    "username, restrict_jobs, all_base_jobs",
    ((ADMIN_USERNAME, False, ALL_JOBS),),
)
def test_filter_by_job_array(page: Page, username, restrict_jobs, all_base_jobs):
    # Define what we expect
    for searched_job in sorted_jobs:

        if searched_job["slurm"]["array_job_id"] != "0" and searched_job["slurm"][
            "job_id"
        ] in [job[2] for job in all_base_jobs]:
            break
    searched_array_job_id = searched_job["slurm"]["array_job_id"]

    if restrict_jobs:
        restriction_condition = lambda job: job["cw"]["mila_email_username"] == username
    else:
        restriction_condition = True

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
        if job["slurm"]["array_job_id"] == searched_array_job_id
        and restriction_condition
    ][:40]

    # Go on the jobs search page and click on the job array
    # (We display all jobs in order to be sure to have our searched job on the page)
    _load_all_jobs_search_page(page, username=username)
    job_id = page.get_by_text(searched_job["slurm"]["job_id"])
    expect(job_id).to_have_count(1)
    parent_row = page.locator("table#search_table tbody tr").filter(has=job_id)
    expect(parent_row).to_have_count(1)
    cols = parent_row.locator("td")
    icon_job_array = cols.nth(3).locator("a")
    expect(icon_job_array).to_have_count(1)
    icon_job_array.click()

    # (In this check, the number of items per page is added because we used "_load_all_jobs_search_page",
    # thus this number is maintained in the URL while clicking)
    expect(page).to_have_url(
        f"{BASE_URL}/jobs/search?nbr_items_per_page={len(all_base_jobs)}&job_array={searched_array_job_id}&page_num=1"
    )

    _check_jobs_table(page, expected_results)

    filter_reset = page.get_by_title("Reset filter by job array")
    expect(filter_reset).to_contain_text(f"Job array {searched_array_job_id}")
    filter_reset.click()

    expect(page).to_have_url(
        f"{BASE_URL}/jobs/search?nbr_items_per_page={len(all_base_jobs)}&job_array=None&page_num=1"
    )
    _check_jobs_table(page, all_base_jobs)


def test_filter_by_job_user_props(page: Page):
    current_user = fake_data["jobs"][0]["cw"]["mila_email_username"]
    all_base_jobs = _get_user_jobs_search_default_table(current_user)
    restrict_jobs = True

    prop_name = "name"
    prop_content = "je suis une user prop 1"
    related_jobs_ids = [
        prop["job_id"]
        for prop in fake_data["job_user_props"]
        if prop_name in prop["props"].keys()
        and prop["props"][prop_name] == prop_content
    ]

    if restrict_jobs:
        restriction_condition = lambda job: job["cw"]["mila_email_username"] == username
    else:
        restriction_condition = True

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
        if job["slurm"]["job_id"] in related_jobs_ids and restriction_condition
    ][:40]

    # Login
    page.goto(f"{BASE_URL}/login/testing?user_id={current_user}")
    # Go to settings in order to allow the props display (hidden by default)
    page.goto(f"{BASE_URL}/settings/")
    radio_job_user_props = page.locator("input#jobs_list_job_user_props_toggle")
    expect(radio_job_user_props).to_be_checked(checked=False)
    # Check column job_user_props.
    radio_job_user_props.click()
    expect(radio_job_user_props).to_be_checked(checked=True)

    # Back to jobs/search.
    page.goto(
        f"{BASE_URL}/jobs/search?" f"&nbr_items_per_page={len(sorted_jobs)}"
    )  # We display all the jobs on the page

    # Get one job of the array and click on its user prop link
    # We retrieve one job from the jobs presenting the prop
    job_id = page.get_by_text(choice(related_jobs_ids))
    expect(job_id).to_have_count(1)
    parent_row = page.locator("table#search_table tbody tr").filter(has=job_id)
    expect(parent_row).to_have_count(1)
    cols = parent_row.locator("td")
    link_job_user_prop = cols.nth(4).locator("a")
    expect(link_job_user_prop).to_have_count(1)
    expect(link_job_user_prop).to_contain_text(f"{prop_name} {prop_content}")
    link_job_user_prop.click()

    expect(page).to_have_url(
        f"{BASE_URL}/jobs/search?"
        f"nbr_items_per_page={len(sorted_jobs)}"  # Because we displayed all the jobs previously, so that this parameter stays in the URL
        f"&user_prop_name={prop_name}"
        f"&user_prop_content={prop_content.replace(' ', '+')}"
        f"&page_num=1"
    )

    _check_jobs_table(
        page,
        expected_results,
    )

    filter_reset = page.get_by_title("Reset filter by job user prop")
    expect(filter_reset).to_contain_text('User prop name: "je suis une user prop 1"')
    filter_reset.click()

    expect(page).to_have_url(
        f"{BASE_URL}/jobs/search?nbr_items_per_page={len(sorted_jobs)}&user_prop_name=&user_prop_content=&page_num=1"
    )
    _check_jobs_table(page, all_base_jobs)

    # Back to default settings.
    page.goto(f"{BASE_URL}/settings/")
    radio_job_user_props = page.locator("input#jobs_list_job_user_props_toggle")
    expect(radio_job_user_props).to_be_checked(checked=True)
    radio_job_user_props.click()
    expect(radio_job_user_props).to_be_checked(checked=False)


@pytest.mark.parametrize(
    "prop_name,title",
    (("comet_hyperlink", "Comet link"), ("wandb_hyperlink", "WANDB link")),
)
def test_special_user_props(page: Page, prop_name: str, title: str):
    current_user = "student02@mila.quebec"
    related_jobs_ids = [
        prop["job_id"]
        for prop in fake_data["job_user_props"]
        if prop_name in prop["props"].keys()
    ]
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
        if job["slurm"]["job_id"] in related_jobs_ids
        and job["cw"]["mila_email_username"] == current_user
    ][:40]
    assert expected_results

    # Login
    page.goto(f"{BASE_URL}/login/testing?user_id={current_user}")
    # Go to settings in order to allow the props display (hidden by default)
    page.goto(f"{BASE_URL}/settings/")
    radio_job_user_props = page.locator("input#jobs_list_job_user_props_toggle")
    expect(radio_job_user_props).to_be_checked(checked=False)
    # Check column job_user_props.
    radio_job_user_props.click()
    expect(radio_job_user_props).to_be_checked(checked=True)

    # Back to jobs/search.
    page.goto(
        f"{BASE_URL}/jobs/search?" f"&nbr_items_per_page={len(sorted_jobs)}"
    )  # We display all the jobs on the page

    job_id = page.get_by_text(choice(related_jobs_ids))
    expect(job_id).to_have_count(1)
    parent_row = page.locator("table#search_table tbody tr").filter(has=job_id)
    expect(parent_row).to_have_count(1)
    cols = parent_row.locator("td")
    expect(cols).to_have_count(11)
    # For this job, user props col should be empty
    assert not cols.nth(4).text_content().strip()
    # Check links col
    link = cols.nth(10).locator(f"a.{prop_name}")
    expect(link).to_have_count(1)
    assert link.get_attribute("href").startswith("https://")
    assert link.get_attribute("target") == "_blank"

    # Back to default settings.
    page.goto(f"{BASE_URL}/settings/")
    radio_job_user_props = page.locator("input#jobs_list_job_user_props_toggle")
    expect(radio_job_user_props).to_be_checked(checked=True)
    radio_job_user_props.click()
    expect(radio_job_user_props).to_be_checked(checked=False)


def test_jobs_table_sorting_by_cluster(page: Page):
    _load_jobs_search_page(page, username=ADMIN_USERNAME)
    expected_content = [
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
            fake_data["jobs"],
            key=lambda j: (j["slurm"]["cluster_name"], j["slurm"]["job_id"]),
        )
    ][:40]
    _check_jobs_table_sorting(page, 0, "Cluster", "cluster_name", expected_content)


def test_jobs_table_sorting_by_job_id(page: Page):
    expected_content = [
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
            fake_data["jobs"], key=lambda j: j["slurm"]["job_id"], reverse=True
        )
    ][:40]
    _load_jobs_search_page(page, username=ADMIN_USERNAME)
    _check_jobs_table_sorting(
        page, 2, "Job ID", "job_id", expected_content, reverse=True
    )


def test_jobs_table_sorting_by_job_id_ascending(page: Page):
    _load_jobs_search_page(page, username=ADMIN_USERNAME)
    expected_content = [
        [
            job["slurm"]["cluster_name"],
            (
                job["cw"]["mila_email_username"].replace("@", " @")
                if job["cw"]["mila_email_username"] is not None
                else ""
            ),
            job["slurm"]["job_id"],
        ]
        for job in sorted(fake_data["jobs"], key=lambda j: j["slurm"]["job_id"])
    ][:40]
    _check_jobs_table_sorting(
        page, 2, "Job ID", "job_id", expected_content, double_click=True, reverse=False
    )


def test_jobs_table_sorting_by_end_time(page: Page):
    _load_jobs_search_page(page, username=ADMIN_USERNAME)
    expected_content = [
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
            fake_data["jobs"],
            key=lambda j: (
                0 if j["slurm"]["end_time"] is None else -j["slurm"]["end_time"],
                j["slurm"]["job_id"],
            ),
        )
    ][:40]

    _check_jobs_table_sorting(
        page, 8, "End time", "end_time", expected_content[:40], reverse=True
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
        expect(page).to_have_url(
            f"{BASE_URL}/jobs/search?sort_by={column_name}&sort_asc={-1 if reverse_value else 1}"
        )
    _check_jobs_table(page, expected)


def _print_table(page: Page, column_id: int, nb_columns=None):
    """Print jobs table.

    NB: Currently unused, for debugging only.
    """
    rows = page.locator("table#search_table tbody tr")
    expect(rows).to_have_count(40)
    content = []
    nb_columns = max(3, column_id + 1) if nb_columns is None else nb_columns
    for i in range(40):
        row = rows.nth(i)
        cols = row.locator("td")
        assert cols.count() >= nb_columns
        row_content = []
        for j in range(nb_columns):
            row_content.append(cols.nth(j).text_content().strip(" \r\n\t"))
        content.append(row_content)