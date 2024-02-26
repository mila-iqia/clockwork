import sys

# max: sum(2**i for i in range(n)) jobs
# max: sum(2**i for i in range(n)) dicts
N = 17
Ks = (1, 10, 100)

NB_REQUESTS = 10


def main():
    if len(sys.argv) == 2:
        wd = sys.argv[1]
    else:
        wd = "local"

    print("set -eu")

    for nb_props_per_dict in Ks:
        for nb_dicts in range(N + 1):
            gen_commands(N, nb_dicts, nb_props_per_dict, wd)

    for nb_jobs in range(N):
        gen_commands(nb_jobs, 0, 1, wd)

    for nb_props_per_dict in Ks:
        for nb_jobs in range(N):
            gen_commands(nb_jobs, N, nb_props_per_dict, wd)


def gen_commands(nb_jobs, nb_dicts, nb_props_per_dict, working_directory):
    task_name = f"jobs-{nb_jobs:02}_dicts-{nb_dicts:02}_props-{nb_props_per_dict:02}"

    cmd_fake_data = (
        f"python3 scripts/store_huge_fake_data_in_db.py "
        f"--nb-jobs {nb_jobs} "
        f"--nb-dicts {nb_dicts} "
        f"--nb-props-per-dict {nb_props_per_dict}"
    )
    cmd_benchmark = (
        f"python3 scripts/job_request_benchmark.py "
        f"--config {working_directory}/config.json "
        f"--nb-requests {NB_REQUESTS} "
        f"--output {task_name}"
    )
    print(cmd_fake_data)
    print(cmd_benchmark)


if __name__ == "__main__":
    main()
