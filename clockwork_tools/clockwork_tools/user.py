from client import *
from job import *


client = ClockworkToolsClient(email= "student00@mila.quebec",
        clockwork_api_key = "000aaa00",
        host = "localhost",
        port = 15000)

print(client.search_jobs(job_id=190581))

