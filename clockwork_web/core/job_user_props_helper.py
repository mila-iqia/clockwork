"""Internal functions to manage job-user props."""
from ..db import get_db
import json


# Max length allowed for a JSON-string representing a job-user props dict.
# Currently, 2 Mb.
MAX_PROPS_LENGTH = 2 * 1024 * 1024


class HugeUserPropsError(ValueError):
    """Exception raised when user props are too huge in database."""


def get_user_props(job_id: str, cluster_name: str, mila_email_username: str) -> dict:
    """
    Get job-user props.

    Parameters:
        job_id                  ID of job for which we want to get user props.
        cluster_name            Name of cluster to which the job belongs.
        mila_email_username     Email of user who sets the props we want to get.

    Returns:
        Dictionary of user-props, empty if no props were found.
        Each prop is a key-value pair in returned dictionary.
    """
    # Get matching MongoDB document.
    props_dict = _get_user_props_document(job_id, cluster_name, mila_email_username)
    # Return props if available.
    return props_dict.get("props", {})


def set_user_props(
    job_id: str, cluster_name: str, updates: dict, mila_email_username: str
) -> dict:
    """
    Update job-user-props.

    Parameters:
        job_id                  ID of job for which we want to update user props.
        cluster_name            Name of cluster to which the job belongs.
        updates                 Dictionary of props to add.
                                Each key-value represents a prop.
        mila_email_username     Email of user who wants to update his props.

    Returns:
        Dictionary of Updated job-user props.
    """
    # Get previous props and check that
    # previous + updates props do not exceed a size limit.
    previous_doc = _get_user_props_document(job_id, cluster_name, mila_email_username)
    previous_props = previous_doc.get("props", {})
    new_props = previous_props.copy()
    new_props.update(updates)
    if _get_dict_size(new_props) > MAX_PROPS_LENGTH:
        raise HugeUserPropsError(
            f"Too huge job-user props: maximum {_get_megabytes(MAX_PROPS_LENGTH)} Mbytes "
            f"(previous: {_get_megabytes(_get_dict_size(previous_props))} Mbytes, "
            f"updates: {_get_megabytes(_get_dict_size(updates))} Mbytes)"
        )

    # Update or insert job-user props.
    mc = get_db()
    db = mc["job_user_props"]
    if "_id" in previous_doc:
        db.update_one({"_id": previous_doc["_id"]}, {"$set": {"props": new_props}})
    else:
        db.insert_one(
            {
                "job_id": job_id,
                "cluster_name": cluster_name,
                "mila_email_username": mila_email_username,
                "props": new_props,
            }
        )

    return new_props


def delete_user_props(job_id, cluster_name, key_or_keys, mila_email_username: str):
    """
    Delete some job-user props.

    Parameters:
        job_id                  ID of job for which we want to delete some user props.
        cluster_name            Name of cluster to which the job belongs.
        key_or_keys             Either a key or a sequence of keys,
                                representing prop names to delete.
        mila_email_username     Email of user who wants to delete props.
    """
    # Parse key_or_keys to get keys to delete.
    if isinstance(key_or_keys, str):
        keys = [key_or_keys]
    else:
        assert isinstance(key_or_keys, (list, tuple, set))
        keys = list(key_or_keys)

    # Get previous props
    previous_doc = _get_user_props_document(job_id, cluster_name, mila_email_username)
    previous_props = previous_doc.get("props", {})
    new_props = previous_props.copy()
    # Remove keys
    for key in keys:
        new_props.pop(key, None)
    # Register in MongoDB
    if len(new_props) < len(previous_props):
        mc = get_db()
        db = mc["job_user_props"]
        db.update_one({"_id": previous_doc["_id"]}, {"$set": {"props": new_props}})


def _get_user_props_document(
    job_id: str, cluster_name: str, mila_email_username: str
) -> dict:
    """
    Get MongoDB document representing job-user props corresponding to given parameters.

    Parameters:
        job_id                  ID of job for which we want to get user props.
        cluster_name            Name of cluster to which the job belongs.
        mila_email_username     Email of user who sets the props we want to get.

    Returns:
        MongoDB document representing job-user props.
        Document is a dictionary with following format:
        {
            job_id: str                 # ID of job associated to props.
            cluster_name: str           # cluster name of job associated to props.
            mila_email_username: str    # user who created these props.
            props: dict                 # actual user-props, each prop is a key-value.
        }
    """
    mc = get_db()
    result = list(
        mc["job_user_props"].find(
            {
                "job_id": job_id,
                "cluster_name": cluster_name,
                "mila_email_username": mila_email_username,
            }
        )
    )
    if not result:
        return {}
    else:
        assert len(result) == 1
        (props,) = result
        return props


def _get_dict_size(dct: dict) -> int:
    """Get length of JSON-string representation for given dictionary."""
    return len(json.dumps(dct))


def _get_megabytes(size: int) -> float:
    """Convert bytes to megabytes."""
    return size / (1024 * 1024)
