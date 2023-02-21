"""
Tests for the clockwork_web.core.pagination_helper functions.
"""

import pytest

from clockwork_web.core.pagination_helper import get_pagination_values
from clockwork_web.core.users_helper import (
    get_default_setting_value,
    set_items_per_page,
)

###
#   Tests of get_pagination_values
#
#   In order to keep the semantic of each testing function, a certain
#   amount of functions are written instead only one full parametrized.
#
#   As the name of the variables are pretty long, the functions' names
#   present this format (this could be changed if wanted):
#
#   - The first part of the name is "test_get_pagination_" to keep the
#     structure of the other Clockwork tests
#   - The second part is the user's status. It takes either "none_user_",
#     "unknwon_user_" or "known_user_" as values
#   - The third part refers to the page number; related to the page_num
#     argument of the function to test. It takes either "wrong_type",
#     "negative_value" or "positive_value" as values
#   - The fourth part refers to the number of items to display per page
#     related to the nbr_items_per_page argument of the function to test.
#     It takes either "wrong_type", "negative_value" or "positive_value" as values
#
#   Thus, the function:
#       test_get_pagination_known_user_wrong_type_negative_value
#   tests the function get_pagination_values with:
#       - a known user (ie it is stored in the database)
#       - a page_num argument presenting another type than integer
#       - a nbr_items_per_page argument set at 0 or a negative integer
###

# When user is None

# When user is None and page_num of wrong type
@pytest.mark.parametrize(
    "page_num,nbr_items_per_page",
    [("pifpafpouf", True), (None, [1, 2, 3]), ({}, (4, 5, 6))],
)
def test_get_pagination_none_user_wrong_type_wrong_type(
    app, page_num, nbr_items_per_page
):
    """
    Test the function get_pagination_values with:
    - None as the current_user_mila_email parameter
    - The page_num argument presenting a type different from integer
    - The nbr_items_per_page presenting a type different from integer

    Parameters:
        app                                 The scope of our tests, used to set
                                            the context (to access MongoDB)
        page_num                            The page number to pass as argument
        nbr_items_per_page                  The number of elements to display per
                                            page, to pass as argument
    """
    # Define the current_user_mila_email to be tested
    none_user = None

    # Define the expected results
    # The number of skipped items we expect to retrieve in the function's return
    expected_nbr_of_skipped_items = 0
    # The number of elements to display per page we expect to retrieve in the
    # function's return
    expected_nbr_items_per_page = get_default_setting_value("nbr_items_per_page")

    # Use the app context
    with app.app_context():
        # Call the function with the input parameters
        (
            retrieved_nbr_of_skipped_items,
            retrieved_nbr_items_per_page,
        ) = get_pagination_values(none_user, page_num, nbr_items_per_page)

        # Assert the values we retrieve equal the values we expect
        assert retrieved_nbr_items_per_page == expected_nbr_items_per_page
        assert retrieved_nbr_of_skipped_items == expected_nbr_of_skipped_items


@pytest.mark.parametrize(
    "page_num,nbr_items_per_page", [("pifpafpouf", -34), (None, -6), ({}, 0)]
)
def test_get_pagination_none_user_wrong_type_negative_value(
    app, page_num, nbr_items_per_page
):
    """
    Test the function get_pagination_values with:
    - None as the current_user_mila_email parameter
    - The page_num argument presenting a type different from integer
    - The nbr_items_per_page presenting 0 or a negative integer as value

    Parameters:
        app                                 The scope of our tests, used to set
                                            the context (to access MongoDB)
        page_num                            The page number to pass as argument
        nbr_items_per_page                  The number of elements to display per
                                            page, to pass as argument
    """
    # Define the current_user_mila_email to be tested
    none_user = None

    # Define the expected results
    # The number of skipped items we expect to retrieve in the function's return
    expected_nbr_of_skipped_items = 0
    # The number of elements to display per page we expect to retrieve in the
    # function's return
    expected_nbr_items_per_page = get_default_setting_value("nbr_items_per_page")

    # Use the app context
    with app.app_context():
        # Call the function with the input parameters
        (
            retrieved_nbr_of_skipped_items,
            retrieved_nbr_items_per_page,
        ) = get_pagination_values(none_user, page_num, nbr_items_per_page)

        # Assert the values we retrieve equal the values we expect
        assert retrieved_nbr_items_per_page == expected_nbr_items_per_page
        assert retrieved_nbr_of_skipped_items == expected_nbr_of_skipped_items


@pytest.mark.parametrize(
    "page_num,nbr_items_per_page", [(True, 5), ([1, 2, 3], 42), ((4, 5, 6), 117)]
)
def test_get_pagination_none_user_wrong_type_positive_value(
    app, page_num, nbr_items_per_page
):
    """
    Test the function get_pagination_values with:
    - None as the current_user_mila_email parameter
    - The page_num argument presenting a type different from integer
    - The nbr_items_per_page presenting a positive integer as value

    Parameters:
        app                                 The scope of our tests, used to set
                                            the context (to access MongoDB)
        page_num                            The page number to pass as argument
        nbr_items_per_page                  The number of elements to display per
                                            page, to pass as argument
    """
    # Define the current_user_mila_email to be tested
    none_user = None

    # Define the expected results
    # The number of skipped items we expect to retrieve in the function's return
    expected_nbr_of_skipped_items = 0
    # The number of elements to display per page we expect to retrieve in the
    # function's return
    expected_nbr_items_per_page = nbr_items_per_page

    # Use the app context
    with app.app_context():
        # Call the function with the input parameters
        (
            retrieved_nbr_of_skipped_items,
            retrieved_nbr_items_per_page,
        ) = get_pagination_values(none_user, page_num, nbr_items_per_page)

        # Assert the values we retrieve equal the values we expect
        assert retrieved_nbr_items_per_page == expected_nbr_items_per_page
        assert retrieved_nbr_of_skipped_items == expected_nbr_of_skipped_items


