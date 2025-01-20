"""
Insert elements extracted from the Slurm reports into the database.
"""

import copy, json, logging, os, time
from pymongo import InsertOne, ReplaceOne, UpdateOne


from slurm_state.helpers.gpu_helper import get_cw_gres_description
from slurm_state.helpers.clusters_helper import get_all_clusters

# Import parser classes
from slurm_state.parsers.job_parser import JobParser
from slurm_state.parsers.node_parser import NodeParser
from slurm_state.parsers.entity_parser import IdentityParser


def pprint_bulk_result(result):
    if "upserted" in result.bulk_api_result:
        # too long and not necessary
        del result.bulk_api_result["upserted"]
    print(result.bulk_api_result)


def fetch_slurm_report(parser, report_path):
    """
    Yields elements ready to be slotted into the "slurm" field,
    but they have to be processed further before committing to MongoDB.
    """
    # Retrieve the cluster name
    cluster_name = parser.cluster["name"]

    assert os.path.exists(report_path), f"The report path {report_path} is missing."

    ctx = get_all_clusters().get(cluster_name, None)
    assert ctx is not None, f"{cluster_name} not configured"

    with open(report_path, "r") as f:
        try:
            for e in parser.parser(f):
                e["cluster_name"] = cluster_name
                yield e
        except Exception as err:
            logging.warning(str(err))


def slurm_job_to_clockwork_job(slurm_job: dict):
    """
    Takes the components returned from the slurm reports,
    and turns it into a dict with 2 subcomponents.
    That can later be committed to mongodb in the format
    that clockwork expects.
    """
    clockwork_job = {
        "slurm": slurm_job,
        "cw": {
            "mila_email_username": None,
        },
    }
    return clockwork_job


def slurm_node_to_clockwork_node(slurm_node: dict):
    """
    Similar to slurm_job_to_clockwork_job,
    but without the "user" field and without a need
    to infer user accounts (because nodes don't belong
    to specific users).
    We still add the "cw" field for our own uses.
    """

    # If GPU information are available on the node
    if (
        all(key in slurm_node for key in ["gres", "features"])
        and slurm_node["gres"] is not None
    ):
        # Parse the GPU data and add it to the "cw" field
        gpu_data = get_cw_gres_description(slurm_node["gres"], slurm_node["features"])

        # Set up the node dictionary as used in Clockwork
        clockwork_node = {
            "slurm": slurm_node,
            "cw": {"gpu": gpu_data},
        }
    # Otherwise
    else:
        clockwork_node = {
            "slurm": slurm_node,
            "cw": {"gpu": {}},
        }

    return clockwork_node


def lookup_user_account(users_collection):
    """
    Mutates the argument in order to fill in the
    field for "cw" pertaining to the user account.
    Returns the mutated value to facilitate a `map` call.
    """

    def _lookup_user_account(clockwork_job: dict[dict]):
        cluster_name = clockwork_job["slurm"]["cluster_name"]
        cluster_username = clockwork_job["slurm"]["username"]

        account_field = get_all_clusters()[cluster_name]["account_field"]
        result = users_collection.find_one({account_field: cluster_username})
        if result is not None:
            clockwork_job["cw"]["mila_email_username"] = result["mila_email_username"]

        return clockwork_job

    return _lookup_user_account


