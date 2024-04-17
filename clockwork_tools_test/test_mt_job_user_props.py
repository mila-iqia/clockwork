import random


def _get_test_user_props(mtclient, fake_data):
    # Find an entry that's associated with the user that's currently logged in.
    # This becomes the ground truth against which we compare the retrieved user props.
    LD_candidates = [
        D_job_user_props_entry
        for D_job_user_props_entry in fake_data["job_user_props"]
        if (
            D_job_user_props_entry["mila_email_username"] == mtclient.email
            and len(D_job_user_props_entry["props"]) > 0
        )
    ]
    assert (
        len(LD_candidates) > 0
    ), "There should be at least one job_user_props entry for the user that's currently logged in."
    D_job_user_props_entry = random.choice(LD_candidates)

    job_id = D_job_user_props_entry["job_id"]
    cluster_name = D_job_user_props_entry["cluster_name"]
    original_props = D_job_user_props_entry["props"]
    return job_id, cluster_name, original_props


def test_cw_tools_get_user_props(mtclient, fake_data):
    job_id, cluster_name, original_props = _get_test_user_props(mtclient, fake_data)
    props = mtclient.get_user_props(job_id, cluster_name)
    assert original_props == props


def test_cw_tools_set_and_delete_user_props(mtclient, fake_data):
    job_id, cluster_name, original_props = _get_test_user_props(mtclient, fake_data)

    assert original_props
    # Test we can replace existing user prop value.
    an_existing_prop_name = next(iter(original_props.keys()))
    a_new_value = "a totally new value"
    # We check new value is not already associated to existing prop name
    assert original_props[an_existing_prop_name] != a_new_value
    # Set new value
    props = mtclient.set_user_props(
        job_id, cluster_name, {an_existing_prop_name: a_new_value}
    )
    # Check set returns same value as get
    assert props == mtclient.get_user_props(job_id, cluster_name)
    # Check returned props
    assert len(props) == len(original_props)
    # Props should be original props, except that `an_existing_prop_name` is now associated to `a_new_value`.
    assert props == {
        an_existing_prop_name: a_new_value,
        **{
            key: value
            for key, value in original_props.items()
            if key != an_existing_prop_name
        },
    }

    # Get back to original props for tests below
    props = mtclient.set_user_props(job_id, cluster_name, original_props)
    # Check set and get
    assert props == mtclient.get_user_props(job_id, cluster_name) == original_props

    # Define new props to add
    new_props = {"a new name": "a new prop", "aa": "aa", "bb": "bb", "cc": "cc"}
    # We check new props are not already in original props
    for new_prop_name in new_props.keys():
        assert new_prop_name not in original_props

    # Test set new props
    props = mtclient.set_user_props(job_id, cluster_name, new_props)
    assert len(props) == len(original_props) + len(new_props)
    assert props == {**original_props, **new_props}

    # Test delete a prop using a str
    assert mtclient.delete_user_props(job_id, cluster_name, "aa") == ""
    props = mtclient.get_user_props(job_id, cluster_name)
    assert len(props) == len(original_props) + len(new_props) - 1
    assert props == {
        **original_props,
        "a new name": "a new prop",
        "bb": "bb",
        "cc": "cc",
    }

    # Test delete a prop using a list with 1 string
    assert mtclient.delete_user_props(job_id, cluster_name, ["a new name"]) == ""
    props = mtclient.get_user_props(job_id, cluster_name)
    assert len(props) == len(original_props) + len(new_props) - 2
    assert props == {**original_props, "bb": "bb", "cc": "cc"}

    # Test delete multiple props using a list with many strings
    assert mtclient.delete_user_props(job_id, cluster_name, ["bb", "cc"]) == ""
    props = mtclient.get_user_props(job_id, cluster_name)
    assert props == original_props

    # As props are not original_props, no need to clean-up code here!
