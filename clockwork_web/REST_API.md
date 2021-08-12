
Je pense que je devrais mettre "/jobs" menant à la longue liste (avec arguments possibles) et pas l'index interactif.
L'index interactif ça pourrait être "/", et là je ne sais pas si je voudrais donner des arguments possibles.



browser_routes/nodes.py
        /nodes/list?cluster_name=mila&name=cn-a003
        /nodes/one?cluster_name=mila&name=cn-a003   [TODO]

browser_routes/jobs.py
        /jobs/list?cluster_name=mila&user=guillaume.alain&time=3600
        /jobs/one?cluster_name=beluga&job_id=100000   [TODO]

rest_routes/jobs.py
        /api/v1/clusters/jobs/list?cluster_name=beluga&user=guillaume.alain&time=3600
        /api/v1/clusters/jobs/one?cluster_name=beluga&job_id=100000   [TODO]
rest_routes/nodes.py
        /api/v1/clusters/nodes/list?cluster_name=mila
        /api/v1/clusters/nodes/one?name=cn-a003   [TODO]