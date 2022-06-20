"""
Functions to unify the pagination process for the nodes and jobs.
"""

from clockwork_web.core.users_helper import get_nbr_items_per_page


def get_pagination_values(current_user_mila_email, page_num, nbr_items_per_page):
    """
    Add pagination filter to preexisting filters, regarding the parameters
    provided in the request, or the current user's settings.

    Parameters:
        current_user_mila_email   Current user mila email. Its settings are used
                                  if page_num or nbr_items_per_page is missing.
        page_num                  Number of the current page. This number is the one
                                  provided in the request. If it is None or invalid,
                                  the first page is considered.
        nbr_items_per_page        Number of items to displayed per page; this number
                                  is the one provided in the request. If it is None
                                  or invalid, the value stored in the current user's
                                  settings is used.

    Returns:
        A tuple corresponding to the pagination parameters. It presents the following
        format: (number_of_skipped_items, nbr_items_per_page).
        For instance, the tuple (50, 10) indicates that the items to return are
        the items from the 51st to the 60th of the list.
    """
    # Set the value of page_num
    if page_num:
        if not (type(page_num) == int and page_num > 0):
            # If the provided page_num is a strictly positive integer, it is kept
            # Otherwise (such as it is the case here), it is set to 1
            page_num = 1
    else:
        # If no page number has been provided, we considered the first page
        page_num = 1

    # Set the value of nbr_items_per_page
    if nbr_items_per_page:
        if not (type(nbr_items_per_page) == int and nbr_items_per_page > 0):
            # If the provided nbr_items_per_page is a stricly positive integer,
            # it is kept. Otherwise (such as it is the case here), the users
            # helper is called in order to retrieve the default value related
            # to this user
            nbr_items_per_page = get_nbr_items_per_page(current_user_mila_email)

    else:
        # If no nbr_items_per_page has been provided, we use the value which is
        # stored in the user's settings by calling the users helper
        nbr_items_per_page = get_nbr_items_per_page(current_user_mila_email)

    # Return the pagination tuple
    number_of_skipped_items = nbr_items_per_page * (page_num - 1)
    return (number_of_skipped_items, nbr_items_per_page)
