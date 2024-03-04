from playwright.sync_api import Page, expect

from clockwork_frontend_test.utils import BASE_URL


def test_languages(page: Page):
    # Login
    page.goto(f"{BASE_URL}/login/testing?user_id=student00@mila.quebec")
    header_title = page.locator("#formBlock > .container .title.float-start h1")
    # Check language. Should be english.
    expect(header_title).to_contain_text("Welcome back student00 !")

    # Go to settings.
    page.goto(f"{BASE_URL}/settings/")
    # Get language select.
    select = page.locator("select#language_selection")
    # Check default language is english.
    expect(select).to_have_value("en")
    # Switch to French.
    select.select_option("fr")
    # Check french is selected.
    expect(select).to_have_value("fr")
    # Go to dashboard page and check language. Should be French.
    page.goto(f"{BASE_URL}/jobs/dashboard")
    header_title = page.locator("#formBlock > .container .title.float-start h1")
    expect(header_title).to_contain_text("Bienvenue student00 !")

    # Move back to english (necessary to not interfere with other tests)
    page.goto(f"{BASE_URL}/settings/")
    select = page.locator("select#language_selection")
    select.select_option("en")
    expect(select).to_have_value("en")
    page.goto(f"{BASE_URL}/jobs/dashboard")
    header_title = page.locator("#formBlock > .container .title.float-start h1")
    expect(header_title).to_contain_text("Welcome back student00 !")


def test_nb_items_per_page(page: Page):
    # Login
    page.goto(f"{BASE_URL}/login/testing?user_id=student00@mila.quebec")
    # Go to jobs/search page
    page.goto(f"{BASE_URL}/jobs/search")
    # Check we have 40 rows by default in table.
    rows = page.locator("table#search_table tbody tr")
    expect(rows).to_have_count(40)
    # Check we have 3 pages in table nav.
    nav_elements = page.locator("nav.table_nav ul.pagination li.page-item")
    expect(nav_elements).to_have_count(6)
    expect(nav_elements.nth(0)).to_have_class("page-item first")
    expect(nav_elements.nth(1)).to_have_class("page-item current")
    expect(nav_elements.nth(1)).to_have_text("1")
    expect(nav_elements.nth(2)).to_have_text("2")
    expect(nav_elements.nth(3)).to_have_text("3")
    expect(nav_elements.nth(4)).to_have_class("page-item last")
    expect(nav_elements.nth(5)).to_have_class("page-item last")

    # Go to settings.
    page.goto(f"{BASE_URL}/settings/")
    # Check we display 40 jobs per page per default.
    select = page.locator("select#nbr_items_per_page_selection")
    expect(select).to_have_value("40")
    # Switch to 25 jobs.
    select.select_option("25")
    expect(select).to_have_value("25")

    # Go back to jobs/search and check table and nav.
    page.goto(f"{BASE_URL}/jobs/search")
    rows = page.locator("table#search_table tbody tr")
    expect(rows).to_have_count(25)
    nav_elements = page.locator("nav.table_nav ul.pagination li")
    expect(nav_elements).to_have_count(8)
    expect(nav_elements.nth(0)).to_have_class("page-item first")
    expect(nav_elements.nth(1)).to_have_class("page-item current")
    expect(nav_elements.nth(1)).to_have_text("1")
    expect(nav_elements.nth(2)).to_have_text("2")
    expect(nav_elements.nth(3)).to_have_text("3")
    expect(nav_elements.nth(4)).to_have_text("4")
    expect(nav_elements.nth(5)).to_have_text("...")
    expect(nav_elements.nth(6)).to_have_class("page-item last")
    expect(nav_elements.nth(7)).to_have_class("page-item last")

    # Move back to 40 jobs per page.
    page.goto(f"{BASE_URL}/settings/")
    select = page.locator("select#nbr_items_per_page_selection")
    select.select_option("40")
    expect(select).to_have_value("40")
    page.goto(f"{BASE_URL}/jobs/search")
    rows = page.locator("table#search_table tbody tr")
    expect(rows).to_have_count(40)