# When user is None and page_num 0 or a negative integer
@pytest.mark.parametrize(
    "page_num,nbr_items_per_page", [(-66, True), (-578, [1, 2, 3]), (-1, (4, 5, 6))]
)
def test_get_pagination_none_user_negative_value_wrong_type(
    app, page_num, nbr_items_per_page
):
    """
    Test the function get_pagination_values with:
    - None as the current_user_mila_email parameter
    - The page_num argument presenting 0 or a negative integer as value
    - The nbr_items_per_page presenting a type different from integer

    Parameters:
        app                                 The scope of our tests, used to set
                                            the context (to access MongoDB)
        page_num                            The page number to pass as argument
        nbr_items_per_page                  The number of elements to display per
                                            page, to pass as argument
    """
    # Define the current_user_mila_email to be tested
    none_user = None

    # Define the expected results
    # The number of skipped items we expect to retrieve in the function's return
    expected_nbr_of_skipped_items = 0
    # The number of elements to display per page we expect to retrieve in the
    # function's return
    expected_nbr_items_per_page = get_default_setting_value("nbr_items_per_page")

    # Use the app context
    with app.app_context():
        # Call the function with the input parameters
        (
            retrieved_nbr_of_skipped_items,
            retrieved_nbr_items_per_page,
        ) = get_pagination_values(none_user, page_num, nbr_items_per_page)

        # Assert the values we retrieve equal the values we expect
        assert retrieved_nbr_items_per_page == expected_nbr_items_per_page
        assert retrieved_nbr_of_skipped_items == expected_nbr_of_skipped_items


@pytest.mark.parametrize(
    "page_num,nbr_items_per_page", [(-10, 0), (-6, -144), (-10001, -9)]
)
def test_get_pagination_none_user_negative_value_negative_value(
    app, page_num, nbr_items_per_page
):
    """
    Test the function get_pagination_values with:
    - None as the current_user_mila_email parameter
    - The page_num argument presenting 0 or a negative integer as value
    - The nbr_items_per_page presenting 0 or a negative integer as value

    Parameters:
        app                                 The scope of our tests, used to set
                                            the context (to access MongoDB)
        page_num                            The page number to pass as argument
        nbr_items_per_page                  The number of elements to display per
                                            page, to pass as argument
    """
    # Define the current_user_mila_email to be tested
    none_user = None

    # Define the expected results
    # The number of skipped items we expect to retrieve in the function's return
    expected_nbr_of_skipped_items = 0
    # The number of elements to display per page we expect to retrieve in the
    # function's return
    expected_nbr_items_per_page = get_default_setting_value("nbr_items_per_page")

    # Use the app context
    with app.app_context():
        # Call the function with the input parameters
        (
            retrieved_nbr_of_skipped_items,
            retrieved_nbr_items_per_page,
        ) = get_pagination_values(none_user, page_num, nbr_items_per_page)

        # Assert the values we retrieve equal the values we expect
        assert retrieved_nbr_items_per_page == expected_nbr_items_per_page
        assert retrieved_nbr_of_skipped_items == expected_nbr_of_skipped_items


@pytest.mark.parametrize(
    "page_num,nbr_items_per_page", [(-6, 10), (0, 24), (-137, 200)]
)
def test_get_pagination_none_user_negative_value_positive_value(
    app, page_num, nbr_items_per_page
):
    """
    Test the function get_pagination_values with:
    - None as the current_user_mila_email parameter
    - The page_num argument presenting 0 or a negative integer as value
    - The nbr_items_per_page presenting a positive integer as value

    Parameters:
        app                                 The scope of our tests, used to set
                                            the context (to access MongoDB)
        page_num                            The page number to pass as argument
        nbr_items_per_page                  The number of elements to display per
                                            page, to pass as argument
    """
    # Define the current_user_mila_email to be tested
    none_user = None

    # Define the expected results
    # The number of skipped items we expect to retrieve in the function's return
    expected_nbr_of_skipped_items = 0
    # The number of elements to display per page we expect to retrieve in the
    # function's return
    expected_nbr_items_per_page = nbr_items_per_page

    # Use the app context
    with app.app_context():
        # Call the function with the input parameters
        (
            retrieved_nbr_of_skipped_items,
            retrieved_nbr_items_per_page,
        ) = get_pagination_values(none_user, page_num, nbr_items_per_page)

        # Assert the values we retrieve equal the values we expect
        assert retrieved_nbr_items_per_page == expected_nbr_items_per_page
        assert retrieved_nbr_of_skipped_items == expected_nbr_of_skipped_items


# When user is None and page_num a positive integer
@pytest.mark.parametrize(
    "page_num,nbr_items_per_page", [(1, True), (45, [1, 2, 3]), (19, (4, 5, 6))]
)
def test_get_pagination_none_user_positive_value_wrong_type(
    app, page_num, nbr_items_per_page
):
    """
    Test the function get_pagination_values with:
    - None as the current_user_mila_email parameter
    - The page_num argument presenting a positive integer as value
    - The nbr_items_per_page presenting a type different from integer

    Parameters:
        app                                 The scope of our tests, used to set
                                            the context (to access MongoDB)
        page_num                            The page number to pass as argument
        nbr_items_per_page                  The number of elements to display per
                                            page, to pass as argument
    """
    # Define the current_user_mila_email to be tested
    none_user = None

    # Define the expected results
    # The number of elements to display per page we expect to retrieve in the
    # function's return
    expected_nbr_items_per_page = get_default_setting_value("nbr_items_per_page")
    # The number of skipped items we expect to retrieve in the function's return
    expected_nbr_of_skipped_items = (page_num - 1) * expected_nbr_items_per_page

    # Use the app context
    with app.app_context():
        # Call the function with the input parameters
        (
            retrieved_nbr_of_skipped_items,
            retrieved_nbr_items_per_page,
        ) = get_pagination_values(none_user, page_num, nbr_items_per_page)

        # Assert the values we retrieve equal the values we expect
        assert retrieved_nbr_items_per_page == expected_nbr_items_per_page
        assert retrieved_nbr_of_skipped_items == expected_nbr_of_skipped_items


