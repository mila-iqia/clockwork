import re
import time

from flask import request, make_response
from flask.json import jsonify
from .authentication import authentication_required

from clockwork_web.core.jobs_helper import (
    get_filter_user,
    get_filter_after_end_time,
    get_filter_cluster_name,
    get_filter_job_id,
    combine_all_mongodb_filters,
    strip_artificial_fields_from_job,
    get_jobs,
    infer_best_guess_for_username,
)


from flask import Blueprint

flask_api = Blueprint("rest_jobs", __name__)


@flask_api.route("/jobs/list")
@authentication_required
def route_api_v1_jobs_list():
    """

    .. :quickref: list all Slurm jobs
    """
    f0 = get_filter_user(request.args.get("user", None))

    time1 = request.args.get("relative_time", None)
    if time1 is None:
        f1 = {}
    else:
        try:
            time1 = float(time1)
            f1 = get_filter_after_end_time(end_time=time.time() - time1)
        except Exception as inst:
            print(inst)
            return (
                jsonify(
                    f"Field 'relative_time' cannot be cast as a valid float: {time1}."
                ),
                400,
            )  # bad request

    f2 = get_filter_cluster_name(request.args.get("cluster_name", None))

    filter = combine_all_mongodb_filters(f0, f1, f2)
    LD_jobs = get_jobs(filter)

    # TODO : Potential redesign. See CW-81.
    LD_jobs = [
        infer_best_guess_for_username(strip_artificial_fields_from_job(D_job))
        for D_job in LD_jobs
    ]

    return jsonify(LD_jobs)


@flask_api.route("/jobs/one")
@authentication_required
def route_api_v1_jobs_one():
    """

    .. :quickref: list one Slurm job
    """
    job_id = request.args.get("job_id", None)
    if job_id is None:
        return jsonify("Missing argument job_id."), 400  # bad request
    f0 = get_filter_job_id(job_id)
    f1 = get_filter_cluster_name(request.args.get("cluster_name", None))
    filter = combine_all_mongodb_filters(f0, f1)

    LD_jobs = get_jobs(filter)

    if len(LD_jobs) == 0:
        # Not a great when missing the value we want, but it's an acceptable answer.
        return jsonify({}), 200
    if len(LD_jobs) > 1:
        # This is not a situation that should even happen, and it's a sign of data corruption.
        resp = jsonify(
            f"Found {len(LD_jobs)} jobs with job_id {filter['job_id']}. Not sure what to do about these cases."
        )
        resp.status_code = 500  # server error
        return resp

    # TODO : Potential redesign. See CW-81.
    D_job = strip_artificial_fields_from_job(LD_jobs[0])
    D_job = infer_best_guess_for_username(D_job)

    return jsonify(D_job)