def main_read_report_and_update_collection(
    entity,
    collection,
    users_collection,
    cluster_name,
    report_file_path,
    from_file=None,
    want_commit_to_db=True,
    dump_file="",
):
    """
    Create a Clockwork jobs or nodes list from a sacct report file and store it into
    the database and/or a dump file, according to what is requested by the parameters.

    Parameters:
        entity              String which could be "jobs" or "nodes": define which entity we are handling
        collection          Collection of the jobs or nodes in the database
        users_collection    Collection of the users in the database, required when jobs are retrieved. Could be None for nodes
        cluster_name        Name of the cluster we are working on
        report_file_path    Path to the report from which the jobs or nodes information is extracted. This report is generated through
                            the command sacct for the jobs, or sinfo for the nodes. If None, a new report is generated.
        from_file           Value contained in ["cw", "slurm", None] indicating whether the jobs or nodes are extracted from a Slurm file, a CW file (ie JSON file presenting a list of the entities formatted as used in Clockwork) or from no file. If "cw" or "slurm", the input file
                            is report_file_path. If None, the file is generated at the report_file_path path.
        want_commit_to_db   Boolean indicating whether or not the jobs or nodes are stored in the database. Default is True
        dump_file           String containing the path to the file in which we want to dump the data. Default is "", which means nothing is stored in an output file
    """
    # Initialize the time of this operation's beginning
    timestamp_start = time.time()

    # Retrieve clusters data from the configuration file
    clusters = get_all_clusters()
    assert cluster_name in clusters

    # Retrieve Slurm version
    # If a data file has been set as input, the Slurm version should
    # be stored in it, else the parser will try to get the version
    # through an SSH command
    # Initialize the parser version
    parser_version = None
    if from_file:
        with open(report_file_path, "r") as infile:
            infile_data = json.load(infile)

            if from_file == "slurm":
                if "Slurm" in infile_data["meta"]:
                    version = infile_data["meta"]["Slurm"]["version"]
                elif "slurm" in infile_data["meta"]:
                    version = infile_data["meta"]["slurm"]["version"]
                else:
                    raise Exception(f'"Slurm" or "slurm" not found in data["meta"] for file {report_file_path}')
                parser_version = f"{version['major']}.{version['micro']}.{version['minor']}"

    # Check the input parameters
    assert entity in ["jobs", "nodes"]

    if entity == "jobs":
        id_key = (
            "job_id"  # The id_key is used to determine how to retrieve the ID of a job
        )
        parser = JobParser(
            cluster_name=cluster_name, slurm_version=parser_version
        )  # This parser is used to retrieve and format useful information from a sacct job
        from_slurm_to_clockwork = slurm_job_to_clockwork_job  # This function is used to translate a Slurm job (created through the parser) to a Clockwork job
    
    elif entity == "nodes":
        if from_file in ["slurm", None]:
            id_key = (
                "name"  # The id_key is used to determine how to retrieve the ID of a node
            )
            parser = NodeParser(
                cluster_name=cluster_name, slurm_version=parser_version
            )  # This parser is used to retrieve and format useful information from a sacct node
            from_slurm_to_clockwork = slurm_node_to_clockwork_node  # This function is used to translate a Slurm node (created through the parser) to a Clockwork node
        elif from_file == "cw":
            parser = IdentityParser(entity=entity, cluster_name=cluster_name)
            from_slurm_to_clockwork = lambda x: x
    
    else:
        # Raise an error because it should not happen
        raise ValueError(
            f'Incorrect value for entity in main_read_sacct_and_update_collection: "{entity}" when it should be "jobs" or "nodes".'
        )

    ## Retrieve entities ##

    # Generate a report file if required
    if not from_file or not os.path.exists(report_file_path):
        print(
            f"Generate report file for the {cluster_name} cluster at location {report_file_path}."
        )
        parser.generate_report(report_file_path)

    # Construct an iterator over the list of entities in the report file,
    # each one of them is turned into a clockwork job or node, according to applicability
    I_clockwork_entities_from_report = map(
        from_slurm_to_clockwork,
        fetch_slurm_report(parser, report_file_path),
    )

    L_updates_to_do = []  # Entity updates to store in the database if requested
    L_users_updates = []  # Users updates to store in the database if requested
    L_data_for_dump_file = []  # Data to store in the dump file if requested

    if entity == "jobs":
        (
            L_updates_to_do,
            L_users_updates,
            L_data_for_dump_file,
        ) = get_jobs_updates_and_insertions(
            I_clockwork_entities_from_report, cluster_name, collection, users_collection
        )
    elif entity == "nodes":
        (L_updates_to_do, L_data_for_dump_file) = get_nodes_updates(
            I_clockwork_entities_from_report
        )

    # Commit new elements and changes to the database, if requested
    if want_commit_to_db:
        # Store the jobs or nodes
        if L_updates_to_do:
            assert collection is not None
            print(f"{entity}: collection.bulk_write(L_updates_to_do)")
            result = collection.bulk_write(L_updates_to_do)
            pprint_bulk_result(result)
        else:
            print(
                f"Empty list found for updates to {entity} collection."
                "This is unexpected and might be the sign of a problem."
            )

        # Update the users associating their account
        if L_users_updates:
            print("users_collection.bulk_write(L_user_updates, upsert=False)")
            result = users_collection.bulk_write(
                L_users_updates,
                upsert=False,  # this should never create new users.
            )
            pprint_bulk_result(result)

        # Display the time taken for this import
        mongo_update_duration = time.time() - timestamp_start
        print(
            f"Bulk write for {len(L_updates_to_do)} {entity} entries in mongodb took {mongo_update_duration} seconds."
        )

    # Dump the JSON data in a given output file, if requested
    if dump_file:
        with open(dump_file, "w") as f:
            json.dump(L_data_for_dump_file, f, indent=4)
        print(f"Wrote {entity} to dump_file {dump_file}.")


