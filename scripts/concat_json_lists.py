"""
For some json files containing lists of elements,
produce a resulting file containing the concatenation
of those lists. Allows only for keeping only a fixed
number of elements, chosen at random.

Order is not preserved because we don't care about that
for our predicted usage.
"""

import sys, os
import numpy as np
import argparse
import json


def main(argv):

    my_parser = argparse.ArgumentParser()
    my_parser.add_argument("--keep", type=int, default=None)
    my_parser.add_argument("--output", type=str, default=None)
    my_parser.add_argument("--inputs", action="store", type=str, nargs="*")

    args = my_parser.parse_args(argv[1:])
    print(args)

    # In order to keep jobs and nodes from all our input sources,
    # regardless of the repartition of the jobs and nodes by clusters,
    # we divide the number we want to keep by the number of input
    # sources we use, and keep this number of elements from each source.
    kept_elements_nb = round(args.keep / len(args.inputs)) + 1
    # Nota bene: as this number has to be an integer, we are not sure to
    # have a perfect fraction of the requested number. Thus, we round up the
    # result then add one: the surplus would then be withdrawn from the
    # resulting data, but, unless we work with very little values (or a lot
    # of input sources), it should not represent all the elements of any
    # input source.

    L = []
    # For each input file
    for input_path in args.inputs:
        with open(input_path, "r") as f:
            E = json.load(f)
            # Get a part of the data
            np.random.shuffle(E)
            E = E[0:kept_elements_nb]
        L.extend(E)

    if args.keep is not None:
        assert 0 < args.keep
        assert args.keep <= len(
            L
        ), f"Not enough arguments for --keep. We have {len(L)} values in concatenated lists, but we're asking for {args.keep}."
        # N = len(L)
        np.random.shuffle(L)
        L = L[0 : args.keep]
        # indices_to_keep = np.random.permutation(N)[0:args.keep]
        # print(indices_to_keep)
        # print(indices_to_keep.dtype)
        # print(type(indices_to_keep))
        # L = L[indices_to_keep.tolist()]

    if args.output is not None:
        with open(args.output, "w") as f:
            json.dump(L, f, indent=2)
            print(f"Wrote {args.output}.")


if __name__ == "__main__":
    main(sys.argv)

"""

export CLOCKWORK_ROOT=..

python3 concat_json_lists.py --keep 10 \
    --output ${CLOCKWORK_ROOT}/tmp/slurm_report/subset_10_jobs.json \
    --inputs \
    ${CLOCKWORK_ROOT}/tmp/slurm_report/beluga/job_anonymized_dump_file.json \
    ${CLOCKWORK_ROOT}/tmp/slurm_report/cedar/job_anonymized_dump_file.json \
    ${CLOCKWORK_ROOT}/tmp/slurm_report/graham/job_anonymized_dump_file.json \
    ${CLOCKWORK_ROOT}/tmp/slurm_report/mila/job_anonymized_dump_file.json

"""
