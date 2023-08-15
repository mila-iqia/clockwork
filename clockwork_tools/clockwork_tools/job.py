import json

#Classe pour stocker les informations d'une job
class Job:
    def __init__(self,data):
        json_str = json.dumps(data) # Formatting a dict to json valid string
        self.json_data = json.loads(json_str) # Formatting a json string to a json object
        cw_json = self.json_data.get("cw")
        slurm_json = self.json_data.get("slurm")

        self.mila_email = cw_json.get("mila_email_username")
        self.job_id = slurm_json.get("job_id")
        self.job_state = slurm_json.get("job_state")
        self.name = slurm_json.get("name")
        self.account = slurm_json.get("account")
        self.uid = slurm_json.get("uid")
        self.username = slurm_json.get("username")

        self.TRES = slurm_json.get("TRES")    
        self.command = slurm_json.get("command")
        self.cpus_per_task = slurm_json.get("cpus_per_task")
        self.work_dir = slurm_json.get("work_dir")
        self.exit_code = slurm_json.get("exit_code")
        self.partition = slurm_json.get("partition")
        
        self.nodes = slurm_json.get("nodes")
        self.num_cpus = slurm_json.get("num_cpus")
        self.num_nodes = slurm_json.get("num_nodes")
        self.num_tasks = slurm_json.get("num_tasks")
        
        self.cw_last_update = cw_json.get("last_slurm_update")
        self.start_time = slurm_json.get("start_time")
        self.end_time = slurm_json.get("end_time")
        self.submit_time = slurm_json.get("submit_time")
        self.time_limit = slurm_json.get("time_limit")

        self.stderr = slurm_json.get("stderr")
        self.stdin = slurm_json.get("stdin")
        self.stdout = slurm_json.get("stdout")
    
    def to_json(self):
        return self.json_data
    
    def __str__(self):
        return json.dumps(self.json_data, indent=4)
    