@pytest.mark.parametrize("page_num,nbr_items_per_page", [(24, 0), (46, -70), (10, -5)])
def test_get_pagination_none_user_positive_value_negative_value(
    app, page_num, nbr_items_per_page
):
    """
    Test the function get_pagination_values with:
    - None as the current_user_mila_email parameter
    - The page_num argument presenting a positive integer as value
    - The nbr_items_per_page presenting 0 or a negative integer as value

    Parameters:
        app                                 The scope of our tests, used to set
                                            the context (to access MongoDB)
        page_num                            The page number to pass as argument
        nbr_items_per_page                  The number of elements to display per
                                            page, to pass as argument
    """
    # Define the current_user_mila_email to be tested
    none_user = None

    # Define the expected results
    # The number of elements to display per page we expect to retrieve in the
    # function's return
    expected_nbr_items_per_page = get_default_setting_value("nbr_items_per_page")
    # The number of skipped items we expect to retrieve in the function's return
    expected_nbr_of_skipped_items = (page_num - 1) * expected_nbr_items_per_page

    # Use the app context
    with app.app_context():
        # Call the function with the input parameters
        (
            retrieved_nbr_of_skipped_items,
            retrieved_nbr_items_per_page,
        ) = get_pagination_values(none_user, page_num, nbr_items_per_page)

        # Assert the values we retrieve equal the values we expect
        assert retrieved_nbr_items_per_page == expected_nbr_items_per_page
        assert retrieved_nbr_of_skipped_items == expected_nbr_of_skipped_items


@pytest.mark.parametrize("page_num,nbr_items_per_page", [(10, 33), (42, 6), (5, 5)])
def test_get_pagination_none_user_positive_value_positive_value(
    app, page_num, nbr_items_per_page
):
    """
    Test the function get_pagination_values with:
    - None as the current_user_mila_email parameter
    - The page_num argument presenting a positive integer as value
    - The nbr_items_per_page presenting a positive integer as value

    Parameters:
        app                                 The scope of our tests, used to set
                                            the context (to access MongoDB)
        page_num                            The page number to pass as argument
        nbr_items_per_page                  The number of elements to display per
                                            page, to pass as argument
    """
    # Define the current_user_mila_email to be tested
    none_user = None

    # Define the expected results
    # The number of elements to display per page we expect to retrieve in the
    # function's return
    expected_nbr_items_per_page = nbr_items_per_page
    # The number of skipped items we expect to retrieve in the function's return
    expected_nbr_of_skipped_items = (page_num - 1) * expected_nbr_items_per_page

    # Use the app context
    with app.app_context():
        # Call the function with the input parameters
        (
            retrieved_nbr_of_skipped_items,
            retrieved_nbr_items_per_page,
        ) = get_pagination_values(none_user, page_num, nbr_items_per_page)

        # Assert the values we retrieve equal the values we expect
        assert retrieved_nbr_items_per_page == expected_nbr_items_per_page
        assert retrieved_nbr_of_skipped_items == expected_nbr_of_skipped_items


# When user is unknown

# When user is unknown and page_num of wrong type
@pytest.mark.parametrize(
    "page_num,nbr_items_per_page",
    [("pifpafpouf", True), (None, [1, 2, 3]), ({}, (4, 5, 6))],
)
def test_get_pagination_unknown_user_wrong_type_wrong_type(
    app, page_num, nbr_items_per_page
):
    """
    Test the function get_pagination_values with:
    - An unknown user as the current_user_mila_email parameter
    - The page_num argument presenting a type different from integer
    - The nbr_items_per_page presenting a type different from integer

    Parameters:
        app                                 The scope of our tests, used to set
                                            the context (to access MongoDB)
        page_num                            The page number to pass as argument
        nbr_items_per_page                  The number of elements to display per
                                            page, to pass as argument
    """
    # Define the current_user_mila_email to be tested
    unknown_user = "unknownuser"

    # Define the expected results
    # The number of elements to display per page we expect to retrieve in the
    # function's return
    expected_nbr_items_per_page = get_default_setting_value("nbr_items_per_page")
    # The number of skipped items we expect to retrieve in the function's return
    expected_nbr_of_skipped_items = 0

    # Use the app context
    with app.app_context():
        # Call the function with the input parameters
        (
            retrieved_nbr_of_skipped_items,
            retrieved_nbr_items_per_page,
        ) = get_pagination_values(unknown_user, page_num, nbr_items_per_page)

        # Assert the values we retrieve equal the values we expect
        assert retrieved_nbr_items_per_page == expected_nbr_items_per_page
        assert retrieved_nbr_of_skipped_items == expected_nbr_of_skipped_items


