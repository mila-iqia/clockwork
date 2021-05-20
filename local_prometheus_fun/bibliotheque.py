
import time
import numpy as np
from prometheus_client import start_http_server
from prometheus_client import Summary


def process_request(prom_metrics):
    prom_metrics['request_latency_seconds'].observe(np.random.randn())


def run():
    port = 19997
    prom_metrics = {'request_latency_seconds': Summary('request_latency_seconds', 'Description of summary')}

    start_http_server(port)
    while True:
        process_request(prom_metrics)
        time.sleep(1)

if __name__ == "__main__":
    run()
