import numpy as np

import pylab
import matplotlib.pyplot as plt

import json

"""
   {
    "single_page_duration": 0.0025930404663085938,
    "nbr_skipped_items": 18,
    "nbr_items_to_display": 100,
    "total_inserted": 1000001,
    "nbr_results_on_page": 100,
    "count_duration": 0.0013692378997802734
  },
"""

def one_plot_index_vs_no_index(
    D_source_index,
    D_source_no_index,
    output_path_png,
    output_path_json):

    # this value is supposed to be more or less constant throughout,
    # and by eye inspection it is the case so we don't need to bother
    # with tracking and plotting stddev (it would be more of a distraction)
    index_count_mean_duration = np.array([D_data["count_duration"] for D_data in D_source_index["LD_data"]]).mean()
    no_index_count_mean_duration = np.array([D_data["count_duration"] for D_data in D_source_no_index["LD_data"]]).mean()

    # this value is the same everywhere, or else you have violated your assumptions
    nbr_items_to_display = D_source_index["LD_data"][0]["nbr_items_to_display"]
    for e in D_source_index["LD_data"]:
        assert ["nbr_items_to_display"] == nbr_items_to_display
    for e in D_source_no_index["LD_data"]:
        assert ["nbr_items_to_display"] == nbr_items_to_display

    # get the data that you want to use for plotting
    L_x_index = [D_data["nbr_skipped_items"]       for D_data in D_source_index["LD_data"]]
    L_y_index = [D_data["single_page_duration"]    for D_data in D_source_index["LD_data"]]
    #
    L_x_no_index = [D_data["nbr_skipped_items"]    for D_data in D_source_no_index["LD_data"]]
    L_y_no_index = [D_data["single_page_duration"] for D_data in D_source_no_index["LD_data"]]

    plt.plot(L_x_index, L_y_index, label="with index")
    plt.plot(L_x_no_index, L_y_no_index, label="without index")

    # TODO have these labels as text instead
    plt.axhline(y=index_count_mean_duration, label="count with index", style="--")
    plt.axhline(y=no_index_count_mean_duration, label="count without index", style="--")

    pylab.savefig(output_path_png, dpi=250)
    pylab.close()
    print(f"Wrote {output_path_png}.")

    with open(output_path_json, "w") as f:
        json.write(dict(
            L_x_index=L_x_index, L_y_index=L_y_index,
            L_x_no_index=L_x_no_index, L_y_no_index=L_y_no_index,
            nbr_items_to_display=nbr_items_to_display,
            index_count_mean_duration=index_count_mean_duration,
            no_index_count_mean_duration=no_index_count_mean_duration), f)
        print(f"Wrote {output_path_json}.")

    plt.xlabel("number of items skipped to arrive to given page")
    plt.ylabel("duration in seconds (less is better)")
    plt.title("costs of queries with pagination vs 'count' of whole query")


def run():

    if False:
        LD_sources = [  dict(path="benchmark_queries_and_counts_2_4_1e4.json",
                            nbr_users=2, nbr_clusters=4, N=1e4, Nstr="1e4", LD_data=[]),
                        dict(path="benchmark_queries_and_counts_2_4_1e5.json",
                            nbr_users=2, nbr_clusters=4, N=1e5, Nstr="1e5", LD_data=[])]
    else:
        LD_sources = [  dict(   path="benchmark_queries_and_counts_200_4_1e5.json", want_index=False,
                                nbr_users=200, nbr_clusters=4, N=1e5, label="1e5", LD_data=[]),
                        dict(   path="benchmark_queries_and_counts_200_4_1e6.json", want_index=False,
                                nbr_users=200, nbr_clusters=4, N=1e6, label="1e6", LD_data=[]),
                        dict(   path="benchmark_queries_and_counts_200_4_1e5i.json", want_index=True,
                                nbr_users=200, nbr_clusters=4, N=1e5, label="1e5i", LD_data=[]),
                        dict(   path="benchmark_queries_and_counts_200_4_1e6i.json", want_index=True,
                                nbr_users=200, nbr_clusters=4, N=1e6, label="1e6i", LD_data=[])]

    # start by loading the data from the json sources
    for D_source in LD_sources:
        with open(D_source["path"], "r") as f:
            D_source["LD_data"] = json.load(f)

    one_plot_index_vs_no_index(LD_sources[0], LD_sources[2],
        "benchmark_queries_and_counts_200_4_1e5.png",
        "benchmark_queries_and_counts_200_4_1e5.json")

    one_plot_index_vs_no_index(LD_sources[1], LD_sources[3],
        "benchmark_queries_and_counts_200_4_1e6.png",
        "benchmark_queries_and_counts_200_4_1e6.json")



if __name__ == "__main__":
    run()