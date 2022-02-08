# Clockwork Tools python module

## Overview

Mainly a way to wrap up the REST API calls to "Clockwork Cluster" in a way
that doesn't require users to know about the details of the making such requests.
It's a python wrapper, plus a little more.

The main appeal of having such a library is that we can present a python module
to Mila members and they don't have to know anything else about Clockwork.
We can polish our interface, document it, make tutorials, notebooks, and
the complexity of the tool ends at the "clockwork_tools" python module for our users.

Thus, the Clockwork Tools python module does not get data directly from the
database, but sends requests to the REST API, as presented in the following scheme:

![Clockwork tools components](../docs/images/clockwork_tools_io.png)

## Structure

This repository presents two main files: `client.py` and `requirements.txt`.
They are quickly presented below:

| File | Use |
| -- | -- |
| client.py | Implements the Python interface in order to ease the use of Clockwork for Python developers |
| requirements.txt | Lists the Python requirements needed for this module to work |

## Technologies

* Docker
* Python
* See `requirements.txt`.
