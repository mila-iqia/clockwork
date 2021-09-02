# Clockwork User Guide

The service is hosted at Mila and accessible to everyone that can authenticate
with their @mila.quebec account.

The web front-end is accessible at https://clockwork.mila.quebec 
and everything can be done also through a REST API.
There is a `mila_tools` python module that can be used to access the REST API
without having to think about any implementation details.

Mila members can thus simply use the `mila_tools` in their python scripts
and ignore the web site (beyond the initial authentication to get the API key).

## clusters

The main information found online is about jobs running on the Mila cluster as well as the Compute Canada clusters.

The information is refreshed with a frequency determined with the administrators
of the clusters.

|cluster| refresh frequency |
|-------|-------------------|
| Mila cluster | every minute |
| beluga, cedar, graham | every 10 minutes |


## people

The REST API also exposes information that's available publicly
on the Mila web site in a way that's more convenient for python users.

[stub]