

python3 -c "import pyslurm; import json; print(json.dumps(pyslurm.node().get()))" | python3 -m json.tool > node.json
python3 -c "import pyslurm; import json; print(json.dumps(pyslurm.job().get()))" | python3 -m json.tool > job.json
python3 -c "import pyslurm; import json; print(json.dumps(pyslurm.reservation().get()))" | python3 -m json.tool > reservation.json

# python3 -c "import pyslurm; import json; print(json.dumps(pyslurm.hostlist()))" | python3 -m json.tool > hostlist.json
