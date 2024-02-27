import os
import sys
import json


try:
    import matplotlib.pyplot as plt

    # plt.figure(figure=(10.8, 7.2), dpi=100)
except Exception:
    print(
        "Matplotlib needed. You can install it with `pip install matplotlib`",
        file=sys.stderr,
    )
    raise


def main():
    if len(sys.argv) != 2:
        print("Missing stats folder", file=sys.stderr)
        sys.exit(1)

    # Get stat files.
    folder = sys.argv[1]
    stats_file_names = []
    for name in os.listdir(folder):
        if name.startswith("jobs-") and name.endswith(".json"):
            stats_file_names.append(name)

    # Get stat data.
    stats = {}
    nbs_jobs = []
    nbs_dicts = []
    nbs_props = []
    for name in sorted(stats_file_names):
        title, extension = name.split(".")
        jobs_info, dicts_info, props_info = title.split("_")
        _, nb_jobs = jobs_info.split("-")
        _, nb_dicts = dicts_info.split("-")
        _, nb_props_per_dict = props_info.split("-")
        nb_jobs = int(nb_jobs)
        nb_dicts = int(nb_dicts)
        nb_props_per_dict = int(nb_props_per_dict)
        with open(os.path.join(folder, name)) as file:
            local_stats = json.load(file)
            assert len({stat["nb_jobs"] for stat in local_stats}) == 1
            durations = sorted(stat["pc_nanoseconds"] for stat in local_stats)
            stats[(nb_jobs, nb_dicts, nb_props_per_dict)] = durations
            nbs_jobs.append(nb_jobs)
            nbs_dicts.append(nb_dicts)
            nbs_props.append(nb_props_per_dict)

    assert sorted(set(nbs_jobs)) == sorted(set(nbs_dicts))
    Ns = sorted(set(nbs_jobs))
    Ks = sorted(set(nbs_props))

    _plot_request_time_per_nb_dicts(stats, Ns, Ks, folder)
    _plots_request_time_per_nb_jobs(stats, Ns, Ks, folder)


def _plot_request_time_per_nb_dicts(stats: dict, Ns: list, Ks: list, folder: str):
    N = max(Ns)

    x_nb_dicts = list(Ns)
    y_time = {nb_props: [] for nb_props in Ks}

    for nb_props in Ks:
        print()
        for nb_dicts in Ns:
            key = (N, nb_dicts, nb_props)
            average_duration = _debug_average_seconds(key, stats[key])
            y_time[nb_props].append(average_duration)

    fig, ax = plt.subplots()
    for nb_props in Ks:
        ax.plot(
            x_nb_dicts,
            y_time[nb_props],
            marker="o",
            label=f"{_compute_nb_jobs(N)} jobs in DB, {nb_props} prop(s) per dict",
        )
        _show_points(x_nb_dicts, y_time[nb_props])

    ax.set_title("Request duration per number of job-user dicts")
    ax.set_xlabel("Number of job-user dicts in DB")
    ax.set_ylabel("Request duration in seconds")
    ax.legend()
    plot_path = os.path.join(
        folder,
        f"nb_dicts_to_time_for_{_compute_nb_jobs(N)}_jobs.jpg",
    )
    plt.gcf().set_size_inches(20, 10)
    plt.savefig(plot_path, bbox_inches="tight")
    plt.close(fig)


def _plots_request_time_per_nb_jobs(stats: dict, Ns: list, Ks: list, folder: str):
    x_nb_jobs = list(Ns)
    y_time_0_dicts_1_props = []
    y_time_N_dicts = {nb_props: [] for nb_props in Ks}
    N = max(Ns)

    print()
    for nb_jobs in Ns:
        key = (nb_jobs, 0, 1)
        average_duration = _debug_average_seconds(key, stats[key])
        y_time_0_dicts_1_props.append(average_duration)
    print()
    for nb_props in Ks:
        for nb_jobs in Ns:
            key = (nb_jobs, N, nb_props)
            average_duration = _debug_average_seconds(key, stats[key])
            y_time_N_dicts[nb_props].append(average_duration)

    fig, ax = plt.subplots()
    ax.plot(
        x_nb_jobs, y_time_0_dicts_1_props, marker="o", label=f"0 job-user dicts in DB"
    )
    _show_points(x_nb_jobs, y_time_0_dicts_1_props)

    for nb_props in Ks:
        ax.plot(
            x_nb_jobs,
            y_time_N_dicts[nb_props],
            marker="o",
            label=f"{_compute_nb_jobs(N)} job-user dicts in DB, {nb_props} props per dict",
        )
        _show_points(x_nb_jobs, y_time_N_dicts[nb_props])

    ax.set_title("Request duration per number of jobs")
    ax.set_xlabel("Number of jobs in DB")
    ax.set_ylabel("Request duration in seconds")
    ax.legend()
    plot_path = os.path.join(folder, f"nb_jobs_to_time.jpg")
    plt.gcf().set_size_inches(20, 10)
    plt.savefig(plot_path, bbox_inches="tight")
    plt.close(fig)


def _compute_nb_jobs(n: int):
    return n


def _show_points(xs, ys):
    # return
    for x, y in zip(xs, ys):
        plt.text(x, y, f"({x}, {round(y, 2)})")


def _debug_average_seconds(key, durations):
    nb_jobs, nb_dicts, nb_props = key
    avg = sum(durations) / (len(durations) * 1e9)
    print(
        f"jobs {nb_jobs:02} dicts {nb_dicts:02} props {nb_props:02}",
        avg,
        [d / 1e9 for d in durations],
    )
    return avg


if __name__ == "__main__":
    main()
