
import pyslurm
from collections import defaultdict
import re

LD_nodes = pyslurm.node().get().values()

D_res_counts = defaultdict(list)

for D_node in LD_nodes:
    #
    D_res_counts['tmp_disk'].append(int(D_node['tmp_disk']))
    #
    matched_something = False
    # cpu=80,mem=386619M,billing=136,gres/gpu=8
    if m := re.match(r".*?cpu=(\d+).*?", D_node['tres_fmt_str']):
        D_res_counts['cpus'].append(int(m.group(1)))
        matched_something = True
    if m := re.match(r".*?mem=(\d+)M.*?", D_node['tres_fmt_str']):
        D_res_counts['mem_MB'].append(int(m.group(1)))
        matched_something = True
    if m := re.match(r".*?mem=(\d+)G.*?", D_node['tres_fmt_str']):
        D_res_counts['mem_MB'].append(int(m.group(1)) * 1000)
        matched_something = True
    if m := re.match(r".*?gpu=(\d+).*?", D_node['tres_fmt_str']):
        D_res_counts['gpus'].append(int(m.group(1)))
        matched_something = True
    #
    if not matched_something:
        print(f"Failed to match string : {D_node['tres_fmt_str']}")

for key in ['cpus', 'gpus', 'mem_MB', 'tmp_disk']:
    print(f"total {key}: {sum(D_res_counts[key])}")


total_cpus = sum(D_res_counts['cpus'])
total_gpus = sum(D_res_counts['gpus'])
total_mem_MB = sum(D_res_counts['mem_MB'])
total_mem_MB = sum(D_res_counts['tmp_disk'])

print(f"total_cpus: {total_cpus}")
print(f"total_gpus: {total_gpus}")
print(f"total_mem_MB: {total_mem_MB}")



D_states = defaultdict(int)
for D_node in LD_nodes:
    D_states[D_node['state']] += 1

{'DOWN*+DRAIN': 3,
'DOWN*': 9,
'MIXED': 53,
'RESERVED': 4,
'RESERVED+DRAIN': 1,
'ALLOCATED': 2}


# 480*20 + 15360*100 = 1.546 PB

"""
alaingui@login-2:~$ df -h
Filesystem                           Size  Used Avail Use% Mounted on
udev                                  12G     0   12G   0% /dev
tmpfs                                2.3G  5.9M  2.3G   1% /run
/dev/sda1                            196G   21G  166G  12% /
tmpfs                                 12G   56K   12G   1% /dev/shm
tmpfs                                5.0M     0  5.0M   0% /run/lock
/dev/sdb1                             40G   20G   18G  53% /tmp
beegfs_nodev                          59T   13T   46T  23% /miniscratch
beegfs_nodev                         146T   59T   88T  41% /home/mila
toubeau:/export/tmp                   84T   62T   23T  74% /network/tmp1
toubeau:/export/secure                23T  297G   23T   2% /network/sec1
cortex:/export/data/data2             57T   40T   17T  70% /network/data2
cortex:/export/data/datasets          80T   75T  6.0T  93% /network/datasets
cortex:/export/data/datasets/.data1   80T   75T  6.0T  93% /network/data1
cortex:/export/containers             17T  3.1G   17T   1% /network/containers
cortex:/export/data/projects          20T  2.2T   17T  12% /network/projects
"""
