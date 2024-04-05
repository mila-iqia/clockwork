from playwright.sync_api import Page, expect

from clockwork_frontend_test.utils import BASE_URL


# Expected jobs table content for first columns (cluster, user (@mila.quebec), job ID).
JOBS_SEARCH_DEFAULT_TABLE = [
    ["cedar", "student05 @mila.quebec", "162810"],
    ["mila", "student08 @mila.quebec", "159143"],
    ["mila", "student11 @mila.quebec", "821519"],
    ["mila", "student09 @mila.quebec", "587459"],
    ["mila", "student06 @mila.quebec", "795002"],
    ["mila", "student00 @mila.quebec", "988661"],
    ["mila", "student16 @mila.quebec", "606872"],
    ["mila", "student06 @mila.quebec", "462974"],
    ["mila", "student06 @mila.quebec", "591707"],
    ["mila", "student04 @mila.quebec", "895000"],
    ["mila", "student04 @mila.quebec", "199032"],
    ["mila", "student12 @mila.quebec", "658913"],
    ["mila", "student00 @mila.quebec", "688953"],
    ["mila", "student09 @mila.quebec", "6242"],
    ["graham", "student02 @mila.quebec", "176413"],
    ["graham", "student15 @mila.quebec", "834395"],
    ["graham", "student15 @mila.quebec", "154325"],
    ["graham", "student08 @mila.quebec", "573157"],
    ["graham", "student12 @mila.quebec", "613024"],
    ["graham", "student18 @mila.quebec", "711192"],
    ["graham", "student04 @mila.quebec", "755456"],
    ["cedar", "student18 @mila.quebec", "671999"],
    ["cedar", "student07 @mila.quebec", "474015"],
    ["cedar", "student11 @mila.quebec", "357153"],
    ["cedar", "student11 @mila.quebec", "739671"],
    ["cedar", "student03 @mila.quebec", "914229"],
    ["cedar", "student12 @mila.quebec", "395476"],
    ["cedar", "student15 @mila.quebec", "330000"],
    ["cedar", "student08 @mila.quebec", "709562"],
    ["cedar", "student07 @mila.quebec", "42644"],
    ["cedar", "student14 @mila.quebec", "528078"],
    ["cedar", "student11 @mila.quebec", "91221"],
    ["cedar", "student04 @mila.quebec", "239334"],
    ["graham", "student02 @mila.quebec", "162069"],
    ["graham", "student05 @mila.quebec", "340462"],
    ["graham", "student04 @mila.quebec", "213258"],
    ["graham", "student05 @mila.quebec", "374687"],
    ["beluga", "student17 @mila.quebec", "647328"],
    ["beluga", "student04 @mila.quebec", "822514"],
    ["beluga", "student09 @mila.quebec", "498497"],
]


