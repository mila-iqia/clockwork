# Setup with Docker Compose

Instead of starting the four services separately, we can start them all together with Docker Compose.

This does not cover the scraping because that requires a 

```bash
export UID=$(id -u ${USER})
export GID=$(id -g ${USER})

export MONGO_INITDB_ROOT_USERNAME="mongoadmin"
export MONGO_INITDB_ROOT_PASSWORD="secret_password_okay"

# export CLOCKWORK_TASK="clockwork_run_web_development"
export CLOCKWORK_TASK="clockwork_run_web_unit_tests"

docker-compose up -d
```

## Different tasks

We want to be able to use the same setup in order to run unit tests, so we need to way to
tell the scripts if they should start the web server in development mode, or if they
should only run tests.

This is done by setting an environment variable CLOCKWORK_TASK.

```bash
# To run the tests present in "web_server", which requires a database
# but no real data nor any scraping. This terminates after running
# the tests and does not stay up to serve more HTTP requests.
# The web server is in debug mode and logins are disabled.
export CLOCKWORK_TASK="clockwork_run_web_unit_tests"

# Starts the web server in debug mode and logins are disabled.
# This is for development.
export CLOCKWORK_TASK="clockwork_run_web_development"

# Start the web server in production mode with gunicorn front,
# with HTTPS and logins required. This is impossible to use for
# local development because you need to have DNS redirection,
# as well an nginx running on the production machine with TLS
# properly set up.
export CLOCKWORK_TASK="clockwork_run_web_production"
```

We're not sure at the moment what is the best way to run the tests
for the scrapers. It might be the case that we should define a separate
Docker Compose file in order to run only the scraper, but then we have
to decide if
   - we run unit tests on fake data
   - we run unit tests that test the scraping on real clusters
This will probably become clearer as the pieces are assembled.


## Making it secure

- Update the Grafana configuration to have proper authentication instead of accepting admin/admin and not even require authentication.
- Update Prometheus configuration to have proper authentication.

| service | exposed ports |
|--|--|
| Prometheus | 9090 |
| ElasticSearch | 9200, 9300 |
| Grafana | 3000 |
| MongoDB | 27017 |

## Debugging

Here's a hint. You can replace the command for any service with something like `command: sh -c "sleep 43897423"`.
Then you can attach to that server with `docker-compose exec web_server bash` and run whatever you like.

You can start a service in isolation by calling `docker-compose up -d web_server` if you don't want everything to come along with it.

## etc

