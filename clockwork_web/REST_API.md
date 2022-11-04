
browser_routes/jobs.py
        /jobs/list?cluster_name=mila&username=guillaume.alain&time=3600
        /jobs/one?cluster_name=beluga&job_id=100000
browser_routes/nodes.py
        /nodes/list?cluster_name=mila&name=cn-a003
        /nodes/one?cluster_name=mila&name=cn-a003   [TODO]

rest_routes/jobs.py
        /api/v1/clusters/jobs/list?cluster_name=beluga&username=guillaume.alain&time=3600
        /api/v1/clusters/jobs/one?cluster_name=beluga&job_id=100000
rest_routes/nodes.py
        /api/v1/clusters/nodes/list?cluster_name=mila
        /api/v1/clusters/nodes/one?node_name=cn-a003