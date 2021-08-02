# Setup with Docker Compose

Instead of starting the four services separately, we can start them all together with Docker Compose.

This does not cover the scraping because that requires a 

```bash
export UID=$(id -u ${USER})
export GID=$(id -g ${USER})

export MONGO_INITDB_ROOT_USERNAME="mongoadmin"
export MONGO_INITDB_ROOT_PASSWORD="secret_password_okay"

docker-compose up -d
```

## Making it secure.

- Update the Grafana configuration to have proper authentication instead of accepting admin/admin and not even require authentication.
- Update Prometheus configuration to have proper authentication.

| service | exposed ports |
|--|--|
| Prometheus | 9090 |
| ElasticSearch | 9200, 9300 |
| Grafana | 3000 |
| MongoDB | 27017 |