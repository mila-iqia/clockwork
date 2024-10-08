"""
Just a little helper program to combine fake users, fake jobs, fakes nodes
into a single json file as a dict. The output path is the first argument.
This script is expected to be used only once, but let's write it
so it can take an arbitrary enumeration of pairs of arguments.

python3 stitch_json_lists_as_dict.py \
    ${CLOCKWORK_ROOT}/test_common/fake_data.json \
    users ${FAKE_USERS_FILE} \
    jobs ${CLOCKWORK_ROOT}/tmp/slurm_report/subset_100_jobs_anonymized.json \
    nodes ${CLOCKWORK_ROOT}/tmp/slurm_report/subset_100_nodes_anonymized.json \
    gpu ${CLOCKWORK_ROOT}/scripts/fake_gpu_information.json
"""

import os, sys
import json


def main(argv):

    assert 4 <= len(argv)
    assert len(argv[1:]) % 2 == 1

    D_results = {}
    output_path = argv[1]
    for k, v_path in zip(argv[2::2], argv[3::2]):
        print((k, v_path))
        with open(v_path, "r") as f:
            v = json.load(f)
            # extra data useful for processing but that should be stripped.
            for d in v:
                if "_extra" in d:
                    del d["_extra"]
            D_results[k] = v

    with open(output_path, "w") as f:
        json.dump(D_results, f, indent=2)
        print(f"Wrote {output_path}.")


if __name__ == "__main__":
    import sys

    main(sys.argv)
