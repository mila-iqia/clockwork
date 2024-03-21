"""
This script is inspired from `store_fake_data_in_db.py` for same usage, i.e. with "dev.sh".
The difference is that here, we can call this script with parameters to control
how much data will be inserted in database. This allows to test database
when populated with a huge amount of data.
"""

import argparse
import sys

from clockwork_web.config import register_config
from slurm_state.mongo_client import get_mongo_client
from slurm_state.config import get_config

USERS = [
    {
        "mila_email_username": "student00@mila.quebec",
        "status": "enabled",
        "clockwork_api_key": "000aaa00",
        "mila_cluster_username": "milauser00",
        "cc_account_username": "ccuser00",
        "cc_account_update_key": None,
        "web_settings": {
            "nbr_items_per_page": 40,
            "dark_mode": False,
            "language": "en",
        },
    },
    {
        "mila_email_username": "student01@mila.quebec",
        "status": "enabled",
        "clockwork_api_key": "000aaa01",
        "mila_cluster_username": "milauser01",
        "cc_account_username": "ccuser01",
        "cc_account_update_key": None,
        "web_settings": {
            "nbr_items_per_page": 40,
            "dark_mode": False,
            "language": "fr",
        },
    },
    {
        "mila_email_username": "student02@mila.quebec",
        "status": "enabled",
        "clockwork_api_key": "000aaa02",
        "mila_cluster_username": "milauser02",
        "cc_account_username": "ccuser02",
        "cc_account_update_key": None,
        "web_settings": {
            "nbr_items_per_page": 40,
            "dark_mode": False,
            "language": "en",
        },
    },
    {
        "mila_email_username": "student03@mila.quebec",
        "status": "enabled",
        "clockwork_api_key": "000aaa03",
        "mila_cluster_username": "milauser03",
        "cc_account_username": "ccuser03",
        "cc_account_update_key": None,
        "web_settings": {
            "nbr_items_per_page": 40,
            "dark_mode": False,
            "language": "fr",
        },
    },
    {
        "mila_email_username": "student04@mila.quebec",
        "status": "enabled",
        "clockwork_api_key": "000aaa04",
        "mila_cluster_username": "milauser04",
        "cc_account_username": "ccuser04",
        "cc_account_update_key": None,
        "web_settings": {
            "nbr_items_per_page": 40,
            "dark_mode": False,
            "language": "en",
        },
    },
    {
        "mila_email_username": "student05@mila.quebec",
        "status": "enabled",
        "clockwork_api_key": "000aaa05",
        "mila_cluster_username": "milauser05",
        "cc_account_username": "ccuser05",
        "cc_account_update_key": None,
        "web_settings": {
            "nbr_items_per_page": 40,
            "dark_mode": False,
            "language": "fr",
        },
    },
    {
        "mila_email_username": "student06@mila.quebec",
        "status": "enabled",
        "clockwork_api_key": "000aaa06",
        "mila_cluster_username": "milauser06",
        "cc_account_username": None,
        "cc_account_update_key": None,
        "web_settings": {
            "nbr_items_per_page": 40,
            "dark_mode": False,
            "language": "en",
        },
    },
    {
        "mila_email_username": "student07@mila.quebec",
        "status": "enabled",
        "clockwork_api_key": "000aaa07",
        "mila_cluster_username": "milauser07",
        "cc_account_username": "ccuser07",
        "cc_account_update_key": None,
        "web_settings": {
            "nbr_items_per_page": 40,
            "dark_mode": False,
            "language": "fr",
        },
    },
    {
        "mila_email_username": "student08@mila.quebec",
        "status": "enabled",
        "clockwork_api_key": "000aaa08",
        "mila_cluster_username": "milauser08",
        "cc_account_username": "ccuser08",
        "cc_account_update_key": None,
        "web_settings": {
            "nbr_items_per_page": 40,
            "dark_mode": False,
            "language": "en",
        },
    },
    {
        "mila_email_username": "student09@mila.quebec",
        "status": "disabled",
        "clockwork_api_key": "000aaa09",
        "mila_cluster_username": "milauser09",
        "cc_account_username": "ccuser09",
        "cc_account_update_key": None,
        "web_settings": {
            "nbr_items_per_page": 40,
            "dark_mode": False,
            "language": "fr",
        },
    },
    {
        "mila_email_username": "student10@mila.quebec",
        "status": "enabled",
        "clockwork_api_key": "000aaa10",
        "mila_cluster_username": "milauser10",
        "cc_account_username": "ccuser10",
        "cc_account_update_key": None,
        "web_settings": {
            "nbr_items_per_page": 40,
            "dark_mode": False,
            "language": "en",
        },
    },
    {
        "mila_email_username": "student11@mila.quebec",
        "status": "enabled",
        "clockwork_api_key": "000aaa11",
        "mila_cluster_username": "milauser11",
        "cc_account_username": "ccuser11",
        "cc_account_update_key": None,
        "web_settings": {
            "nbr_items_per_page": 40,
            "dark_mode": False,
            "language": "fr",
        },
    },
    {
        "mila_email_username": "student12@mila.quebec",
        "status": "enabled",
        "clockwork_api_key": "000aaa12",
        "mila_cluster_username": "milauser12",
        "cc_account_username": "ccuser12",
        "cc_account_update_key": None,
        "web_settings": {
            "nbr_items_per_page": 40,
            "dark_mode": False,
            "language": "en",
        },
    },
    {
        "mila_email_username": "student13@mila.quebec",
        "status": "enabled",
        "clockwork_api_key": "000aaa13",
        "mila_cluster_username": "milauser13",
        "cc_account_username": "ccuser13",
        "cc_account_update_key": None,
        "web_settings": {
            "nbr_items_per_page": 40,
            "dark_mode": False,
            "language": "fr",
        },
    },
    {
        "mila_email_username": "student14@mila.quebec",
        "status": "enabled",
        "clockwork_api_key": "000aaa14",
        "mila_cluster_username": "milauser14",
        "cc_account_username": "ccuser14",
        "cc_account_update_key": None,
        "web_settings": {
            "nbr_items_per_page": 40,
            "dark_mode": False,
            "language": "en",
        },
    },
    {
        "mila_email_username": "student15@mila.quebec",
        "status": "enabled",
        "clockwork_api_key": "000aaa15",
        "mila_cluster_username": "milauser15",
        "cc_account_username": "ccuser15",
        "cc_account_update_key": None,
        "web_settings": {
            "nbr_items_per_page": 40,
            "dark_mode": False,
            "language": "fr",
        },
    },
    {
        "mila_email_username": "student16@mila.quebec",
        "status": "enabled",
        "clockwork_api_key": "000aaa16",
        "mila_cluster_username": "milauser16",
        "cc_account_username": "ccuser16",
        "cc_account_update_key": None,
        "web_settings": {
            "nbr_items_per_page": 40,
            "dark_mode": False,
            "language": "en",
        },
    },
    {
        "mila_email_username": "student17@mila.quebec",
        "status": "enabled",
        "clockwork_api_key": "000aaa17",
        "mila_cluster_username": "milauser17",
        "cc_account_username": "ccuser17",
        "cc_account_update_key": None,
        "web_settings": {
            "nbr_items_per_page": 40,
            "dark_mode": False,
            "language": "fr",
        },
    },
    {
        "mila_email_username": "student18@mila.quebec",
        "status": "enabled",
        "clockwork_api_key": "000aaa18",
        "mila_cluster_username": "milauser18",
        "cc_account_username": "ccuser18",
        "cc_account_update_key": None,
        "web_settings": {
            "nbr_items_per_page": 40,
            "dark_mode": False,
            "language": "en",
        },
    },
    {
        "mila_email_username": "student19@mila.quebec",
        "status": "disabled",
        "clockwork_api_key": "000aaa19",
        "mila_cluster_username": "milauser19",
        "cc_account_username": "ccuser19",
        "cc_account_update_key": None,
        "web_settings": {
            "nbr_items_per_page": 40,
            "dark_mode": False,
            "language": "fr",
        },
    },
]


