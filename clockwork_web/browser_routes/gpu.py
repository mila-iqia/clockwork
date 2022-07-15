from flask import Blueprint, Markup, render_template, request
from flask.json import jsonify

from flask_login import current_user, login_required
from flask_babel import gettext
from clockwork_web.core.gpu_helper import get_gpu_info, get_gpu_list


flask_api = Blueprint("gpu", __name__)


@flask_api.route("/list")
@login_required
def route_list():
    """
    Get a list of the GPUs.

    Takes no argument.

    Returns a list of dictionaries describing the GPUs listed in the database.

    .. :quickref: list all the GPU as formatted HTML
    """
    LD_gpus = get_gpu_list()

    return render_template(
        "gpu.html",
        LD_gpus=LD_gpus,
        mila_email_username=current_user.mila_email_username,
    )


@flask_api.route("/one")
@login_required
def route_one():
    """
    Takes "gpu_name" as a mandatory argument.

    Returns a page displaying the GPU information if a gpu_name is
    specified, and a page with a message presenting the lack of information if the
    provided gpu_name has not been found in the database.
    Returns an error message otherwise. The potential returned error
    is:
        - 400 ("Bad Request") if the gpu_name is missing.

    .. :quickref: display the information of one GPU as formatted HTML
    """
    gpu_name = request.args.get("gpu_name", None)
    if gpu_name is None:
        return (
            render_template(
                "error.html", error_msg=gettext("Missing argument gpu_name.")
            ),
            400,  # Bad Request
        )

    # Retrieve the GPU information
    D_gpu = get_gpu_info(gpu_name)
    # Need to format it as list of tuples for the template
    LP_gpu = list(sorted(D_gpu.items(), key=lambda e: e[0]))
    return render_template(
        "single_gpu.html",
        LP_gpu=LP_gpu,
        gpu_name=gpu_name,
        mila_email_username=current_user.mila_email_username,
    )
