
import json
import re

with open("job.json", "r") as f:
    E = json.load(f)

accounts = list(set(v['account'] for v in E.values()))
print(accounts)

print("")
print("Accounts with .*bengio.* :")

for a in accounts:
    if re.match(r".*bengio.*", a):
        print(a)