DEFAULT_NB_JOBS = 1_000_000
DEFAULT_NB_DICTS = DEFAULT_NB_JOBS
DEFAULT_NB_PROPS_PER_DICT = 4


def _gen_new_job(job_id, slurm_username, mila_email_username):
    return {
        "slurm": {
            "account": "def-patate-rrg",
            "cluster_name": "beluga",
            "time_limit": 4320,
            "submit_time": 1681680327,
            "start_time": 0,
            "end_time": 0,
            "exit_code": "SUCCESS:0",
            "array_job_id": "0",
            "array_task_id": "None",
            "job_id": str(job_id),
            "name": f"job_name_{job_id}",
            "nodes": "None assigned",
            "partition": "other_fun_partition",
            "job_state": "PENDING",
            "tres_allocated": {},
            "tres_requested": {
                "num_cpus": 80,
                "mem": 95000,
                "num_nodes": 1,
                "billing": 80,
            },
            "username": slurm_username,
            "working_directory": "/a809/b333/c569",
        },
        "cw": {
            "mila_email_username": mila_email_username,
            "last_slurm_update": 1686248596.476063,
            "last_slurm_update_by_sacct": 1686248596.476063,
        },
        "user": {},
    }


def _generate_huge_fake_data(
    nb_jobs=DEFAULT_NB_JOBS,
    nb_student_jobs=None,
    nb_dicts=DEFAULT_NB_DICTS,
    nb_props_per_dict=DEFAULT_NB_PROPS_PER_DICT,
    props_username="student00@mila.quebec",
):
    student_to_nb_jobs = []
    if nb_student_jobs is not None:
        for desc in nb_student_jobs:
            student_name, str_nb_student_jobs = desc.split("=")
            nb_student_jobs = int(str_nb_student_jobs.strip())
            student_to_nb_jobs.append((student_name.strip(), nb_student_jobs))
    else:
        assert nb_jobs >= 0

    jobs = []

    # populate jobs
    if student_to_nb_jobs:
        user_map = {user["mila_email_username"]: user for user in USERS}
        assert len(user_map) == len(USERS)
        job_id = 0
        for student_name, nb_student_jobs in student_to_nb_jobs:
            student_email = f"{student_name}@mila.quebec"
            user = user_map[student_email]
            for i in range(nb_student_jobs):
                job_id += 1
                jobs.append(
                    _gen_new_job(
                        job_id, user["cc_account_username"], user["mila_email_username"]
                    )
                )
            print(f"Student {student_email}: {nb_student_jobs} jobs")
        assert job_id == len(jobs)
    else:
        for i in range(nb_jobs):
            # Pick a user
            user = USERS[i % len(USERS)]
            # Then create job
            job_id = i + 1
            jobs.append(
                _gen_new_job(
                    job_id, user["cc_account_username"], user["mila_email_username"]
                )
            )

    # populate job-user-dicts
    job_user_dicts = [
        {
            "mila_email_username": props_username,
            "job_id": i + 1,
            "cluster_name": "beluga",
            "props": {
                f"prop_{j + 1}_for_job_{i + 1}": f"I am user dict prop {j + 1} for job ID {i + 1}"
                for j in range(nb_props_per_dict)
            },
        }
        for i in range(nb_dicts)
    ]

    print(
        f"Jobs: {len(jobs)}, dicts: {len(job_user_dicts)}, props per dict: {nb_props_per_dict}"
    )
    return {"users": USERS, "jobs": jobs, "job_user_props": job_user_dicts}


