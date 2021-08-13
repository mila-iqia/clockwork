
import re

from flask import request, make_response
from flask.json import jsonify
from .authentication import authenticate_with_header_basic

from clockwork_web.core.common import get_filter_from_request_args
from clockwork_web.core.jobs_helper import (strip_artificial_fields_from_job,
    get_mongodb_filter_from_query_filter,
    get_jobs,
    infer_best_guess_for_username)


from flask import Blueprint
flask_api = Blueprint('rest_jobs', __name__)


@flask_api.route('/jobs/list')
def route_api_v1_jobs_list():

    D_user = authenticate_with_header_basic(request.headers.get("Authorization"))
    if D_user is None:
        return jsonify("Authorization error."), 401  # unauthorized


    filter = get_filter_from_request_args(["cluster_name", "user", "time"])
    if 'user' in filter:
        filter['user'] = filter['user'].replace(" ", "")
    if 'time' in filter:
        try:
            filter['time'] = int(filter['time'])
        except:
            return jsonify(f"Field 'time' cannot be cast as a valid integer: {filter['time']}."), 400  # bad request

    LD_jobs = get_jobs(mongodb_filter=get_mongodb_filter_from_query_filter(filter))

    LD_jobs = [infer_best_guess_for_username(strip_artificial_fields_from_job(D_job))
                 for D_job in LD_jobs]

    return jsonify(LD_jobs)


@flask_api.route('/jobs/one')
def route_api_v1_jobs_one():

    D_user = authenticate_with_header_basic(request.headers.get("Authorization"))
    if D_user is None:
        return jsonify("Authorization error."), 401  # unauthorized


    filter = get_filter_from_request_args(["cluster_name", "job_id"])
    if "job_id" in filter:
        # There's this annoying thing by which many of the job_id are integers in the database,
        # but then some of them are these weird slurm batch identifiers, and then we can't cast
        # them as integers. Let's just add a conversion here when it's all digits, and leave it
        # as it is when there are non-digits characters.
        if re.match(r"^(\d*)$", filter["job_id"]):
            filter["job_id"] = int(filter["job_id"])
    else:
        return jsonify("Missing argument job_id."), 400  # bad request


    LD_jobs = get_jobs(filter)

    if len(LD_jobs) == 0:
        # Not a great when missing the value we want, but it's an acceptable answer.
        return jsonify({}), 200
    if len(LD_jobs) > 1:
        # This is not a situation that should even happen, and it's a sign of data corruption.
        resp = jsonify(f"Found {len(LD_jobs)} jobs with job_id {filter['job_id']}. Not sure what to do about these cases.")
        resp.status_code = 500  # server error
        return resp

    D_job = strip_artificial_fields_from_job(LD_jobs[0])
    D_job = infer_best_guess_for_username(D_job)

    return jsonify(D_job)
    # resp.status_code = 200  # success
    # return resp