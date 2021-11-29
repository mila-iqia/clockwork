# Clockwork User Guide

The service is hosted at Mila and accessible to everyone that can authenticate
with their @mila.quebec account.

The web front-end is accessible at https://clockwork.mila.quebec 
and everything can be done also through a REST API.
There is a `clockwork_tools` python module that can be used to access the REST API
without having to think about any implementation details.

Mila members can thus simply use the `clockwork_tools` in their python scripts
and ignore the web site (beyond the initial authentication to get the API key).

## clusters

The main information found online is about jobs running on the Mila cluster as well as the Compute Canada clusters.

The information is refreshed with a frequency determined with the administrators
of the clusters.

|cluster| refresh frequency |
|-------|-------------------|
| Mila cluster | every minute |
| beluga, cedar, graham | every 10 minutes |

[todo : expand this section]

## notebooks

[TODO : Section on Jupyter Notebooks with ]

## information on hardware

The REST API exposes specs for the hardware installed on the clusters.
This gives users quick access to basic back-of-the-envelope estimates
about the hardware available. For example, we can estimate how many teraflops
of FP32 we have for all our GPUs.

There are also methods to expose some of the storage quotas on filesystems
to allow Mila members to see if they are going to run out of space.
That information is also available online at [docs.mila.quebec](https://docs.mila.quebec)
but we exposed it through a programmatic interface through Clockwork's REST API.

[TODO : Expand.]

## people

The REST API also exposes information that's available publicly
on the Mila web site in a way that's more convenient for python users.

[TODO : Expand.]

