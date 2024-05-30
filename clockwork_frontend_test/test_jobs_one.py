import random
from playwright.sync_api import Page, expect

from clockwork_frontend_test.utils import BASE_URL


def _get_job_with_user_props(fake_data, mila_email_username):
    """Get a job from fake data that does have user props for given mila email username."""
    LD_candidates = [
        D_job_user_props_entry
        for D_job_user_props_entry in fake_data["job_user_props"]
        if (
            D_job_user_props_entry["mila_email_username"] == mila_email_username
            and len(D_job_user_props_entry["props"]) > 0
        )
    ]
    assert (
        len(LD_candidates) > 0
    ), f"There should be at least one job_user_props entry for user {mila_email_username}."
    D_job_user_props_entry = random.choice(LD_candidates)

    job_id = D_job_user_props_entry["job_id"]
    cluster_name = D_job_user_props_entry["cluster_name"]
    original_props = D_job_user_props_entry["props"]
    return job_id, cluster_name, original_props


def _get_job_without_user_props(fake_data, mila_email_username):
    """Get a job from fake data that does not have any user prop for given mila email username."""
    # Collect keys (job_id, cluster_name) for all jobs in fake data which do have user props.
    jobs_with_user_props = {
        (D_job_user_props_entry["job_id"], D_job_user_props_entry["cluster_name"])
        for D_job_user_props_entry in fake_data["job_user_props"]
        if (
            D_job_user_props_entry["mila_email_username"] == mila_email_username
            and len(D_job_user_props_entry["props"]) > 0
        )
    }
    assert jobs_with_user_props
    # Take the first job in fake data which is not present in jobs collected above.
    for job in fake_data["jobs"]:
        if (
            job["slurm"]["job_id"],
            job["slurm"]["cluster_name"],
        ) not in jobs_with_user_props:
            return job
    else:
        raise AssertionError(
            f"We should have at least one job without user props for user {mila_email_username}"
        )


def test_job_no_user_props(page: Page, fake_data):
    mila_email_username = "student01@mila.quebec"
    # Login
    page.goto(f"{BASE_URL}/login/testing?user_id={mila_email_username}")
    # Go to settings to set language to english.
    page.goto(f"{BASE_URL}/settings/")
    # Get language select.
    select = page.locator("select#language_selection")
    # Switch to english.
    select.select_option("en")
    # Check english is selected.
    expect(select).to_have_value("en")

    job = _get_job_without_user_props(fake_data, mila_email_username)
    job_id = job["slurm"]["job_id"]
    # Go to job page
    page.goto(f"{BASE_URL}/jobs/one?job_id={job_id}")
    # Check we are on job page
    expect(page.get_by_text(f"Single job {job_id}")).to_be_visible()
    # Check user props section is well displayed
    expect(page.get_by_text(f"Your props for job {job_id}")).to_be_visible()
    # Check user props section does not contain any prop
    expect(
        page.get_by_text("You have not defined any user prop for this job.")
    ).to_be_visible()
    props_table = page.locator("table#user_props_table")
    expect(props_table).to_have_count(0)


def test_job_with_user_props(page: Page, fake_data):
    mila_email_username = "student01@mila.quebec"
    # Login
    page.goto(f"{BASE_URL}/login/testing?user_id={mila_email_username}")
    # Go to settings to set language to english.
    page.goto(f"{BASE_URL}/settings/")
    # Get language select.
    select = page.locator("select#language_selection")
    # Switch to english.
    select.select_option("en")
    # Check english is selected.
    expect(select).to_have_value("en")

    job_id, _, user_props = _get_job_with_user_props(
        fake_data, mila_email_username
    )
    assert user_props

    # Go to job page
    page.goto(f"{BASE_URL}/jobs/one?job_id={job_id}")
    # Check we are on job page
    expect(page.get_by_text(f"Single job {job_id}")).to_be_visible()
    expect(page.get_by_text(f"Your props for job {job_id}")).to_be_visible()
    # Check we do have user props displayed
    expect(
        page.get_by_text(
            "The array below displays the user props you defined for this job."
        )
    ).to_be_visible()

    # Check displayed user props

    props_table = page.locator("table#user_props_table")
    expect(props_table).to_have_count(1)
    rows = props_table.locator("tbody tr")
    expect(rows).to_have_count(len(user_props))

    for i, (k, v) in enumerate(sorted(user_props.items(), key=lambda e: e[0])):
        row = rows.nth(i)
        cols = row.locator("td")
        expect(cols).to_have_count(2)
        expect(cols.nth(0)).to_contain_text(k)
        expect(cols.nth(1)).to_contain_text(str(v))
