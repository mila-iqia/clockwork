
# rules for queries in mongodb

## which timestamp to use

The web page will talk to the REST API and supply an argument
`query_filter` that looks like the following:
```
    {'time': 3600, 'user': 'all'}
```

We need to be able to translate that into an argument for mongodb
to filter out values in a query. For example, if we went for
```
    {'submit_time': {'$gt': int(time.time() - query_filter['time'])}}
```
this would be problematic because of the fact that 'submit_time' is
not the most relevant timestamp to use.

Let us say for a moment that the 'time' is 3600, which corresponds to an hour.
Jobs that have completed in the past hour are interesting, no matter when
they were submitted. Jobs that are currently queued are also interesting, no matter
when they were submitted.

Job that are not currently running have 'start_time' equal to 0.
Job that are not finished have 'end_time' equal to 0.

All jobs have the following fields : submit_time, eligible_time, start_time, end_time.

It appears that every job that's "CANCELLED" has a start time. This assumption should be verified
for cases when a job is queued and then cancelled before it has a chance to start.

## the answer

We decided to use the following rule based on 'end_time'.
When 'end_time' is 0, we always return the job.
Otherwise, we made a comparison to make see if 'end_time'
falls within the scope of the time specified by the user.

## what this means for mongodb

```python
{'$or' : [  {'end_time': {'$gt': int(time.time() - query_filter['time'])}},
            {'end_time': 0}]
}
```

## note about `cedar`

We currently cannot run `pyslurm` on `cedar`, but are instead parsing the outputs of `sacct` and `sinfo`.
This means that we are more limited in the information that we can store in the database.
Despite that, we have the same fields : submit_time, eligible_time, start_time, end_time.

Those are unix timestamps as integer values, and they follow the same rules as described above
when it comes to being set to 0 to represent a missing value.

## about usernames

There are three kinds of accounts that are relevant in our ecosystem.
We try to include them in the following fields:

- mila_cluster_username
- cc_account_username
- mila_email_username

In the meantime we have "mila_user_account" being used. This isn't great,
but let's at least support it for the time being.

When `query_filter` has the field "user", we are going to ignore it if
- it's "all", or
- it's the empty string "", or
- it's "*".

Otherwise, we will try to match that "user" value against all of the four
fields "mila_cluster_username", "cc_account_username", "mila_email_username",
"mila_user_account", provided they exist. The nice thing about it is that
we don't need to test for the presence of the fields using '$exists', because
we're using an OR clause with the four tests.

## what this means for mongodb

```python
{'$or': [   {'mila_cluster_username': user}, 
            {'cc_account_username': user}, 
            {'mila_email_username': user}, 
            {'mila_user_account': user}
]}
```
