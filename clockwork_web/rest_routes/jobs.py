from flask import request
from flask.json import jsonify
from .authentication import authenticate_with_header_basic

from flask import Blueprint
flask_api = Blueprint('rest_jobs', __name__)

@flask_api.route('/jobs/list')
def route_api_v1_jobs_list():

    D_user = authenticate_with_header_basic(request.headers.get("Authorization"))
    if D_user is None:
        return jsonify("Authorization error."), 401  # unauthorized

    return jsonify("Success. Now put something real here."), 200