def _load_jobs_search_page(page: Page):
    """Login and go to jobs search page."""
    # Login
    page.goto(f"{BASE_URL}/login/testing?user_id=student00@mila.quebec")
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
        f"username=student00@mila.quebec"
        f"&cluster_name=mila,narval,cedar,beluga,graham"
        f"&aggregated_job_state=COMPLETED,RUNNING,PENDING,FAILED"
        f"&nbr_items_per_page=40"
        f"&sort_by=submit_time"
        f"&sort_asc=-1"
    )
    _check_jobs_table(
        page,
        [
            ["mila", "student00 @mila.quebec", "988661"],
            ["mila", "student00 @mila.quebec", "688953"],
            ["narval", "student00 @mila.quebec", "429092"],
            ["graham", "student00 @mila.quebec", "213472"],
            ["mila", "student00 @mila.quebec", "914405"],
        ],
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
    _check_jobs_table(page, JOBS_SEARCH_DEFAULT_TABLE)


def test_filter_by_user_other_user(page: Page):
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
        f"username=student05@mila.quebec"
        f"&cluster_name=mila,narval,cedar,beluga,graham"
        f"&aggregated_job_state=COMPLETED,RUNNING,PENDING,FAILED"
        f"&nbr_items_per_page=40"
        f"&sort_by=submit_time"
        f"&sort_asc=-1"
    )
    _check_jobs_table(
        page,
        [
            ["cedar", "student05 @mila.quebec", "162810"],
            ["graham", "student05 @mila.quebec", "340462"],
            ["graham", "student05 @mila.quebec", "374687"],
            ["narval", "student05 @mila.quebec", "256638"],
            ["narval", "student05 @mila.quebec", "322466"],
            ["mila", "student05 @mila.quebec", "637504"],
        ],
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
        f"cluster_name=narval,cedar,beluga,graham"
        f"&aggregated_job_state=COMPLETED,RUNNING,PENDING,FAILED"
        f"&nbr_items_per_page=40&"
        f"sort_by=submit_time"
        f"&sort_asc=-1"
    )
    # Just check that first column (cluster) does not contain "mila".
    _check_jobs_table(
        page,
        [
            ["cedar"],
            ["graham"],
            ["graham"],
            ["graham"],
            ["graham"],
            ["graham"],
            ["graham"],
            ["graham"],
            ["cedar"],
            ["cedar"],
            ["cedar"],
            ["cedar"],
            ["cedar"],
            ["cedar"],
            ["cedar"],
            ["cedar"],
            ["cedar"],
            ["cedar"],
            ["cedar"],
            ["cedar"],
            ["graham"],
            ["graham"],
            ["graham"],
            ["graham"],
            ["beluga"],
            ["beluga"],
            ["beluga"],
            ["beluga"],
            ["beluga"],
            ["beluga"],
            ["beluga"],
            ["beluga"],
            ["beluga"],
            ["beluga"],
            ["beluga"],
            ["beluga"],
            ["beluga"],
            ["beluga"],
            ["beluga"],
            ["beluga"],
        ],
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
    _check_jobs_table(page, JOBS_SEARCH_DEFAULT_TABLE)


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
    _check_jobs_table(
        page,
        [
            ["graham"],
            ["graham"],
            ["graham"],
            ["graham"],
            ["graham"],
            ["graham"],
            ["graham"],
            ["graham"],
            ["graham"],
            ["graham"],
            ["graham"],
            ["beluga"],
            ["beluga"],
            ["beluga"],
            ["beluga"],
            ["beluga"],
            ["beluga"],
            ["beluga"],
            ["beluga"],
            ["beluga"],
            ["beluga"],
            ["beluga"],
            ["beluga"],
            ["beluga"],
            ["beluga"],
            ["beluga"],
            ["beluga"],
            ["beluga"],
            ["beluga"],
            ["beluga"],
            ["beluga"],
            ["beluga"],
            ["narval"],
            ["narval"],
            ["narval"],
            ["narval"],
            ["narval"],
            ["narval"],
            ["narval"],
            ["narval"],
        ],
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
    _check_jobs_table(page, JOBS_SEARCH_DEFAULT_TABLE)


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
        f"cluster_name=mila,narval,cedar,beluga,graham"
        f"&aggregated_job_state=COMPLETED,PENDING,FAILED"
        f"&nbr_items_per_page=40"
        f"&sort_by=submit_time"
        f"&sort_asc=-1"
    )
    _check_jobs_table(
        page,
        [
            ["cedar", "student05 @mila.quebec", "162810"],
            ["mila", "student11 @mila.quebec", "821519"],
            ["mila", "student09 @mila.quebec", "587459"],
            ["mila", "student06 @mila.quebec", "795002"],
            ["mila", "student00 @mila.quebec", "988661"],
            ["mila", "student16 @mila.quebec", "606872"],
            ["mila", "student06 @mila.quebec", "462974"],
            ["mila", "student06 @mila.quebec", "591707"],
            ["mila", "student04 @mila.quebec", "895000"],
            ["mila", "student04 @mila.quebec", "199032"],
            ["mila", "student12 @mila.quebec", "658913"],
            ["mila", "student00 @mila.quebec", "688953"],
            ["mila", "student09 @mila.quebec", "6242"],
            ["graham", "student02 @mila.quebec", "176413"],
            ["graham", "student15 @mila.quebec", "834395"],
            ["graham", "student15 @mila.quebec", "154325"],
            ["graham", "student08 @mila.quebec", "573157"],
            ["graham", "student12 @mila.quebec", "613024"],
            ["graham", "student18 @mila.quebec", "711192"],
            ["graham", "student04 @mila.quebec", "755456"],
            ["cedar", "student18 @mila.quebec", "671999"],
            ["cedar", "student07 @mila.quebec", "474015"],
            ["cedar", "student11 @mila.quebec", "357153"],
            ["cedar", "student11 @mila.quebec", "739671"],
            ["graham", "student02 @mila.quebec", "162069"],
            ["graham", "student05 @mila.quebec", "340462"],
            ["graham", "student04 @mila.quebec", "213258"],
            ["graham", "student05 @mila.quebec", "374687"],
            ["beluga", "student17 @mila.quebec", "647328"],
            ["beluga", "student04 @mila.quebec", "822514"],
            ["beluga", "student09 @mila.quebec", "498497"],
            ["beluga", "student07 @mila.quebec", "631744"],
            ["beluga", "student16 @mila.quebec", "72805"],
            ["beluga", "student16 @mila.quebec", "633149"],
            ["beluga", "student02 @mila.quebec", "628692"],
            ["beluga", "student17 @mila.quebec", "516434"],
            ["beluga", "student13 @mila.quebec", "618134"],
            ["beluga", "student02 @mila.quebec", "933740"],
            ["beluga", "student02 @mila.quebec", "22299"],
            ["beluga", "student16 @mila.quebec", "532606"],
        ],
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
        f"cluster_name=mila,narval,cedar,beluga,graham"
        f"&aggregated_job_state=PENDING,FAILED"
        f"&nbr_items_per_page=40"
        f"&sort_by=submit_time"
        f"&sort_asc=-1"
    )
    _check_jobs_table(
        page,
        [
            ["cedar", "student05 @mila.quebec", "162810"],
            ["mila", "student11 @mila.quebec", "821519"],
            ["mila", "student09 @mila.quebec", "587459"],
            ["mila", "student06 @mila.quebec", "795002"],
            ["mila", "student00 @mila.quebec", "988661"],
            ["mila", "student16 @mila.quebec", "606872"],
            ["mila", "student06 @mila.quebec", "462974"],
            ["mila", "student06 @mila.quebec", "591707"],
            ["mila", "student04 @mila.quebec", "895000"],
            ["mila", "student04 @mila.quebec", "199032"],
            ["mila", "student12 @mila.quebec", "658913"],
            ["mila", "student00 @mila.quebec", "688953"],
            ["mila", "student09 @mila.quebec", "6242"],
            ["graham", "student02 @mila.quebec", "176413"],
            ["graham", "student15 @mila.quebec", "834395"],
            ["graham", "student08 @mila.quebec", "573157"],
            ["graham", "student12 @mila.quebec", "613024"],
            ["graham", "student18 @mila.quebec", "711192"],
            ["graham", "student04 @mila.quebec", "755456"],
            ["cedar", "student18 @mila.quebec", "671999"],
            ["cedar", "student07 @mila.quebec", "474015"],
            ["cedar", "student11 @mila.quebec", "357153"],
            ["cedar", "student11 @mila.quebec", "739671"],
            ["graham", "student02 @mila.quebec", "162069"],
            ["graham", "student04 @mila.quebec", "213258"],
            ["graham", "student05 @mila.quebec", "374687"],
            ["beluga", "student17 @mila.quebec", "647328"],
            ["beluga", "student04 @mila.quebec", "822514"],
            ["beluga", "student09 @mila.quebec", "498497"],
            ["beluga", "student07 @mila.quebec", "631744"],
            ["beluga", "student16 @mila.quebec", "72805"],
            ["beluga", "student16 @mila.quebec", "633149"],
            ["beluga", "student02 @mila.quebec", "628692"],
            ["beluga", "student17 @mila.quebec", "516434"],
            ["beluga", "student13 @mila.quebec", "618134"],
            ["beluga", "student02 @mila.quebec", "933740"],
            ["beluga", "student02 @mila.quebec", "22299"],
            ["beluga", "student16 @mila.quebec", "532606"],
            ["beluga", "student04 @mila.quebec", "761751"],
            ["beluga", "student03 @mila.quebec", "911005"],
        ],
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
    _check_jobs_table(page, JOBS_SEARCH_DEFAULT_TABLE)


def test_multiple_filters(page: Page):
    # Only current user, and ignore cluster mila and status pending.
    _load_jobs_search_page(page)
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
        f"username=student00@mila.quebec"
        f"&cluster_name=narval,cedar,beluga,graham"
        f"&aggregated_job_state=COMPLETED,RUNNING,FAILED"
        f"&nbr_items_per_page=40"
        f"&sort_by=submit_time"
        f"&sort_asc=-1"
    )
    _check_jobs_table(page, [["graham", "student00 @mila.quebec", "213472"]])

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
    _check_jobs_table(page, JOBS_SEARCH_DEFAULT_TABLE)


def test_filter_by_job_array(page: Page):
    _load_jobs_search_page(page)
    job_id = page.get_by_text("834395")
    expect(job_id).to_have_count(1)
    parent_row = page.locator("table#search_table tbody tr").filter(has=job_id)
    expect(parent_row).to_have_count(1)
    cols = parent_row.locator("td")
    icon_job_array = cols.nth(3).locator("a")
    expect(icon_job_array).to_have_count(1)
    icon_job_array.click()
    expect(page).to_have_url(f"{BASE_URL}/jobs/search?job_array=834395&page_num=1")
    _check_jobs_table(page, [["graham", "student15 @mila.quebec", "834395"]])

    filter_reset = page.get_by_title("Reset filter by job array")
    expect(filter_reset).to_contain_text("Job array 834395")
    filter_reset.click()

    expect(page).to_have_url(f"{BASE_URL}/jobs/search?job_array=None&page_num=1")
    _check_jobs_table(page, JOBS_SEARCH_DEFAULT_TABLE)


def test_filter_by_job_user_props(page: Page):
    # Login
    page.goto(f"{BASE_URL}/login/testing?user_id=student01@mila.quebec")
    # Go to settings.
    page.goto(f"{BASE_URL}/settings/")
    radio_job_user_props = page.locator("input#jobs_list_job_user_props_toggle")
    expect(radio_job_user_props).to_be_checked(checked=False)
    # Check column job_user_props.
    radio_job_user_props.click()
    expect(radio_job_user_props).to_be_checked(checked=True)
    # Back to jobs/search.
    page.goto(f"{BASE_URL}/jobs/search")

    job_id = page.get_by_text("795002")
    expect(job_id).to_have_count(1)
    parent_row = page.locator("table#search_table tbody tr").filter(has=job_id)
    expect(parent_row).to_have_count(1)
    cols = parent_row.locator("td")
    link_job_user_prop = cols.nth(4).locator("a")
    expect(link_job_user_prop).to_have_count(1)
    expect(link_job_user_prop).to_contain_text("name je suis une user prop 1")
    link_job_user_prop.click()
    expect(page).to_have_url(
        f"{BASE_URL}/jobs/search?"
        f"user_prop_name=name"
        f"&user_prop_content=je+suis+une+user+prop+1"
        f"&page_num=1"
    )
    _check_jobs_table(
        page,
        [
            ["mila", "student06 @mila.quebec", "795002"],
            ["graham", "student12 @mila.quebec", "613024"],
        ],
    )

    filter_reset = page.get_by_title("Reset filter by job user prop")
    expect(filter_reset).to_contain_text('User prop name: "je suis une user prop 1"')
    filter_reset.click()

    expect(page).to_have_url(
        f"{BASE_URL}/jobs/search?user_prop_name=&user_prop_content=&page_num=1"
    )
    _check_jobs_table(page, JOBS_SEARCH_DEFAULT_TABLE)

    # Back to default settings.
    page.goto(f"{BASE_URL}/settings/")
    radio_job_user_props = page.locator("input#jobs_list_job_user_props_toggle")
    expect(radio_job_user_props).to_be_checked(checked=True)
    radio_job_user_props.click()
    expect(radio_job_user_props).to_be_checked(checked=False)


def test_jobs_table_sorting_by_cluster(page: Page):
    _load_jobs_search_page(page)
    expected_content = [
        ["beluga", "student02 @mila.quebec", "197775"],
        ["beluga", "student15 @mila.quebec", "217623"],
        ["beluga", "student02 @mila.quebec", "22299"],
        ["beluga", "student14 @mila.quebec", "237447"],
        ["beluga", "student18 @mila.quebec", "325922"],
        ["beluga", "student19 @mila.quebec", "411175"],
        ["beluga", "student09 @mila.quebec", "498497"],
        ["beluga", "student17 @mila.quebec", "516434"],
        ["beluga", "student16 @mila.quebec", "532606"],
        ["beluga", "student07 @mila.quebec", "587367"],
        ["beluga", "student13 @mila.quebec", "618134"],
        ["beluga", "student02 @mila.quebec", "628692"],
        ["beluga", "student07 @mila.quebec", "631744"],
        ["beluga", "student16 @mila.quebec", "633149"],
        ["beluga", "student17 @mila.quebec", "647328"],
        ["beluga", "student16 @mila.quebec", "72805"],
        ["beluga", "student04 @mila.quebec", "744881"],
        ["beluga", "student04 @mila.quebec", "761751"],
        ["beluga", "student15 @mila.quebec", "807865"],
        ["beluga", "student04 @mila.quebec", "822514"],
        ["beluga", "student03 @mila.quebec", "911005"],
        ["beluga", "student02 @mila.quebec", "933740"],
        ["cedar", "student05 @mila.quebec", "162810"],
        ["cedar", "student04 @mila.quebec", "239334"],
        ["cedar", "student15 @mila.quebec", "330000"],
        ["cedar", "student11 @mila.quebec", "357153"],
        ["cedar", "student12 @mila.quebec", "395476"],
        ["cedar", "student07 @mila.quebec", "42644"],
        ["cedar", "student07 @mila.quebec", "474015"],
        ["cedar", "student14 @mila.quebec", "528078"],
        ["cedar", "student18 @mila.quebec", "671999"],
        ["cedar", "student08 @mila.quebec", "709562"],
        ["cedar", "student11 @mila.quebec", "739671"],
        ["cedar", "student11 @mila.quebec", "91221"],
        ["cedar", "student03 @mila.quebec", "914229"],
        ["graham", "student15 @mila.quebec", "154325"],
        ["graham", "student02 @mila.quebec", "162069"],
        ["graham", "student02 @mila.quebec", "176413"],
        ["graham", "student16 @mila.quebec", "210984"],
        ["graham", "student04 @mila.quebec", "213258"],
    ]
    _check_jobs_table_sorting(page, 0, "Cluster", "cluster_name", expected_content)


def test_jobs_table_sorting_by_job_id(page: Page):
    _load_jobs_search_page(page)
    expected_content = [
        ["mila", "student00 @mila.quebec", "988661"],
        ["mila", "student15 @mila.quebec", "946069"],
        ["beluga", "student02 @mila.quebec", "933740"],
        ["mila", "student00 @mila.quebec", "914405"],
        ["cedar", "student03 @mila.quebec", "914229"],
        ["cedar", "student11 @mila.quebec", "91221"],
        ["beluga", "student03 @mila.quebec", "911005"],
        ["mila", "student04 @mila.quebec", "895000"],
        ["narval", "student17 @mila.quebec", "894480"],
        ["narval", "student10 @mila.quebec", "879054"],
        ["narval", "student15 @mila.quebec", "834677"],
        ["graham", "student15 @mila.quebec", "834395"],
        ["narval", "student19 @mila.quebec", "833046"],
        ["beluga", "student04 @mila.quebec", "822514"],
        ["mila", "student11 @mila.quebec", "821519"],
        ["graham", "student03 @mila.quebec", "8172"],
        ["beluga", "student15 @mila.quebec", "807865"],
        ["mila", "student06 @mila.quebec", "795002"],
        ["beluga", "student04 @mila.quebec", "761751"],
        ["narval", "student02 @mila.quebec", "760618"],
        ["graham", "student04 @mila.quebec", "755456"],
        ["narval", "student16 @mila.quebec", "748262"],
        ["beluga", "student04 @mila.quebec", "744881"],
        ["cedar", "student11 @mila.quebec", "739671"],
        ["beluga", "student16 @mila.quebec", "72805"],
        ["graham", "student18 @mila.quebec", "711192"],
        ["cedar", "student08 @mila.quebec", "709562"],
        ["mila", "student00 @mila.quebec", "688953"],
        ["cedar", "student18 @mila.quebec", "671999"],
        ["narval", "student15 @mila.quebec", "66711"],
        ["mila", "student12 @mila.quebec", "658913"],
        ["beluga", "student17 @mila.quebec", "647328"],
        ["mila", "student06 @mila.quebec", "645674"],
        ["mila", "student05 @mila.quebec", "637504"],
        ["beluga", "student16 @mila.quebec", "633149"],
        ["beluga", "student07 @mila.quebec", "631744"],
        ["beluga", "student02 @mila.quebec", "628692"],
        ["mila", "student09 @mila.quebec", "6242"],
        ["beluga", "student13 @mila.quebec", "618134"],
        ["graham", "student12 @mila.quebec", "613024"],
    ]
    _check_jobs_table_sorting(
        page, 2, "Job ID", "job_id", expected_content, reverse=True
    )


def test_jobs_table_sorting_by_job_id_ascending(page: Page):
    _load_jobs_search_page(page)
    expected_content = [
        ["narval", "student18 @mila.quebec", "102417"],
        ["narval", "student15 @mila.quebec", "136607"],
        ["narval", "student14 @mila.quebec", "149540"],
        ["graham", "student15 @mila.quebec", "154325"],
        ["mila", "student08 @mila.quebec", "159143"],
        ["graham", "student02 @mila.quebec", "162069"],
        ["cedar", "student05 @mila.quebec", "162810"],
        ["graham", "student02 @mila.quebec", "176413"],
        ["mila", "student02 @mila.quebec", "195046"],
        ["beluga", "student02 @mila.quebec", "197775"],
        ["mila", "student04 @mila.quebec", "199032"],
        ["narval", "student14 @mila.quebec", "202674"],
        ["narval", "student08 @mila.quebec", "206969"],
        ["graham", "student16 @mila.quebec", "210984"],
        ["graham", "student04 @mila.quebec", "213258"],
        ["graham", "student00 @mila.quebec", "213472"],
        ["narval", "student10 @mila.quebec", "216586"],
        ["beluga", "student15 @mila.quebec", "217623"],
        ["narval", "student16 @mila.quebec", "220838"],
        ["beluga", "student02 @mila.quebec", "22299"],
        ["beluga", "student14 @mila.quebec", "237447"],
        ["cedar", "student04 @mila.quebec", "239334"],
        ["narval", "student05 @mila.quebec", "256638"],
        ["graham", "student14 @mila.quebec", "260380"],
        ["narval", "student11 @mila.quebec", "281405"],
        ["graham", "", "284357"],
        ["narval", "student07 @mila.quebec", "285203"],
        ["graham", "student04 @mila.quebec", "295441"],
        ["narval", "student05 @mila.quebec", "322466"],
        ["beluga", "student18 @mila.quebec", "325922"],
        ["cedar", "student15 @mila.quebec", "330000"],
        ["graham", "student05 @mila.quebec", "340462"],
        ["narval", "student03 @mila.quebec", "350633"],
        ["cedar", "student11 @mila.quebec", "357153"],
        ["graham", "student05 @mila.quebec", "374687"],
        ["narval", "student09 @mila.quebec", "385631"],
        ["cedar", "student12 @mila.quebec", "395476"],
        ["graham", "student01 @mila.quebec", "401253"],
        ["beluga", "student19 @mila.quebec", "411175"],
        ["graham", "student17 @mila.quebec", "412365"],
    ]
    _check_jobs_table_sorting(
        page, 2, "Job ID", "job_id", expected_content, double_click=True, reverse=False
    )


def test_jobs_table_sorting_by_end_time(page: Page):
    _load_jobs_search_page(page)
    expected_content = [
        ["cedar", "student18 @mila.quebec", "671999"],
        ["graham", "student01 @mila.quebec", "401253"],
        ["graham", "student17 @mila.quebec", "462729"],
        ["beluga", "student18 @mila.quebec", "325922"],
        ["mila", "student16 @mila.quebec", "606872"],
        ["graham", "student05 @mila.quebec", "340462"],
        ["graham", "student00 @mila.quebec", "213472"],
        ["graham", "student17 @mila.quebec", "412365"],
        ["graham", "student15 @mila.quebec", "834395"],
        ["mila", "student06 @mila.quebec", "591707"],
        ["mila", "student06 @mila.quebec", "462974"],
        ["mila", "student11 @mila.quebec", "821519"],
        ["mila", "student04 @mila.quebec", "199032"],
        ["mila", "student12 @mila.quebec", "658913"],
        ["mila", "student00 @mila.quebec", "688953"],
        ["mila", "student06 @mila.quebec", "795002"],
        ["mila", "student09 @mila.quebec", "587459"],
        ["mila", "student04 @mila.quebec", "895000"],
        ["mila", "student09 @mila.quebec", "6242"],
        ["cedar", "student05 @mila.quebec", "162810"],
        ["graham", "student08 @mila.quebec", "573157"],
        ["graham", "student15 @mila.quebec", "154325"],
        ["mila", "student00 @mila.quebec", "988661"],
        ["narval", "student18 @mila.quebec", "102417"],
        ["narval", "student15 @mila.quebec", "136607"],
        ["narval", "student14 @mila.quebec", "149540"],
        ["mila", "student08 @mila.quebec", "159143"],
        ["graham", "student02 @mila.quebec", "162069"],
        ["graham", "student02 @mila.quebec", "176413"],
        ["mila", "student02 @mila.quebec", "195046"],
        ["beluga", "student02 @mila.quebec", "197775"],
        ["narval", "student14 @mila.quebec", "202674"],
        ["narval", "student08 @mila.quebec", "206969"],
        ["graham", "student16 @mila.quebec", "210984"],
        ["graham", "student04 @mila.quebec", "213258"],
        ["narval", "student10 @mila.quebec", "216586"],
        ["beluga", "student15 @mila.quebec", "217623"],
        ["narval", "student16 @mila.quebec", "220838"],
        ["beluga", "student02 @mila.quebec", "22299"],
        ["beluga", "student14 @mila.quebec", "237447"],
    ]
    _check_jobs_table_sorting(
        page, 8, "End time", "end_time", expected_content, reverse=True
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
    # _print_table(page, column_id)
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
    print(content)
