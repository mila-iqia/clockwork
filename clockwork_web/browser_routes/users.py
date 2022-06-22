from flask import Blueprint, request, render_template
from flask_login import current_user, login_required

flask_api = Blueprint("users", __name__)

import random  # TODO: This is a temporary import

from clockwork_web.core.users_helper import get_user_by_single_username


@flask_api.route("/one")
@login_required
def route_one():
    """
    Takes "username" as a mandatory argument.

    Returns a page displaying the User information if a username is
    specified.
    Returns an error message otherwise. The potential returned error
    is:
        - 400 ("Bad Request") if the username is missing.

    .. :quickref: display the information of one user as formatted HTML
    """
    username = request.args.get("username", None)
    if username is None:
        return (
            render_template("error.html", error_msg=f"Missing argument username."),
            400,  # Bad Request
        )

    # Retrieve the user information
    D_user = get_user_by_single_username(username)

    if D_user is not None:
        return render_template(
            "single_user.html",
            username=username,
            user=D_user,
            mila_email_username=current_user.mila_email_username,
            picture_name="user{}".format(
                random.randint(0, 2)
            ),  # TODO: This is a temporary addition in order to user several images
        )
    else:
        return (
            render_template(
                "error.html", error_msg=f"The requested user has not been found."
            ),
            400,  # Bad Request
        )
