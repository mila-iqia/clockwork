
import re
import json
from pprint import pprint

from collections import defaultdict

def main():

    # Account|UID|JobID|JobName|State|Start|End|

    with open("sacct_beluga.txt", "r") as f:
        L_lines = f.readlines()

    LD = []
    header = L_lines[0][:-1].split("|")
    for line in L_lines[1:]:
        line = line.replace("\n", "")
        if not line:
            continue
        assert line[-1] == "|", (line[-1], line)
        tokens = line[:-1].split("|")

        D = dict(zip(header, tokens))
        if D['UID']:
            LD.append(D)

    count_running = sum(1 for D in LD if D['State'] == 'RUNNING')
    count_in_time_interval = sum(1 for D in LD if (D['Start'] != 'Unknown' and D['End'] == 'Unknown'))

    print(count_running)
    print(count_in_time_interval)

    # 94
    # 94

    ##################
    ## sort by who has more jobs running

    def f(state):

        DLD_user_to_jobs = defaultdict(list)

        for D in LD:
            if D['State'] == state:
                DLD_user_to_jobs[D['UID']].append( D )

        LP_LD_user_to_jobs = sorted( DLD_user_to_jobs.items(), key=lambda P: -len(P[1]) )

        for (uid, LD_single_user_jobs) in LP_LD_user_to_jobs:
            print( (uid, len(LD_single_user_jobs)))

    print("jobs RUNNING")
    f("RUNNING")

    """
        jobs RUNNING
        ('3060080', 34)
        ('3065065', 14)
        ('3063744', 12)
        ('3095176', 10)
        ('3074329', 4)
        ('3074726', 4)
        ('3100539', 3)
        ('3079272', 3)
        ('3103500', 3)
        ('3100560', 2)
        ('3093349', 1)
        ('3078412', 1)
        ('3087405', 1)
        ('3062564', 1)
        ('3079410', 1)
    """

    ##################
    ## sort by who has more jobs PENDING

    print("jobs PENDING")
    f("PENDING")

    """
        jobs PENDING
        ('3079272', 26)
        ('3090897', 3)
        ('3083913', 2)
        ('3093349', 1)
    """

if __name__ == "__main__":
    main()
