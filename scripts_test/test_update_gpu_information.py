"""
Test functions of the script allowing to update the GPU information.
"""

import pytest
from pymongo import MongoClient

from scripts.update_gpu_information import update_gpu_information
from scripts_test.config import get_config


def test_insertion_from_an_empty_collection():
    # Initialization
    mongodb_collection_name = "test_gpu"

    # GPU information to insert the first time in the database
    gpu_infos_insert = {
        "gpu_infos": [
            {
                "name": "rtx8000",
                "vendor": "nvidia",
                "ram": 48,
                "cuda_cores": 4608,
                "tensor_cores": 576,
                "tflops_fp32": 16.3,
            },
            {
                "name": "test",
                "vendor": "test_vendor",
                "ram": 56,
                "cuda_cores": 6200,
                "tensor_cores": 602,
                "tflops_fp32": 10.3,
            },
        ]
    }

    first_insert_example = gpu_infos_insert["gpu_infos"][0]
    last_insert_example = gpu_infos_insert["gpu_infos"][-1]

    # GPU information used to launch the update_gpu_information a second time:
    # it contains at list a new GPU (new name) and a different pre-existing
    # GPU (same name but different informations)

    gpu_infos_update = {
        "gpu_infos": [
            {
                "name": first_insert_example["name"],
                "vendor": "other vendor",
                "ram": first_insert_example["ram"]
                + 1,  # to be sure that the values differ
                "cuda_cores": 5000,
                "tensor_cores": 425,
                "tflops_fp32": 14,
            },
            {
                "name": "other_name",
                "vendor": "other vendor",
                "ram": 36,
                "cuda_cores": 6200,
                "tensor_cores": 603,
                "tflops_fp32": 16.4,
            },
            {
                "name": "still another name",
                "vendor": "other vendor",
                "ram": 54,
                "cuda_cores": 7895,
                "tensor_cores": 653,
                "tflops_fp32": 15.98,
            },
        ]
    }

    first_update_example = gpu_infos_update["gpu_infos"][0]
    last_update_example = gpu_infos_update["gpu_infos"][-1]

    # Connect to MongoDB
    client = MongoClient(get_config("mongo.connection_string"))
    db = client[get_config("mongo.database_name")]

    # Clean the 'gpu' collection
    db.drop_collection(mongodb_collection_name)

    # Launch the script the first time to insert information
    update_gpu_information(
        gpu_infos_insert,
        get_config("mongo.connection_string"),
        get_config("mongo.database_name"),
        mongodb_collection_name,
    )

    # Check the content of the database
    assert (
        db[mongodb_collection_name].find_one(
            # Filter to find the entry (by checking its `name` attribute)
            {"name": first_insert_example["name"]},
            # The result does not contain the field `_id`
            {"_id": 0},
        )
        == first_insert_example
    )
    assert (
        db[mongodb_collection_name].find_one(
            # Filter to find the entry (by checking its `name` attribute)
            {"name": last_insert_example["name"]},
            # The result does not contain the field `_id`
            {"_id": 0},
        )
        == last_insert_example
    )

    # Launch the script again, with different values
    update_gpu_information(
        gpu_infos_update,
        get_config("mongo.connection_string"),
        get_config("mongo.database_name"),
        mongodb_collection_name,
    )

    # Check the content of the database
    assert (
        db[mongodb_collection_name].find_one(
            # Filter to find the entry (by checking its `name` attribute)
            {"name": first_update_example["name"]},
            # The result does not contain the field `_id`
            {"_id": 0},
        )
        == first_update_example
    )
    assert (
        db[mongodb_collection_name].find_one(
            # Filter to find the entry (by checking its `name` attribute)
            {"name": last_update_example["name"]},
            # The result does not contain the field `_id`
            {"_id": 0},
        )
        == last_update_example
    )