def populate_fake_data(db_insertion_point, **kwargs):
    disable_index = kwargs.pop("disable_index", False)

    print("Generating huge fake data")
    E = _generate_huge_fake_data(**kwargs)
    print("Generated huge fake data")

    # Drop any collection (and related index) before.
    for k in ["users", "jobs", "nodes", "gpu", "job_user_props"]:
        db_insertion_point[k].drop()
        # This should verify we do not have collection indexes.
        assert not list(db_insertion_point[k].list_indexes())

    if not disable_index:
        print("Generate MongoDB index.")
        # Create indices. This isn't half as important as when we're
        # dealing with large quantities of data, but it's part of the
        # set up for the database.
        db_insertion_point["jobs"].create_index(
            [
                ("slurm.job_id", 1),
                ("slurm.cluster_name", 1),
                ("cw.mila_email_username", 1),
            ],
            name="job_id_and_cluster_name",
        )
        db_insertion_point["nodes"].create_index(
            [("slurm.name", 1), ("slurm.cluster_name", 1)],
            name="name_and_cluster_name",
        )
        db_insertion_point["users"].create_index(
            [("mila_email_username", 1)], name="users_email_index"
        )
        db_insertion_point["gpu"].create_index([("name", 1)], name="gpu_name")
        db_insertion_point["job_user_props"].create_index(
            [
                ("mila_email_username", 1),
                ("job_id", 1),
                ("cluster_name", 1),
            ],
            name="job_user_props_index",
        )

        # This should verify we do have collection indexes.
        for k in ["users", "jobs", "nodes", "gpu", "job_user_props"]:
            assert list(db_insertion_point[k].list_indexes())

    for k in ["users", "jobs", "nodes", "gpu", "job_user_props"]:
        # Anyway clean before inserting
        db_insertion_point[k].delete_many({})
        if k in E and E[k]:
            print(f"Inserting {k}, {len(E[k])} value(s)")
            db_insertion_point[k].insert_many(E[k])
            # Check count
            assert db_insertion_point[k].count_documents({}) == len(E[k])
            print("Inserted", k)