def get_jobs_updates_and_insertions(
    I_clockwork_jobs, cluster_name, jobs_collection, users_collection
):
    """
    Retrieve lists of database operations (InsertOne, ReplaceOne and UpdateOne, from pymongo) summarizing the updates
    to be done on jobs and users in the database, and data to store in the dump file.

    Parameters:
        I_clockwork_jobs    Iterator on Clockwork jobs we want to insert or update in the database
        cluster_name        Name of the cluster on which we are working
        jobs_collection     Collection of the jobs in the database
        users_collection    Collection of the users in the database

    Returns:
        A 3-tuple containing (in this order) the following elements:
            - A list of the database operations (InsertOne and ReplaceOne, from pymongo) summarizing the
              updates to be done into the database for the jobs
            - A list of the database operations (UpdateOne, from pymongo) summarizing the updates to be
              done into the database for the users
            - A list of the elements to store in the dump file
    """

    L_updates_to_do = []  # Initialize the list of elements to update
    L_data_for_dump_file = (
        []
    )  # Initialize the list of elements to store into the dump file

    ## Retrieve MongoDB entities ##

    # Retrieve the entities already stored in MongoDB for this cluster
    LD_currently_in_mongodb = list(
        jobs_collection.find({"slurm.cluster_name": cluster_name})
    )

    # Index these entities by id in order to have a O(1) lookup
    # when matching entities stored in MongoDB and in the sacct file
    DD_currently_in_mongodb = dict(
        (D_entity["slurm"]["job_id"], D_entity) for D_entity in LD_currently_in_mongodb
    )

    ## Retrieve sacct entities ##

    # Apply the function lookup_user_account to each element, which are then gathered in a list
    # (We previously added a filter in order to keep only the Mila related jobs, but this is now
    # done while retrieving these jobs)
    LD_sacct = list(
        map(
            lookup_user_account(users_collection),
            I_clockwork_jobs,
        )
    )

    # Index the jobs by ID
    DD_sacct = dict((D_job["slurm"]["job_id"], D_job) for D_job in LD_sacct)

    ## Identify the elements to insert and the ones to updates ##

    # Identify the element to insert (ie the new element, which have not been stored
    # in the database yet)
    S_ids_to_insert = set(DD_sacct.keys()) - set(DD_currently_in_mongodb.keys())

    # Identify the element to update (ie the element contained in the sacct report
    # which have previously been stored in the database)
    S_ids_to_update = set(DD_sacct.keys()).intersection(
        set(DD_currently_in_mongodb.keys())
    )

    # Make some check on data consistency:
    # The way we partitioned those job_id, they cannot be in two of those sets.
    # Note that many job_id for old jobs are not going to be found in any of those sets
    # because they simply do not require exceptional handling by sacct.
    assert S_ids_to_insert.isdisjoint(S_ids_to_update)

    # -- Insertion --
    for job_id in S_ids_to_insert:
        D_job_sc = DD_sacct[job_id]
        # Copy it because it's a bit ugly to start modifying things in place.
        # This can lead to strange interactions with the operations that
        # we want to do with sacct. Might as well keep it clean here.
        D_job_new = copy.copy(D_job_sc)
        # add this field all the time, whenever you touch an entry
        now = time.time()
        D_job_new["cw"]["last_slurm_update"] = now
        D_job_new["cw"]["last_slurm_update_by_sacct"] = now
        # No need to the empty user dict because it's done earlier
        # by `slurm_job_to_clockwork_job`.

        # Save the operation to do in the database
        L_updates_to_do.append(InsertOne(D_job_new))
        # Save the data to store in the dump file (just omit the "_id" part of the job)
        L_data_for_dump_file.append(
            {k: D_job_new[k] for k in D_job_new.keys() if k != "_id"}
        )

    # -- Update --
    for job_id in S_ids_to_update:
        # Retrieve the two versions of the job
        D_job_db = DD_currently_in_mongodb[
            job_id
        ]  # The job as it is currently stored in the database
        D_job_sacct = DD_sacct[
            job_id
        ]  # The data of the job parsed from the sacct report

        # Check if their clusters match
        assert D_job_db["slurm"]["cluster_name"] == cluster_name
        assert D_job_sacct["slurm"]["cluster_name"] == cluster_name

        # Note that D_job_db has a "_id" which is useful for an update,
        # and it also contains a "user" dict which might have values in it,
        # which is a thing that D_job_sc wouldn't have.

        D_job_new = {}
        for k in ["cw", "slurm"]:
            D_job_new[k] = D_job_db.get(k, {}) | D_job_sacct.get(k, {})
        # Add these field each time an entry is updated
        now = time.time()
        D_job_new["cw"]["last_slurm_update"] = now
        D_job_new["cw"]["last_slurm_update_by_sacct"] = now

        L_updates_to_do.append(
            ReplaceOne({"_id": D_job_db["_id"]}, D_job_new, upsert=False)
        )

        # Save the data to store in the dump file (just omit the "_id" part of the job)
        L_data_for_dump_file.append(
            {k: D_job_new[k] for k in D_job_new.keys() if k != "_id"}
        )

    # -- Account association -- #
    # L_users_updates = associate_account(LD_sacct)

    # return (L_updates_to_do, L_users_updates, L_data_for_dump_file)
    return (L_updates_to_do, [], L_data_for_dump_file)


