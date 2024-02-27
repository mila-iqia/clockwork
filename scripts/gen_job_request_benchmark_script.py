import sys

# Ns = [i * 10_000 for i in range(16)]
Ns = [i * 10_000 for i in range(11)]
Ks = (1, 500)
N = Ns[-1]

NB_REQUESTS = 10


def main():
    if len(sys.argv) == 2:
        wd = sys.argv[1]
    else:
        wd = "local"

    print("set -eu")

    for nb_props_per_dict in Ks:
        for nb_dicts in Ns:
            gen_commands(N, nb_dicts, nb_props_per_dict, wd)

    for nb_jobs in Ns[:-1]:
        gen_commands(nb_jobs, 0, 1, wd)

    for nb_props_per_dict in Ks:
        for nb_jobs in Ns[:-1]:
            gen_commands(nb_jobs, N, nb_props_per_dict, wd)


def gen_commands(nb_jobs, nb_dicts, nb_props_per_dict, working_directory):
    task_name = f"jobs-{nb_jobs:06}_dicts-{nb_dicts:06}_props-{nb_props_per_dict:03}"

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
    print('python3 -m flask run --host="0.0.0.0" &')
    print("export SERVER_PID=$!")
    print("sleep 1")
    print(
        '''python3 -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:5000/').getcode())"'''
    )
    print(cmd_benchmark)
    print("kill $SERVER_PID")
    print("export SERVER_PID=")
    print()


if __name__ == "__main__":
    main()