@pytest.mark.parametrize(
    "page_num,nbr_items_per_page", [("pifpafpouf", -34), (None, -6), ({}, 0)]
)
def test_get_pagination_unknown_user_wrong_type_negative_value(
    app, page_num, nbr_items_per_page
):
    """
    Test the function get_pagination_values with:
    - An unknown user as the current_user_mila_email parameter
    - The page_num argument presenting a type different from integer
    - The nbr_items_per_page presenting 0 or a negative integer as value

    Parameters:
        app                                 The scope of our tests, used to set
                                            the context (to access MongoDB)
        page_num                            The page number to pass as argument
        nbr_items_per_page                  The number of elements to display per
                                            page, to pass as argument
    """
    # Define the current_user_mila_email to be tested
    unknown_user = "unknownuser"

    # Define the expected results
    # The number of elements to display per page we expect to retrieve in the
    # function's return
    expected_nbr_items_per_page = get_default_setting_value("nbr_items_per_page")
    # The number of skipped items we expect to retrieve in the function's return
    expected_nbr_of_skipped_items = 0

    # Use the app context
    with app.app_context():
        # Call the function with the input parameters
        (
            retrieved_nbr_of_skipped_items,
            retrieved_nbr_items_per_page,
        ) = get_pagination_values(unknown_user, page_num, nbr_items_per_page)

        # Assert the values we retrieve equal the values we expect
        assert retrieved_nbr_items_per_page == expected_nbr_items_per_page
        assert retrieved_nbr_of_skipped_items == expected_nbr_of_skipped_items


@pytest.mark.parametrize(
    "page_num,nbr_items_per_page", [(True, 5), ([1, 2, 3], 42), ((4, 5, 6), 117)]
)
def test_get_pagination_unknown_user_wrong_type_positive_value(
    app, page_num, nbr_items_per_page
):
    """
    Test the function get_pagination_values with:
    - An unknown user as the current_user_mila_email parameter
    - The page_num argument presenting a type different from integer
    - The nbr_items_per_page presenting a positive integer as value

    Parameters:
        app                                 The scope of our tests, used to set
                                            the context (to access MongoDB)
        page_num                            The page number to pass as argument
        nbr_items_per_page                  The number of elements to display per
                                            page, to pass as argument
    """
    # Define the current_user_mila_email to be tested
    unknown_user = "unknownuser"

    # Define the expected results
    # The number of elements to display per page we expect to retrieve in the
    # function's return
    expected_nbr_items_per_page = nbr_items_per_page
    # The number of skipped items we expect to retrieve in the function's return
    expected_nbr_of_skipped_items = 0

    # Use the app context
    with app.app_context():
        # Call the function with the input parameters
        (
            retrieved_nbr_of_skipped_items,
            retrieved_nbr_items_per_page,
        ) = get_pagination_values(unknown_user, page_num, nbr_items_per_page)

        # Assert the values we retrieve equal the values we expect
        assert retrieved_nbr_items_per_page == expected_nbr_items_per_page
        assert retrieved_nbr_of_skipped_items == expected_nbr_of_skipped_items


# When user is unknown and page_num 0 or a negative integer
@pytest.mark.parametrize(
    "page_num,nbr_items_per_page", [(-66, True), (-578, [1, 2, 3]), (-1, (4, 5, 6))]
)
def test_get_pagination_unknown_user_negative_value_wrong_type(
    app, page_num, nbr_items_per_page
):
    """
    Test the function get_pagination_values with:
    - An unknown user as the current_user_mila_email parameter
    - The page_num argument presenting 0 or a negative integer as value
    - The nbr_items_per_page presenting a type different from integer

    Parameters:
        app                                 The scope of our tests, used to set
                                            the context (to access MongoDB)
        page_num                            The page number to pass as argument
        nbr_items_per_page                  The number of elements to display per
                                            page, to pass as argument
    """
    # Define the current_user_mila_email to be tested
    unknown_user = "unknownuser"

    # Define the expected results
    # The number of elements to display per page we expect to retrieve in the
    # function's return
    expected_nbr_items_per_page = get_default_setting_value("nbr_items_per_page")
    # The number of skipped items we expect to retrieve in the function's return
    expected_nbr_of_skipped_items = 0

    # Use the app context
    with app.app_context():
        # Call the function with the input parameters
        (
            retrieved_nbr_of_skipped_items,
            retrieved_nbr_items_per_page,
        ) = get_pagination_values(unknown_user, page_num, nbr_items_per_page)

        # Assert the values we retrieve equal the values we expect
        assert retrieved_nbr_items_per_page == expected_nbr_items_per_page
        assert retrieved_nbr_of_skipped_items == expected_nbr_of_skipped_items


@pytest.mark.parametrize(
    "page_num,nbr_items_per_page", [(-10, 0), (-6, -144), (-10001, -9)]
)
def test_get_pagination_unknown_user_negative_value_negative_value(
    app, page_num, nbr_items_per_page
):
    """
    Test the function get_pagination_values with:
    - An unknown user as the current_user_mila_email parameter
    - The page_num argument presenting 0 or a negative integer as value
    - The nbr_items_per_page presenting 0 or a negative integer as value

    Parameters:
        app                                 The scope of our tests, used to set
                                            the context (to access MongoDB)
        page_num                            The page number to pass as argument
        nbr_items_per_page                  The number of elements to display per
                                            page, to pass as argument
    """
    # Define the current_user_mila_email to be tested
    unknown_user = "unknownuser"

    # Define the expected results
    # The number of elements to display per page we expect to retrieve in the
    # function's return
    expected_nbr_items_per_page = get_default_setting_value("nbr_items_per_page")
    # The number of skipped items we expect to retrieve in the function's return
    expected_nbr_of_skipped_items = 0

    # Use the app context
    with app.app_context():
        # Call the function with the input parameters
        (
            retrieved_nbr_of_skipped_items,
            retrieved_nbr_items_per_page,
        ) = get_pagination_values(unknown_user, page_num, nbr_items_per_page)

        # Assert the values we retrieve equal the values we expect
        assert retrieved_nbr_items_per_page == expected_nbr_items_per_page
        assert retrieved_nbr_of_skipped_items == expected_nbr_of_skipped_items