def test_dashboard_columns(page: Page):
    # Login
    page.goto(f"{BASE_URL}/login/testing?user_id=student00@mila.quebec")
    # Check default dashboard columns.
    headers = page.locator("table#dashboard_table thead tr th")
    expect(headers).to_have_count(8)
    expect(headers.nth(0)).to_contain_text("Cluster")
    expect(headers.nth(1)).to_contain_text("Job ID")
    expect(headers.nth(2)).to_contain_text("Job name [:20]")
    expect(headers.nth(3)).to_contain_text("Job state")
    expect(headers.nth(4)).to_contain_text("Submit time")
    expect(headers.nth(5)).to_contain_text("Start time")
    expect(headers.nth(6)).to_contain_text("End time")
    expect(headers.nth(7)).to_contain_text("Links")

    # Go to settings.
    page.goto(f"{BASE_URL}/settings/")
    radio_job_id = page.locator("input#dashboard_job_id_toggle")
    radio_submit_time = page.locator("input#dashboard_submit_time_toggle")
    expect(radio_job_id).to_be_checked(checked=True)
    expect(radio_submit_time).to_be_checked(checked=True)
    # Uncheck columns job ID and submit time.
    radio_job_id.click()
    radio_submit_time.click()
    expect(radio_job_id).to_be_checked(checked=False)
    expect(radio_submit_time).to_be_checked(checked=False)

    # Check columns are indeed not displayed in dashboard.
    page.goto(f"{BASE_URL}/jobs/dashboard")
    headers = page.locator("table#dashboard_table thead tr th")
    expect(headers).to_have_count(6)
    expect(headers.nth(0)).to_contain_text("Cluster")
    expect(headers.nth(1)).to_contain_text("Job name [:20]")
    expect(headers.nth(2)).to_contain_text("Job state")
    expect(headers.nth(3)).to_contain_text("Start time")
    expect(headers.nth(4)).to_contain_text("End time")
    expect(headers.nth(5)).to_contain_text("Links")

    # Back to default settings (re-check columns job ID and submit time).
    page.goto(f"{BASE_URL}/settings/")
    radio_job_id = page.locator("input#dashboard_job_id_toggle")
    radio_submit_time = page.locator("input#dashboard_submit_time_toggle")
    expect(radio_job_id).to_be_checked(checked=False)
    expect(radio_submit_time).to_be_checked(checked=False)
    radio_job_id.click()
    radio_submit_time.click()
    expect(radio_job_id).to_be_checked(checked=True)
    expect(radio_submit_time).to_be_checked(checked=True)
    page.goto(f"{BASE_URL}/jobs/dashboard")
    headers = page.locator("table#dashboard_table thead tr th")
    expect(headers).to_have_count(8)
    expect(headers.nth(0)).to_contain_text("Cluster")
    expect(headers.nth(1)).to_contain_text("Job ID")
    expect(headers.nth(2)).to_contain_text("Job name [:20]")
    expect(headers.nth(3)).to_contain_text("Job state")
    expect(headers.nth(4)).to_contain_text("Submit time")
    expect(headers.nth(5)).to_contain_text("Start time")
    expect(headers.nth(6)).to_contain_text("End time")
    expect(headers.nth(7)).to_contain_text("Links")


def test_jobs_search_columns(page: Page):
    # Login
    page.goto(f"{BASE_URL}/login/testing?user_id=student00@mila.quebec")
    # Check default jobs search columns.
    page.goto(f"{BASE_URL}/jobs/search")
    headers = page.locator("table#search_table thead tr th")
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

    # Go to settings.
    page.goto(f"{BASE_URL}/settings/")
    radio_job_id = page.locator("input#jobs_list_job_id_toggle")
    radio_job_array = page.locator("input#jobs_list_job_array_toggle")
    radio_submit_time = page.locator("input#jobs_list_submit_time_toggle")
    expect(radio_job_id).to_be_checked(checked=True)
    expect(radio_job_array).to_be_checked(checked=True)
    expect(radio_submit_time).to_be_checked(checked=True)
    # Uncheck columns job ID, job array and submit time.
    radio_job_id.click()
    radio_job_array.click()
    radio_submit_time.click()
    expect(radio_job_id).to_be_checked(checked=False)
    expect(radio_job_array).to_be_checked(checked=False)
    expect(radio_submit_time).to_be_checked(checked=False)

    # Check columns are indeed not displayed in jobs/search.
    page.goto(f"{BASE_URL}/jobs/search")
    headers = page.locator("table#search_table thead tr th")
    expect(headers).to_have_count(7)
    expect(headers.nth(0)).to_contain_text("Cluster")
    expect(headers.nth(1)).to_contain_text("User (@mila.quebec)")
    expect(headers.nth(2)).to_contain_text("Job name [:20]")
    expect(headers.nth(3)).to_contain_text("Job state")
    expect(headers.nth(4)).to_contain_text("Start time")
    expect(headers.nth(5)).to_contain_text("End time")
    expect(headers.nth(6)).to_contain_text("Links")

    # Back to default settings (re-check columns job ID, job array and submit time).
    page.goto(f"{BASE_URL}/settings/")
    radio_job_id = page.locator("input#jobs_list_job_id_toggle")
    radio_job_array = page.locator("input#jobs_list_job_array_toggle")
    radio_submit_time = page.locator("input#jobs_list_submit_time_toggle")
    expect(radio_job_id).to_be_checked(checked=False)
    expect(radio_job_array).to_be_checked(checked=False)
    expect(radio_submit_time).to_be_checked(checked=False)
    radio_job_id.click()
    radio_job_array.click()
    radio_submit_time.click()
    expect(radio_job_id).to_be_checked(checked=True)
    expect(radio_job_array).to_be_checked(checked=True)
    expect(radio_submit_time).to_be_checked(checked=True)
    page.goto(f"{BASE_URL}/jobs/search")
    headers = page.locator("table#search_table thead tr th")
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