def store_data_in_db(**kwargs):
    # Open the database and insert the contents.
    client = get_mongo_client()
    populate_fake_data(client[get_config("mongo.database_name")], **kwargs)


def main(argv):
    # Retrieve the arguments passed to the script
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-j",
        "--nb-student-jobs",
        action="append",
        type=str,
        help=(
            "Number of job for a specific student, in format: <student>=<nb-jobs>. "
            "Accept multiple declarations. Example: -j student00=100 -j student05=1900"
        ),
    )
    group.add_argument(
        "--nb-jobs",
        type=int,
        default=DEFAULT_NB_JOBS,
        help="Number of jobs to add. May be 0 (no job added). Mutually exclusive with --nb-student-jobs.",
    )
    parser.add_argument(
        "--nb-dicts",
        type=int,
        default=DEFAULT_NB_DICTS,
        help="Number of job-user dicts to add. May be 0 (no job added).",
    )
    parser.add_argument(
        "--nb-props-per-dict",
        type=int,
        default=DEFAULT_NB_PROPS_PER_DICT,
        help=f"Number of key-value pairs in each job-user dict.",
    )
    parser.add_argument(
        "--props-username",
        type=str,
        default="student00@mila.quebec",
        help="Email of user who creates job-user dicts.",
    )
    parser.add_argument(
        "--disable-index",
        action="store_true",
        help="If specified, will not create MongoDB index.",
    )
    args = parser.parse_args(argv[1:])
    print(args)

    # Register the elements to access the database
    register_config("mongo.connection_string", "")
    register_config("mongo.database_name", "clockwork")

    # Store the generated fake data in the database
    store_data_in_db(
        nb_jobs=args.nb_jobs,
        nb_student_jobs=args.nb_student_jobs,
        nb_dicts=args.nb_dicts,
        nb_props_per_dict=args.nb_props_per_dict,
        props_username=args.props_username,
        disable_index=args.disable_index,
    )


if __name__ == "__main__":
    main(sys.argv)
