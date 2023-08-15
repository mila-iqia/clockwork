import json

#Classe pour stocker les informations d'un Node
class Node:
    def __init__(self,data):
        json_str = json.dumps(data) # Formatting a dict to json valid string
        self.json_data = json.loads(json_str) # Formatting a json string to a json object
        cw_json = self.json_data.get("cw")
        slurm_json = self.json_data.get("slurm")

        self.addr = slurm_json.get("addr")
        self.cluster_name = slurm_json.get("cluster_name")
        self.comment = slurm_json.get("comment")
        self.features = slurm_json.get("features")
        self.name = slurm_json.get("name")
        self.state = slurm_json.get("state")

        self.gres = slurm_json.get("gres")    
        self.memory = slurm_json.get("memory")

        self.alloc_tres = slurm_json.get("alloc_tres")
        self.arch = slurm_json.get("arch")
        self.cfg_tres = slurm_json.get("cfg_tres")
    
        self.cw_last_update = cw_json.get("last_slurm_update")
        self.gpu = cw_json.get("gpu")
    
    def to_json(self):
        return self.json_data
    
    def __str__(self):
        return json.dumps(self.json_data, indent=4)
    



