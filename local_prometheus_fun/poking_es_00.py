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

    if False:
        response = client.search(
            index="slurm_jobs",
            body={
                "query": {
                    "bool": {
                        "must": [
                            {"range": {"end_time_str": {
                                        "gt": "2020-05-01",
                                        "lt": "2021-06-01"}}},
                            # {"match": {"cluster_name": "mila"}}
                            ]
                        #"must_not": [{"match": {"description": "beta"}}]
                    }
                }
            }
        )

    if False:
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
                        "end_time_str": { "gte": "2021-05-28 00:00:00", "lte": "2021-06-01 00:00:00"}
                    }
                }
            }

    response = client.search(
        index="slurm_jobs", body=body
    )


    for (n, hit) in enumerate(response['hits']['hits']):
        e = hit['_source']
        print(e['end_time_str'], e['cluster_name'])
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
        .query("match", account="mila")

    # .exclude("match", description="beta")
    # .filter("term", category="search")

    # s.aggs.bucket('per_tag', 'terms', field='tags') \
    #     .metric('max_lines', 'max', field='lines')

    response = s.execute()

    for (n, hit) in enumerate(response):
        print(hit)
        if 10 < n:
            break
        # print(hit.meta.score, hit.title)
    """
    <Hit(slurm_jobs/950006): {'account': 'mila', 'accrue_time': '2021-05-28T02:18:25', 'a...}>
    <Hit(slurm_jobs/950016): {'account': 'mila', 'accrue_time': '2021-05-28T02:26:48', 'a...}>
    <Hit(slurm_jobs/950018): {'account': 'mila', 'accrue_time': '2021-05-28T02:26:52', 'a...}>
    <Hit(slurm_jobs/950019): {'account': 'mila', 'accrue_time': '2021-05-28T02:26:54', 'a...}>
    <Hit(slurm_jobs/947157): {'account': 'mila', 'accrue_time': '2021-05-27T01:22:45', 'a...}>
    <Hit(slurm_jobs/950008): {'account': 'mila', 'accrue_time': '2021-05-28T02:18:29', 'a...}>
    <Hit(slurm_jobs/950009): {'account': 'mila', 'accrue_time': '2021-05-28T02:18:31', 'a...}>
    <Hit(slurm_jobs/950021): {'account': 'mila', 'accrue_time': '2021-05-28T02:26:57', 'a...}>
    <Hit(slurm_jobs/950000): {'account': 'mila', 'accrue_time': '2021-05-28T02:08:07', 'a...}>
    <Hit(slurm_jobs/948529): {'account': 'mila', 'accrue_time': '2021-05-27T03:08:54', 'a...}>
    """

    for (n, hit) in enumerate(response):
        print(hit)
        print(hit.account)
        if 10 < n:
            break

    #for tag in response.aggregations.per_tag.buckets:
    #    print(tag.key, tag.max_lines.value)


def main():
    # fun00()
    fun01()

if __name__ == "__main__":
    main()
