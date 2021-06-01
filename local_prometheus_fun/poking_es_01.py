import re
import os

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

def fun01():

    client = Elasticsearch(
        "http://deepgroove.local",
        port=9200
    )

    """
    'timestamp': '2021-05-28T07:24:57.127902',
    'submit_time_str': '2021-05-27 03:08:47',
    'start_time_str': '2021-05-27 21:06:27',
    'end_time_str': '2021-05-28 09:05:27',
    'eligible_time_str': '2021-05-27 03:08:54'
    """

    body={
            "query": {
                "filtered": {
                    "query": {
                        "bool": {
                            "must": [{"match": {"title": "python"}}],
                            "must_not": [{"match": {"description": "beta"}}]
                        }
                    },
                    "filter": {"term": {"category": "search"}}
                }
            }
        }

    if True:
        body={
               "query": {
                    "range": {
                        # "timestamp": { "gte": "2021-05-30T00:00:00", "lte": "2021-06-01T00:00:00"}
                        "timestamp": { "gte": "2021-06-01T06:00:00", "lte": "2021-06-01T23:00:00"}
                    }
                }
            }

    response = client.search(
        index="slurm_jobs", body=body
    )


    for (n, hit) in enumerate(response['hits']['hits']):
        e = hit['_source']
        print((e['end_time_str'], e['timestamp'], e['cluster_name']))
        # print(hit['timestamp'])
        if 20 < n:
            break



def fun00():

    # if you DARE passing that host argument with a keyword host="http://deepgroove.local"
    # this thing won't work
    client = Elasticsearch(
        "http://deepgroove.local",
        port=9200
    )

    s = Search(using=client, index="slurm_jobs") \
        .query("match", cluster_name="mila")

    # .exclude("match", description="beta")
    # .filter("term", category="search")

    # s.aggs.bucket('per_tag', 'terms', field='tags') \
    #     .metric('max_lines', 'max', field='lines')

    response = s.execute()

    for (n, hit) in enumerate(response):
        print((hit.cluster_name, hit.account, hit.mila_user_account))
        # print((hit.gpus))
        # if 100 < n:
        #     break
        # print(hit.meta.score, hit.title)

    s = Search(using=client, index="slurm_jobs") \
        .query("match", cluster_name="beluga")
    response = s.execute()
    for (n, hit) in enumerate(response):
        print((hit.cluster_name, hit.account, hit.mila_user_account))
        #if 100 < n:
        #    break        
    """

    """

    #for tag in response.aggregations.per_tag.buckets:
    #    print(tag.key, tag.max_lines.value)


def main():
    fun00()
    # fun01()

if __name__ == "__main__":
    main()