@pytest.mark.parametrize(
    "page_num,nbr_items_per_page", [(-6, 10), (0, 24), (-137, 200)]
)
def test_get_pagination_unknown_user_negative_value_positive_value(
    app, page_num, nbr_items_per_page
):
    """
    Test the function get_pagination_values with:
    - An unknown user as the current_user_mila_email parameter
    - The page_num argument presenting 0 or a negative integer as value
    - The nbr_items_per_page presenting a positive integer as value

    Parameters:
        app                                 The scope of our tests, used to set
                                            the context (to access MongoDB)
        page_num                            The page number to pass as argument
        nbr_items_per_page                  The number of elements to display per
                                            page, to pass as argument
    """
    # Define the current_user_mila_email to be tested
    unknown_user = "unknown"

    # Define the expected results
    # The number of elements to display per page we expect to retrieve in the
    # function's return
    expected_nbr_items_per_page = nbr_items_per_page
    # The number of skipped items we expect to retrieve in the function's return
    expected_nbr_of_skipped_items = 0

    # Use the app context
    with app.app_context():
        # Call the function with the input parameters
        (
            retrieved_nbr_of_skipped_items,
            retrieved_nbr_items_per_page,
        ) = get_pagination_values(unknown_user, page_num, nbr_items_per_page)

        # Assert the values we retrieve equal the values we expect
        assert retrieved_nbr_items_per_page == expected_nbr_items_per_page
        assert retrieved_nbr_of_skipped_items == expected_nbr_of_skipped_items


# When user is unknown and page_num a positive integer
@pytest.mark.parametrize(
    "page_num,nbr_items_per_page", [(1, True), (45, [1, 2, 3]), (19, (4, 5, 6))]
)
def test_get_pagination_unknown_user_positive_value_wrong_type(
    app, page_num, nbr_items_per_page
):
    """
    Test the function get_pagination_values with:
    - An unknown as the current_user_mila_email parameter
    - The page_num argument presenting a positive integer as value
    - The nbr_items_per_page presenting a type different from integer

    Parameters:
        app                                 The scope of our tests, used to set
                                            the context (to access MongoDB)
        page_num                            The page number to pass as argument
        nbr_items_per_page                  The number of elements to display per
                                            page, to pass as argument
    """
    # Define the current_user_mila_email to be tested
    unknown_user = "unknownuser"

    # Define the expected results
    # The number of elements to display per page we expect to retrieve in the
    # function's return
    expected_nbr_items_per_page = get_default_setting_value("nbr_items_per_page")
    # The number of skipped items we expect to retrieve in the function's return
    expected_nbr_of_skipped_items = (page_num - 1) * expected_nbr_items_per_page

    # Use the app context
    with app.app_context():
        # Call the function with the input parameters
        (
            retrieved_nbr_of_skipped_items,
            retrieved_nbr_items_per_page,
        ) = get_pagination_values(unknown_user, page_num, nbr_items_per_page)

        # Assert the values we retrieve equal the values we expect
        assert retrieved_nbr_items_per_page == expected_nbr_items_per_page
        assert retrieved_nbr_of_skipped_items == expected_nbr_of_skipped_items


@pytest.mark.parametrize("page_num,nbr_items_per_page", [(24, 0), (46, -70), (10, -5)])
def test_get_pagination_unknown_user_positive_value_negative_value(
    app, page_num, nbr_items_per_page
):
    """
    Test the function get_pagination_values with:
    - An unknown user as the current_user_mila_email parameter
    - The page_num argument presenting a positive integer as value
    - The nbr_items_per_page presenting 0 or a negative integer as value

    Parameters:
        app                                 The scope of our tests, used to set
                                            the context (to access MongoDB)
        page_num                            The page number to pass as argument
        nbr_items_per_page                  The number of elements to display per
                                            page, to pass as argument
    """
    # Define the current_user_mila_email to be tested
    unknown_user = "unknownuser"

    # Define the expected results
    # The number of elements to display per page we expect to retrieve in the
    # function's return
    expected_nbr_items_per_page = get_default_setting_value("nbr_items_per_page")
    # The number of skipped items we expect to retrieve in the function's return
    expected_nbr_of_skipped_items = (page_num - 1) * expected_nbr_items_per_page

    # Use the app context
    with app.app_context():
        # Call the function with the input parameters
        (
            retrieved_nbr_of_skipped_items,
            retrieved_nbr_items_per_page,
        ) = get_pagination_values(unknown_user, page_num, nbr_items_per_page)

        # Assert the values we retrieve equal the values we expect
        assert retrieved_nbr_items_per_page == expected_nbr_items_per_page
        assert retrieved_nbr_of_skipped_items == expected_nbr_of_skipped_items


@pytest.mark.parametrize("page_num,nbr_items_per_page", [(10, 33), (42, 6), (5, 5)])
def test_get_pagination_unknown_user_positive_value_positive_value(
    app, page_num, nbr_items_per_page
):
    """
    Test the function get_pagination_values with:
    - An unknown user as the current_user_mila_email parameter
    - The page_num argument presenting a positive integer as value
    - The nbr_items_per_page presenting a positive integer as value

    Parameters:
        app                                 The scope of our tests, used to set
                                            the context (to access MongoDB)
        page_num                            The page number to pass as argument
        nbr_items_per_page                  The number of elements to display per
                                            page, to pass as argument
    """
    # Define the current_user_mila_email to be tested
    unknown_user = "unknownuser"

    # Define the expected results
    # The number of elements to display per page we expect to retrieve in the
    # function's return
    expected_nbr_items_per_page = nbr_items_per_page
    # The number of skipped items we expect to retrieve in the function's return
    expected_nbr_of_skipped_items = (page_num - 1) * expected_nbr_items_per_page

    # Use the app context
    with app.app_context():
        # Call the function with the input parameters
        (
            retrieved_nbr_of_skipped_items,
            retrieved_nbr_items_per_page,
        ) = get_pagination_values(unknown_user, page_num, nbr_items_per_page)

        # Assert the values we retrieve equal the values we expect
        assert retrieved_nbr_items_per_page == expected_nbr_items_per_page
        assert retrieved_nbr_of_skipped_items == expected_nbr_of_skipped_items


