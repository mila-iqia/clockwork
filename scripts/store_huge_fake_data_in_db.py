"""
Variation du temps de requête en fonction du nombre de dictionnaires job-utilisateur
Pour un nombre de jobs fixes = n:
    0 à n dicts de 1 prop chacun
        --nb-dicts
    1 à k props pour chacun des n dicts
        --nb-props
Variation du temps de requête en fonction du nombre de jobs dans la DB
    Avec 0 dicts: 0 à n jobs
        --nb-jobs
    Avec n dicts de k props: 0 à n jobs
        --nb-jobs

n = 19
--nb-jobs: 0 à n => 2 ** 0 à 2 ** n
--nb-dicts: 0 à n => 2 ** 0 à 2 ** n
--nb-props: 1 à k

Paramètres:
--nb-jobs   --nb-dicts  --nb-props-per-dict
n           0           1
n           ...         1
n           n           1
n           n           ...
n           n           k

0           0           1
...         0           1
n           0           1
------------VS-----------
0           n           k
...         n           k
n           n           k
"""

import argparse
import sys
from datetime import datetime

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
BASE_JOB_SLURM = {
    "account": "def-patate-rrg",
    "cluster_name": "beluga",
    "time_limit": 4320,
    "submit_time": 1681680327,
    "start_time": 0,
    "end_time": 0,
    "exit_code": "SUCCESS:0",
    "array_job_id": "0",
    "array_task_id": "None",
    "job_id": "197775",
    "name": "somejobname_507716",
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
    "username": "ccuser02",
    "working_directory": "/a809/b333/c569",
}
BASE_JOB_CW = {
    "mila_email_username": "student02@mila.quebec",
    "last_slurm_update": 1686248596.476063,
    "last_slurm_update_by_sacct": 1686248596.476063,
}


DEFAULT_NB_JOBS = 1_000_000
DEFAULT_NB_DICTS = DEFAULT_NB_JOBS
DEFAULT_NB_PROPS_PER_DICT = 4


def _generate_huge_fake_data(
    nb_jobs=DEFAULT_NB_JOBS,
    nb_dicts=DEFAULT_NB_DICTS,
    nb_props_per_dict=DEFAULT_NB_PROPS_PER_DICT,
):
    jobs = []
    job_user_dicts = []

    # populate jobs
    for i in range(nb_jobs):
        user = USERS[i % len(USERS)]
        job_id = i + 1
        job_slurm = BASE_JOB_SLURM.copy()
        job_cw = BASE_JOB_CW.copy()
        # edit slurm.job_id
        job_slurm["job_id"] = str(job_id)
        # edit slurm.name
        job_slurm["name"] = f"job_name_{job_id}"
        # edit slurm.username
        job_slurm["username"] = user["cc_account_username"]
        # edit cw.mila_email_username
        job_cw["mila_email_username"] = user["mila_email_username"]
        jobs.append({"slurm": job_slurm, "cw": job_cw, "user": {}})

    # populate job-user-dicts
    for i in range(nb_dicts):
        user_job_dict = {
            "user_id": "student00@mila.quebec",
            "job_id": i + 1,
            "cluster_name": "beluga",
            "labels": {
                f"prop_{j + 1}_for_job_{i + 1}": f"I am user dict prop {j + 1} for job ID {i + 1}"
                for j in range(nb_props_per_dict)
            },
        }
        job_user_dicts.append(user_job_dict)

    print(
        f"Jobs: {len(jobs)}, dicts: {len(job_user_dicts)}, props per dict: {nb_props_per_dict}"
    )
    return {"users": USERS, "jobs": jobs, "labels": job_user_dicts}


def populate_fake_data(db_insertion_point, **kwargs):
    print("Generating huge fake data")
    E = _generate_huge_fake_data(**kwargs)
    print("Generated huge fake data")

    # Create indices. This isn't half as important as when we're
    # dealing with large quantities of data, but it's part of the
    # set up for the database.
    db_insertion_point["jobs"].create_index(
        [("slurm.job_id", 1), ("slurm.cluster_name", 1)],
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
    db_insertion_point["labels"].create_index(
        [("user_id", 1), ("job_id", 1), ("cluster_name", 1), ("labels", 1)],
        name="job_label_index",
    )

    for k in ["users", "jobs", "nodes", "gpu", "labels"]:
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
    parser.add_argument(
        "--nb-jobs",
        type=int,
        default=DEFAULT_NB_JOBS,
        help="Number of jobs to add. May be 0 (no job added).",
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
    args = parser.parse_args(argv[1:])
    print(args)

    # Register the elements to access the database
    register_config("mongo.connection_string", "")
    register_config("mongo.database_name", "clockwork")

    # Store the generated fake data in the database
    store_data_in_db(
        nb_jobs=args.nb_jobs,
        nb_dicts=args.nb_dicts,
        nb_props_per_dict=args.nb_props_per_dict,
    )


if __name__ == "__main__":
    main(sys.argv)
