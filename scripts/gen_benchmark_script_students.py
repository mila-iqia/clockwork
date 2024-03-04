import sys
import os
from datetime import datetime
import argparse

SIZES_STUDENT00 = [0, 10_000, 100_000, 1_000_000, 2_000_000]
SIZES_STUDENT01 = list(range(0, 101, 20))
NB_PROPS_PER_DICT = 4

NB_REQUESTS = 10


def main(argv):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--disable-index",
        action="store_true",
        help="If specified, will not create MongoDB index when storing fake data.",
    )
    args = parser.parse_args(argv[1:])
    print("Generating benchmark script with args:", args, file=sys.stderr)

    bench_date = datetime.now()
    bench_basename = "bench_students"
    if args.disable_index:
        bench_basename += "_noindex"
    bench_name = f"{bench_basename}_{bench_date}".replace(" ", "_").replace(":", "-")
    assert not os.path.exists(bench_name)
    os.mkdir(bench_name)

    script_name = f"{bench_name}.sh"
    with open(script_name, "w") as file:
        print("set -eu", file=file)
        print("export CLOCKWORK_API_KEY='000aaa01'", file=file)
        print("export CLOCKWORK_EMAIL='student01@mila.quebec'", file=file)
        print(file=file)

        for std_00 in SIZES_STUDENT00:
            for std_01 in SIZES_STUDENT01:
                gen_commands(std_00, std_01, bench_name, args, file)

        print(file=file)
        print(f"python3 scripts/plot_benchmark_students.py {bench_name}", file=file)
        print(f"tar -cf {bench_name}.tar {bench_name}/", file=file)
        print(f"echo Benchmark compressed in: {bench_name}.tar", file=file)

    print("Benchmark script saved in:", script_name, file=sys.stderr)


def gen_commands(nb_jobs_student00, nb_jobs_student01, working_directory, args, file):
    nb_dicts = nb_jobs_student00 + nb_jobs_student01
    task_name = (
        f"std00-{nb_jobs_student00:06}_"
        f"std01-{nb_jobs_student01:06}_"
        f"dicts-{nb_dicts}_"
        f"props-{NB_PROPS_PER_DICT}_"
        f"index-{0 if args.disable_index else 1}"
    )

    print(
        (
            f"python3 scripts/store_huge_fake_data_in_db.py "
            f"-j student00={nb_jobs_student00} "
            f"-j student01={nb_jobs_student01} "
            f"--nb-dicts {nb_dicts} "
            f"--nb-props-per-dict {NB_PROPS_PER_DICT} "
            f"--props-username student01@mila.quebec "
            f"{'--disable-index' if args.disable_index else ''}"
        ),
        file=file,
    )
    print('python3 -m flask run --host="0.0.0.0" &', file=file)
    print("export SERVER_PID=$!", file=file)
    print("sleep 1", file=file)
    print(
        '''python3 -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:5000/').getcode())"''',
        file=file,
    )
    print(
        (
            f"python3 scripts/job_request_benchmark.py "
            f"-w {working_directory} "
            f'--address "0.0.0.0" '
            f"--port 5000 "
            f'--username "student01@mila.quebec" '
            f"--nb-requests {NB_REQUESTS} "
            f"--output {task_name}"
        ),
        file=file,
    )
    print("kill $SERVER_PID", file=file)
    print("export SERVER_PID=", file=file)
    print(file=file)


if __name__ == "__main__":
    main(sys.argv)
