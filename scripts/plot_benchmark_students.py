import os
import sys
import json


try:
    import matplotlib.pyplot as plt
    from matplotlib import colors

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
        if name.startswith("student00-") and name.endswith(".json"):
            stats_file_names.append(name)

    # Get stat data.
    stats = {}
    for name in sorted(stats_file_names):
        title, extension = name.split(".")
        info_student00, info_student01 = title.split("_")
        _, nb_jobs_student00 = info_student00.split("-")
        _, nb_jobs_student01 = info_student01.split("-")
        nb_jobs_student00 = int(nb_jobs_student00)
        nb_jobs_student01 = int(nb_jobs_student01)

        with open(os.path.join(folder, name)) as file:
            local_stats = json.load(file)
            nbs_jobs = {stat["nb_jobs"] for stat in local_stats}
            assert len(nbs_jobs) == 1
            assert next(iter(nbs_jobs)) == nb_jobs_student01
            durations = sorted(stat["pc_nanoseconds"] for stat in local_stats)
            stats[(nb_jobs_student00, nb_jobs_student01)] = durations

    _plots_request_time_per_nb_jobs(stats, folder)


def _plots_request_time_per_nb_jobs(stats: dict, folder: str):
    cdict = {
        "red": (
            (0.0, 0.0, 0.0),
            # (1.0, 0.5, 0.5),
            (1.0, 1.0, 0.0),
        ),
        "green": (
            (0.0, 0.0, 1.0),
            # (1.0, 0.5, 0.5),
            (1.0, 0.0, 0.0),
        ),
        "blue": (
            (0.0, 0.0, 0.0),
            # (1.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
        ),
    }

    cmap = colors.LinearSegmentedColormap("custom", cdict)

    student00_to_plot = {}
    for (student00, student01), durations in stats.items():
        average_duration = _debug_average_seconds((student00, student01), durations)
        student00_to_plot.setdefault(student00, []).append(
            (student01, average_duration)
        )

    fig, ax = plt.subplots()
    n = len(student00_to_plot) - 1
    for i, student00 in enumerate(sorted(student00_to_plot.keys())):
        local_data = student00_to_plot[student00]
        xs = [couple[0] for couple in local_data]
        ys = [couple[1] for couple in local_data]
        print(cmap(i / n))
        ax.plot(
            xs,
            ys,
            marker="o",
            label=f"student00: {student00} jobs",
            c=cmap(i / n),
        )
        # _show_points(xs, ys)

    ax.set_title("Request duration per number of jobs for student01")
    ax.set_xlabel("Number of student01's jobs in DB")
    ax.set_ylabel("Request duration in seconds")
    ax.legend()
    plot_path = os.path.join(folder, f"nb_student01_jobs_to_time.jpg")
    plt.gcf().set_size_inches(20, 10)
    plt.savefig(plot_path, bbox_inches="tight")
    plt.close(fig)


def _show_points(xs, ys):
    # return
    for x, y in zip(xs, ys):
        plt.text(x, y, f"({x}, {round(y, 2)})")


def _debug_average_seconds(key, durations):
    sdt00, std01 = key
    avg = sum(durations) / (len(durations) * 1e9)
    print(
        f"student00 {sdt00:02} student01 {std01:02}",
        avg,
        [d / 1e9 for d in durations],
    )
    return avg


if __name__ == "__main__":
    main()