# When user is known

# When user is known and page_num of wrong type
@pytest.mark.parametrize(
    "page_num,nbr_items_per_page",
    [("pifpafpouf", True), (None, [1, 2, 3]), ({}, (4, 5, 6))],
)
def test_get_pagination_known_user_wrong_type_wrong_type(
    app, known_user, page_num, nbr_items_per_page
):
    """
    Test the function get_pagination_values with:
    - A known user as the current_user_mila_email parameter
    - The page_num argument presenting a type different from integer
    - The nbr_items_per_page presenting a type different from integer

    Parameters:
        app                                 The scope of our tests, used to set
                                            the context (to access MongoDB)
        fake_data                           The data on which our tests are based
        page_num                            The page number to pass as argument
        nbr_items_per_page                  The number of elements to display per
                                            page, to pass as argument
    """
    known_user_email = known_user["mila_email_username"]

    # Set the preferred nbr_items_per_page of the user to a value different
    # from the default one
    new_nbr_items_per_page = 53
    set_items_per_page(known_user_email, new_nbr_items_per_page)

    # Assert that this value is different from the default one
    # (NB: for now, it seems obvious, but when we will centralize the default
    # value, it will make more sense)
    assert new_nbr_items_per_page != get_default_setting_value("nbr_items_per_page")

    # Define the expected results
    # The number of elements to display per page we expect to retrieve in the
    # function's return
    expected_nbr_items_per_page = new_nbr_items_per_page
    # The number of skipped items we expect to retrieve in the function's return
    expected_nbr_of_skipped_items = 0

    # Call the function with the input parameters
    (
        retrieved_nbr_of_skipped_items,
        retrieved_nbr_items_per_page,
    ) = get_pagination_values(known_user_email, page_num, nbr_items_per_page)

    # Assert the values we retrieve equal the values we expect
    assert retrieved_nbr_items_per_page == expected_nbr_items_per_page
    assert retrieved_nbr_of_skipped_items == expected_nbr_of_skipped_items


@pytest.mark.parametrize(
    "page_num,nbr_items_per_page", [("pifpafpouf", -34), (None, -6), ({}, 0)]
)
def test_get_pagination_known_user_wrong_type_negative_value(
    app, known_user, page_num, nbr_items_per_page
):
    """
    Test the function get_pagination_values with:
    - A known user as the current_user_mila_email parameter
    - The page_num argument presenting a type different from integer
    - The nbr_items_per_page presenting 0 or a negative integer as value

    Parameters:
        app                                 The scope of our tests, used to set
                                            the context (to access MongoDB)
        fake_data                           The data on which our tests are based
        page_num                            The page number to pass as argument
        nbr_items_per_page                  The number of elements to display per
                                            page, to pass as argument
    """
    known_user_email = known_user["mila_email_username"]

    # Set the preferred nbr_items_per_page of the user to a value different
    # from the default one
    new_nbr_items_per_page = 53
    set_items_per_page(known_user_email, new_nbr_items_per_page)

    # Assert that this value is different from the default one
    # (NB: for now, it seems obvious, but when we will centralize the default
    # value, it will make more sense)
    assert new_nbr_items_per_page != get_default_setting_value("nbr_items_per_page")

    # Define the expected results
    # The number of elements to display per page we expect to retrieve in the
    # function's return
    expected_nbr_items_per_page = new_nbr_items_per_page
    # The number of skipped items we expect to retrieve in the function's return
    expected_nbr_of_skipped_items = 0

    # Call the function with the input parameters
    (
        retrieved_nbr_of_skipped_items,
        retrieved_nbr_items_per_page,
    ) = get_pagination_values(known_user_email, page_num, nbr_items_per_page)

    # Assert the values we retrieve equal the values we expect
    assert retrieved_nbr_items_per_page == expected_nbr_items_per_page
    assert retrieved_nbr_of_skipped_items == expected_nbr_of_skipped_items


@pytest.mark.parametrize(
    "page_num,nbr_items_per_page", [(True, 5), ([1, 2, 3], 42), ((4, 5, 6), 117)]
)
def test_get_pagination_known_user_wrong_type_positive_value(
    app, known_user, page_num, nbr_items_per_page
):
    """
    Test the function get_pagination_values with:
    - A known user as the current_user_mila_email parameter
    - The page_num argument presenting a type different from integer
    - The nbr_items_per_page presenting a positive integer as value

    Parameters:
        app                                 The scope of our tests, used to set
                                            the context (to access MongoDB)
        fake_data                           The data on which our tests are based
        page_num                            The page number to pass as argument
        nbr_items_per_page                  The number of elements to display per
                                            page, to pass as argument
    """
    known_user_email = known_user["mila_email_username"]

    # Set the preferred nbr_items_per_page of the user to a value different
    # from the default one
    new_nbr_items_per_page = 53
    set_items_per_page(known_user_email, new_nbr_items_per_page)

    # Assert that this value is different from the default one
    # (NB: for now, it seems obvious, but when we will centralize the default
    # value, it will make more sense)
    assert new_nbr_items_per_page != get_default_setting_value("nbr_items_per_page")

    # Define the expected results
    # The number of elements to display per page we expect to retrieve in the
    # function's return
    expected_nbr_items_per_page = nbr_items_per_page
    # The number of skipped items we expect to retrieve in the function's return
    expected_nbr_of_skipped_items = 0

    # Call the function with the input parameters
    (
        retrieved_nbr_of_skipped_items,
        retrieved_nbr_items_per_page,
    ) = get_pagination_values(known_user_email, page_num, nbr_items_per_page)

    # Assert the values we retrieve equal the values we expect
    assert retrieved_nbr_items_per_page == expected_nbr_items_per_page
    assert retrieved_nbr_of_skipped_items == expected_nbr_of_skipped_items