def get_nodes_updates(I_clockwork_nodes):
    """
    Retrieve a list of database operations (UpdateOne, from pymongo) summarizing
    the updates to be done on nodes in the database, and data to store in the dump file.

    Parameters:
        I_clockwork_nodes   Iterator on Clockwork nodes we want to insert or update in the database

    Returns:
        A 2-tuple containing (in this order) the following elements:
            - A list of the database operations (UpdateOne, from pymongo) summarizing the
              updates to be done into the database for the nodes
            - A list of elements to store in the dump file
    """

    L_updates_to_do = []  # Initialize the list of elements to update
    L_data_for_dump_file = (
        []
    )  # Initialize the list of elements to store into the dump file

    for D_node in I_clockwork_nodes:

        # Add these field each time an entry is updated
        now = time.time()
        D_node["cw"]["last_slurm_update"] = now
        D_node["cw"]["last_slurm_update_by_sacct"] = now

        L_data_for_dump_file.append(D_node)

        L_updates_to_do.append(
            UpdateOne(
                # rule to match if already present in collection
                {
                    "slurm.name": D_node["slurm"]["name"],
                    "slurm.cluster_name": D_node["slurm"]["cluster_name"],
                },
                # the data that we write in the collection
                {
                    "$set": {"slurm": D_node["slurm"]},
                    "$setOnInsert": {"cw": D_node["cw"]},
                },
                # create if missing, update if present
                upsert=True,
            )
        )

    return (L_updates_to_do, L_data_for_dump_file)


