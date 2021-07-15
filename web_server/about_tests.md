
In order for tests to run, they need to be able to connect to an instance of mongodb.
This is usually a local instance launched for the purpose of development and testing.

In a context in which the tests are run inside a Docker instance, the database will
also run in an instance of mongodb in its own container (the whole thing probably
launched by a Docker Compose file).

```
export MONGODB_CONNECTION_STRING='mongodb://mongoadmin:secret_password_okay@deepgroove.local:27017/?authSource=admin&readPreference=primary&retryWrites=true&w=majority&tlsAllowInvalidCertificates=true&ssl=false'

export MONGODB_DATABASE_NAME="clockwork_testing"
cd ${HOME}/Documents/code/slurm_monitoring_and_reporting_refactor/web_server

pytest
```


export PYTHONPATH=${PYTHONPATH}:${HOME}/Documents/code/slurm_monitoring_and_reporting_refactor



## temporary

export MONGODB_CONNECTION_STRING='mongodb://mongoadmin:secret_password_okay@deepgroove.local:27017/?authSource=admin&readPreference=primary&retryWrites=true&w=majority&tlsAllowInvalidCertificates=true&ssl=false'