# When user is known and page_num 0 or a negative integer
@pytest.mark.parametrize(
    "page_num,nbr_items_per_page", [(-66, True), (-578, [1, 2, 3]), (-1, (4, 5, 6))]
)
def test_get_pagination_known_user_negative_value_wrong_type(
    app, known_user, page_num, nbr_items_per_page
):
    """
    Test the function get_pagination_values with:
    - A known user as the current_user_mila_email parameter
    - The page_num argument presenting 0 or a negative integer as value
    - The nbr_items_per_page presenting a type different from integer

    Parameters:
        app                                 The scope of our tests, used to set
                                            the context (to access MongoDB)
        fake_data                           The data on which our tests are based
        page_num                            The page number to pass as argument
        nbr_items_per_page                  The number of elements to display per
                                            page, to pass as argument
    """
    known_user_email = known_user["mila_email_username"]

    # Set the preferred nbr_items_per_page of the user to a value different
    # from the default one
    new_nbr_items_per_page = 53
    set_items_per_page(known_user_email, new_nbr_items_per_page)

    # Assert that this value is different from the default one
    # (NB: for now, it seems obvious, but when we will centralize the default
    # value, it will make more sense)
    assert new_nbr_items_per_page != get_default_setting_value("nbr_items_per_page")

    # Define the expected results
    # The number of elements to display per page we expect to retrieve in the
    # function's return
    expected_nbr_items_per_page = new_nbr_items_per_page
    # The number of skipped items we expect to retrieve in the function's return
    expected_nbr_of_skipped_items = 0

    # Call the function with the input parameters
    (
        retrieved_nbr_of_skipped_items,
        retrieved_nbr_items_per_page,
    ) = get_pagination_values(known_user_email, page_num, nbr_items_per_page)

    # Assert the values we retrieve equal the values we expect
    assert retrieved_nbr_items_per_page == expected_nbr_items_per_page
    assert retrieved_nbr_of_skipped_items == expected_nbr_of_skipped_items


@pytest.mark.parametrize(
    "page_num,nbr_items_per_page", [(-10, 0), (-6, -144), (-10001, -9)]
)
def test_get_pagination_known_user_negative_value_negative_value(
    app, known_user, page_num, nbr_items_per_page
):
    """
    Test the function get_pagination_values with:
    - A known user as the current_user_mila_email parameter
    - The page_num argument presenting 0 or a negative integer as value
    - The nbr_items_per_page presenting 0 or a negative integer as value

    Parameters:
        app                                 The scope of our tests, used to set
                                            the context (to access MongoDB)
        fake_data                           The data on which our tests are based
        page_num                            The page number to pass as argument
        nbr_items_per_page                  The number of elements to display per
                                            page, to pass as argument
    """
    known_user_email = known_user["mila_email_username"]

    # Set the preferred nbr_items_per_page of the user to a value different
    # from the default one
    new_nbr_items_per_page = 53
    set_items_per_page(known_user_email, new_nbr_items_per_page)

    # Assert that this value is different from the default one
    # (NB: for now, it seems obvious, but when we will centralize the default
    # value, it will make more sense)
    assert new_nbr_items_per_page != get_default_setting_value("nbr_items_per_page")

    # Define the expected results
    # The number of elements to display per page we expect to retrieve in the
    # function's return
    expected_nbr_items_per_page = new_nbr_items_per_page
    # The number of skipped items we expect to retrieve in the function's return
    expected_nbr_of_skipped_items = 0

    # Call the function with the input parameters
    (
        retrieved_nbr_of_skipped_items,
        retrieved_nbr_items_per_page,
    ) = get_pagination_values(known_user_email, page_num, nbr_items_per_page)

    # Assert the values we retrieve equal the values we expect
    assert retrieved_nbr_items_per_page == expected_nbr_items_per_page
    assert retrieved_nbr_of_skipped_items == expected_nbr_of_skipped_items


@pytest.mark.parametrize(
    "page_num,nbr_items_per_page", [(-6, 10), (0, 24), (-137, 200)]
)
def test_get_pagination_known_user_negative_value_positive_value(
    app, known_user, page_num, nbr_items_per_page
):
    """
    Test the function get_pagination_values with:
    - A known user as the current_user_mila_email parameter
    - The page_num argument presenting 0 or a negative integer as value
    - The nbr_items_per_page presenting a positive integer as value

    Parameters:
        app                                 The scope of our tests, used to set
                                            the context (to access MongoDB)
        fake_data                           The data on which our tests are based
        page_num                            The page number to pass as argument
        nbr_items_per_page                  The number of elements to display per
                                            page, to pass as argument
    """
    known_user_email = known_user["mila_email_username"]

    # Set the preferred nbr_items_per_page of the user to a value different
    # from the default one
    new_nbr_items_per_page = 53
    set_items_per_page(known_user_email, new_nbr_items_per_page)

    # Assert that this value is different from the default one
    # (NB: for now, it seems obvious, but when we will centralize the default
    # value, it will make more sense)
    assert new_nbr_items_per_page != get_default_setting_value("nbr_items_per_page")

    # Define the expected results
    # The number of elements to display per page we expect to retrieve in the
    # function's return
    expected_nbr_items_per_page = nbr_items_per_page
    # The number of skipped items we expect to retrieve in the function's return
    expected_nbr_of_skipped_items = 0

    # Call the function with the input parameters
    (
        retrieved_nbr_of_skipped_items,
        retrieved_nbr_items_per_page,
    ) = get_pagination_values(known_user_email, page_num, nbr_items_per_page)

    # Assert the values we retrieve equal the values we expect
    assert retrieved_nbr_items_per_page == expected_nbr_items_per_page
    assert retrieved_nbr_of_skipped_items == expected_nbr_of_skipped_items