"""
def associate_account(LD_sacct_jobs):
    L_user_updates = []
    for D_job in LD_sacct_jobs:

        # In theory, someone could have copy/pasted the special sbatch command
        # (that we gave them on the web site) on the Mila cluster instead of CC.
        # We really want to avoid that kind of problem whereby someone's
        # "cc_account_username" will be set to their "mila_cluster_username"
        # due to that.
        #
        # The way that we prevent this is by setting a particular value
        # in the cluster config. Here's a snippet from test_config.toml
        # that clearly shows `update_field=false`.
        #    [clusters.mila]
        #    account_field="mila_cluster_username"
        #    update_field=false

        # Register accounts for external clusters (e.g. Compute Canada)
        # using a special comment field in jobs.
        # There is a convention here about the form that
        # a "comment" field can take in order to trigger that.
        comment = D_job["slurm"].get("comment", None)
        marker = "clockwork_register_account:"
        if comment is not None and comment.startswith(marker):
            secret_key = comment[len(marker) :]
            clusters = get_all_clusters()
            cluster_info = clusters[D_job["slurm"]["cluster_name"]]
            # To help follow along, here's an example of the values
            # taken by those variables in the test_config.toml file.
            #    [clusters.beluga]
            #    account_field = "cc_account_username"
            #    update_field = "cc_account_update_key"
            account_field = cluster_info["account_field"]
            update_field = cluster_info["update_field"]

            # Note that we're looking at entries for "users" here,
            # and not for jobs entries.
            # For users, we have entries in the database that look like this:
            # {
            #   "mila_email_username": "student00@mila.quebec",
            #   "status": "enabled",
            #   "clockwork_api_key": "000aaa00",
            #   "mila_cluster_username": "milauser00",
            #   "cc_account_username": "ccuser00",
            #   "cc_account_update_key": null,
            #   "web_settings": {
            #     "nbr_items_per_page": 40,
            #     "dark_mode": false
            #   },
            #   "personal_picture": "https://mila.quebec/wp-content/uploads/2019/08/guillaume_alain_400x700-400x400.jpg"
            # }

            # The mechanics are as follows.
            # If the `update_field` is present in a job, make note of that username
            # from the job. Then make a query that wants to update the appropriate
            # field for the user in the database that has exactly that secret key.
            if update_field:
                external_username_to_update = D_job["slurm"][account_field]
                L_user_updates.append(
                    UpdateOne(
                        {update_field: secret_key},
                        {
                            "$set": {
                                account_field: external_username_to_update,
                                update_field: None,
                            }
                        },
                    )
                )

    return L_user_updates
"""


def main_read_users_and_update_collection(
    users_collection,
    users_json_file,
):

    timestamp_start = time.time()
    L_updates_to_do = []

    with open(users_json_file, "r") as f:
        users_to_store = json.load(f)

    for user_to_store in users_to_store:

        # Add the user to the queue of updates to do
        L_updates_to_do.append(
            UpdateOne(
                # rule to match if already present in collection
                {"mila_email_username": user_to_store["mila_email_username"]},
                # the data that we write in the collection
                {"$set": user_to_store},
                # create if missing, update if present
                upsert=True,
            )
        )

    if L_updates_to_do:
        print("result = users_collection.bulk_write(L_updates_to_do)")
        result = users_collection.bulk_write(L_updates_to_do)
        pprint_bulk_result(result)
    mongo_update_duration = time.time() - timestamp_start
    print(
        f"Bulk write for {len(L_updates_to_do)} user entries in mongodb took {mongo_update_duration} seconds."
    )
