from client import *

client = ClockworkToolsClient(email= "student00@mila.quebec",
        clockwork_api_key = "000aaa00",
        host = "localhost",
        port = 15000)


print(client.nodes_list(cluster_name='graham'))#[1]["cw"]['job_state'])
print("Welcome to Clockwork Tools!")