# When user is known and page_num a positive integer
@pytest.mark.parametrize(
    "page_num,nbr_items_per_page", [(1, True), (45, [1, 2, 3]), (19, (4, 5, 6))]
)
def test_get_pagination_known_user_positive_value_wrong_type(
    app, known_user, page_num, nbr_items_per_page
):
    """
    Test the function get_pagination_values with:
    - A known as the current_user_mila_email parameter
    - The page_num argument presenting a positive integer as value
    - The nbr_items_per_page presenting a type different from integer

    Parameters:
        app                                 The scope of our tests, used to set
                                            the context (to access MongoDB)
        fake_data                           The data on which our tests are based
        page_num                            The page number to pass as argument
        nbr_items_per_page                  The number of elements to display per
                                            page, to pass as argument
    """
    known_user_email = known_user["mila_email_username"]

    # Set the preferred nbr_items_per_page of the user to a value different
    # from the default one
    new_nbr_items_per_page = 53
    set_items_per_page(known_user_email, new_nbr_items_per_page)

    # Assert that this value is different from the default one
    # (NB: for now, it seems obvious, but when we will centralize the default
    # value, it will make more sense)
    assert new_nbr_items_per_page != get_default_setting_value("nbr_items_per_page")

    # Define the expected results
    # The number of elements to display per page we expect to retrieve in the
    # function's return
    expected_nbr_items_per_page = new_nbr_items_per_page
    # The number of skipped items we expect to retrieve in the function's return
    expected_nbr_of_skipped_items = (page_num - 1) * expected_nbr_items_per_page

    # Call the function with the input parameters
    (
        retrieved_nbr_of_skipped_items,
        retrieved_nbr_items_per_page,
    ) = get_pagination_values(known_user_email, page_num, nbr_items_per_page)

    # Assert the values we retrieve equal the values we expect
    assert retrieved_nbr_items_per_page == expected_nbr_items_per_page
    assert retrieved_nbr_of_skipped_items == expected_nbr_of_skipped_items


@pytest.mark.parametrize("page_num,nbr_items_per_page", [(24, 0), (46, -70), (10, -5)])
def test_get_pagination_known_user_positive_value_negative_value(
    app, known_user, page_num, nbr_items_per_page
):
    """
    Test the function get_pagination_values with:
    - A known user as the current_user_mila_email parameter
    - The page_num argument presenting a positive integer as value
    - The nbr_items_per_page presenting 0 or a negative integer as value

    Parameters:
        app                                 The scope of our tests, used to set
                                            the context (to access MongoDB)
        fake_data                           The data on which our tests are based
        page_num                            The page number to pass as argument
        nbr_items_per_page                  The number of elements to display per
                                            page, to pass as argument
    """
    known_user_email = known_user["mila_email_username"]

    # Set the preferred nbr_items_per_page of the user to a value different
    # from the default one
    new_nbr_items_per_page = 53
    set_items_per_page(known_user_email, new_nbr_items_per_page)

    # Assert that this value is different from the default one
    # (NB: for now, it seems obvious, but when we will centralize the default
    # value, it will make more sense)
    assert new_nbr_items_per_page != get_default_setting_value("nbr_items_per_page")

    # Define the expected results
    # The number of elements to display per page we expect to retrieve in the
    # function's return
    expected_nbr_items_per_page = new_nbr_items_per_page
    # The number of skipped items we expect to retrieve in the function's return
    expected_nbr_of_skipped_items = (page_num - 1) * expected_nbr_items_per_page

    # Call the function with the input parameters
    (
        retrieved_nbr_of_skipped_items,
        retrieved_nbr_items_per_page,
    ) = get_pagination_values(known_user_email, page_num, nbr_items_per_page)

    # Assert the values we retrieve equal the values we expect
    assert retrieved_nbr_items_per_page == expected_nbr_items_per_page
    assert retrieved_nbr_of_skipped_items == expected_nbr_of_skipped_items


@pytest.mark.parametrize("page_num,nbr_items_per_page", [(10, 33), (42, 6), (5, 5)])
def test_get_pagination_known_user_positive_value_positive_value(
    app, known_user, page_num, nbr_items_per_page
):
    """
    Test the function get_pagination_values with:
    - A known user as the current_user_mila_email parameter
    - The page_num argument presenting a positive integer as value
    - The nbr_items_per_page presenting a positive integer as value

    Parameters:
        app                                 The scope of our tests, used to set
                                            the context (to access MongoDB)
        fake_data                           The data on which our tests are based
        page_num                            The page number to pass as argument
        nbr_items_per_page                  The number of elements to display per
                                            page, to pass as argument
    """
    known_user_email = known_user["mila_email_username"]

    # Set the preferred nbr_items_per_page of the user to a value different
    # from the default one
    new_nbr_items_per_page = 53
    set_items_per_page(known_user_email, new_nbr_items_per_page)

    # Assert that this value is different from the default one
    # (NB: for now, it seems obvious, but when we will centralize the default
    # value, it will make more sense)
    assert new_nbr_items_per_page != get_default_setting_value("nbr_items_per_page")

    # Define the expected results
    # The number of elements to display per page we expect to retrieve in the
    # function's return
    expected_nbr_items_per_page = nbr_items_per_page
    # The number of skipped items we expect to retrieve in the function's return
    expected_nbr_of_skipped_items = (page_num - 1) * expected_nbr_items_per_page

    # Call the function with the input parameters
    (
        retrieved_nbr_of_skipped_items,
        retrieved_nbr_items_per_page,
    ) = get_pagination_values(known_user_email, page_num, nbr_items_per_page)

    # Assert the values we retrieve equal the values we expect
    assert retrieved_nbr_items_per_page == expected_nbr_items_per_page
    assert retrieved_nbr_of_skipped_items == expected_nbr_of_skipped_items
