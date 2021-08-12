from flask import request
from flask.json import jsonify
from .authentication import authenticate_with_header_basic

from clockwork_web.core.common import get_filter_from_request_args

from flask import Blueprint
flask_api = Blueprint('rest_jobs', __name__)

@flask_api.route('/jobs/list')
def route_api_v1_jobs_list():

    # filter = get_filter_from_request_args(["cluster_name", "user", "time"])

    D_user = authenticate_with_header_basic(request.headers.get("Authorization"))
    if D_user is None:
        return jsonify("Authorization error."), 401  # unauthorized

    return jsonify("Success. Now put something real here."), 200


#@flask_api.route('/jobs/one')
#def route_api_v1_jobs_one():
    # filter = get_filter_from_request_args(["cluster_name", "job_id"])