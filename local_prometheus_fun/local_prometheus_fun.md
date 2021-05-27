# Running prometheus locally to try out things without corrupting the server at Mila

```
docker run --rm \
    -p 9090:9090 \
    --add-host=host.docker.internal:host-gateway \
    -v ${HOME}/Documents/code/slurm_monitoring_and_reporting/local_prometheus_fun/prometheus.yml:/etc/prometheus/prometheus.yml \
    prom/prometheus
```

This is configured to fetch from `http://localhost:19997/books` and `http://localhost:19998/metrics`.

The goal is in part to find out how to use PromQL, to list the data available, to see what the requests look like.

Note that the `--add-host=host.docker.internal:host-gateway` line is to allow prometheus to 
connect to a script like `bibliotheque.py` that's running on the same machine but not inside
of a Docker container. This line comes from https://djangocas.dev/blog/docker-container-to-connect-localhost-of-host/#docker-for-linux, it runs on Linux, and they suggest variations for MacOS.

## Adding Grafana

https://grafana.com/docs/grafana/latest/installation/docker/

```bash
docker run --rm \
    -p 3000:3000 \
    --add-host=host.docker.internal:host-gateway \
    grafana/grafana:latest
# docker run -d -p 3000:3000
```

Let's make it persistent and then we can go in there to edit the config file `/etc/grafana/grafana.ini` manually.

```bash
ID=$(id -u)
docker run -d \
    -p 3000:3000 \
    --add-host=host.docker.internal:host-gateway \
    --user $ID \
    --name my_grafana \
    --volume "${HOME}/Documents/code/slurm_monitoring_and_reporting/mist/grafana_data:/var/lib/grafana" \
    grafana/grafana:latest-ubuntu
# 1f7cc20919c9
```

```bash
# get into that machine as its "root" to install emacs
# and to edit the configuration file
docker exec --user root -it 1f7cc20919c9 bash

# then you can get into it as a normal user
docker exec -it 1f7cc20919c9 bash
```

```
;disable_initial_admin_creation = false                                                                                           
                                                                                                                                  
# default admin user, created on startup                                                                                          
admin_user = admin                                                                                                                
                                                                                                                                  
# default admin password, can be changed before first start of grafana,  or in profile settings                                   
admin_password = admin                                                                                                            
                                                                                                                                  
# used for signing                                                                                                                
;secret_key = SW2YcwTIb9zpOOhoPsMm 
# disable user signup / registration                                                                                              
allow_sign_up = true
# enable anonymous access                                                                                                         
enabled = true




```

## data source dans grafana

Mon container pour prometheus roule sur deepgroove. Mon container pour grafana aussi.
Pourtant, je ne pouvais pas ajouter localhost:9090 ni deepgroove.local:9090 comme data source.
Obtenu une bonne valeur en utilisant `http://172.17.0.2:9090` à partir des commandes suivantes:

```bash
docker ps

CONTAINER ID   IMAGE                           COMMAND                  CREATED          STATUS          PORTS                                       NAMES
1f7cc20919c9   grafana/grafana:latest-ubuntu   "/run.sh"                20 minutes ago   Up 11 minutes   0.0.0.0:3000->3000/tcp, :::3000->3000/tcp   my_grafana
5dd517900823   prom/prometheus                 "/bin/prometheus --c…"   6 days ago       Up 6 days       0.0.0.0:9090->9090/tcp, :::9090->9090/tcp   unruffled_chebyshev

docker inspect 5dd517900823

            "Networks": {
                "bridge": {
                    "IPAMConfig": null,
                    "Links": null,
                    "Aliases": null,
                    "NetworkID": "7d7bf5d0666cf98d67c68804acb91b9a971c8a441b962c50bf7213084a0a41ee",
                    "EndpointID": "f02d88123de4417ae689474d42a2f1df9299ab5ae3c77664ac7b9dcd4b1ab622",
                    "Gateway": "172.17.0.1",
                    "IPAddress": "172.17.0.2",
                    "IPPrefixLen": 16,
                    "IPv6Gateway": "",
                    "GlobalIPv6Address": "",
                    "GlobalIPv6PrefixLen": 0,
                    "MacAddress": "02:42:ac:11:00:02",
                    "DriverOpts": null
                }
            }


```

