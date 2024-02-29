import sys
import os

SIZES_STUDENT00 = [0, 10_000, 100_000, 1_000_000, 2_000_000]
SIZES_STUDENT01 = list(range(0, 101, 20))
NB_PROPS_PER_DICT = 4

NB_REQUESTS = 10


def main():
    if len(sys.argv) != 2:
        print("Missing output folder name", file=sys.stderr)
        exit(1)

    wd = sys.argv[1]
    if not os.path.exists(wd):
        os.mkdir(wd)

    print("set -eu")
    print("export CLOCKWORK_API_KEY='000aaa01'")
    print("export CLOCKWORK_EMAIL='student01@mila.quebec'")
    print()

    for std_00 in SIZES_STUDENT00:
        for std_01 in SIZES_STUDENT01:
            gen_commands(std_00, std_01, wd)


def gen_commands(nb_jobs_student00, nb_jobs_student01, working_directory):
    task_name = f"student00-{nb_jobs_student00:06}_student01-{nb_jobs_student01:06}"
    nb_dicts = nb_jobs_student00 + nb_jobs_student01
    nb_props_per_dict = NB_PROPS_PER_DICT

    cmd_fake_data = (
        f"python3 scripts/store_huge_fake_data_in_db.py "
        f"-j student00={nb_jobs_student00} "
        f"-j student01={nb_jobs_student01} "
        f"--nb-dicts {nb_dicts} "
        f"--nb-props-per-dict {nb_props_per_dict}"
    )
    cmd_benchmark = (
        f"python3 scripts/job_request_benchmark.py "
        f"-w {working_directory} "
        f'--address "0.0.0.0" '
        f"--port 5000 "
        f'--username "student01@mila.quebec" '
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
