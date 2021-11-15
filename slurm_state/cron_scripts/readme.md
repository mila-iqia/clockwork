# setup for slurm reports

These are generated automatically by Compute Canada,
but we generate them for the mila cluster using the same recipe.

We call `generate_clusterstats_cache.sh` as a cron job
with user `mila-automation@blink`.
The output is put in `blink:~mila-automation/slurm_reports/mila`.
The script itself is in the `slurm_reports` directory on `blink`.

Also as cron job for `mila-automation@blink`, we rsync the reports
from three Compute Canada clusters into the following directories:
- `~mila-automation/slurm_reports/beluga`
- `~mila-automation/slurm_reports/cedar`
- `~mila-automation/slurm_reports/graham`

This is done by cron calling the three following commands.
Note the different paths based on decisions made by people at CC.
- `rsync -av mila-automation@beluga.computecanada.ca:/lustre04/cc/slurm/* ${HOME}/slurm_report/beluga`
- `rsync -av mila-automation@cedar.computecanada.ca:/project/cc/slurm/* ${HOME}/slurm_report/cedar`
- `rsync -av mila-automation@graham.computecanada.ca:/opt/software/slurm/clusterstats_cache/* ${HOME}/slurm_report/graham`


## the crontab file for mila-automation@blink

```bash
#SHELL=/bin/bash
PATH = $PATH:/opt/slurm/bin:/usr/bin

# Every 5 minutes, run the slurm report.
# Note that this can't find the slurm commands if we don't ajust the PATH beforehands.
*/5 * * * * ${HOME}/slurm_report/generate_clusterstats_cache.sh > ${HOME}/slurm_report/mila/cron_stdout_and_stderr.log 2>&1


# Every 30 minutes, rsync from the CC clusters.
# We should probably want to do this every 10 minutes (and convince CC to run their thing every 5 minutes eventually),
# but for now there is no reason to be aggressive about our rsync.
# The `timeout 120` is there to prevent this command from getting stuck if it cannot
# reach the host, or if it is stuck at the "do you accept the fingerprint?" question
# because we somehow failed to do it manually one time before, as required to accept the fingerprint.
*/30 * * * * timeout 120 rsync -av mila-automation@beluga.computecanada.ca:/lustre04/cc/slurm/* ${HOME}/slurm_report/beluga > ${HOME}/slurm_report/beluga/cron_stdout_and_stderr.log 2>&1
*/30 * * * * timeout 120 rsync -av mila-automation@cedar.computecanada.ca:/project/cc/slurm/* ${HOME}/slurm_report/cedar > ${HOME}/slurm_report/cedar/cron_stdout_and_stderr.log 2>&1
*/30 * * * * timeout 120 rsync -av mila-automation@graham.computecanada.ca:/opt/software/slurm/clusterstats_cache/* ${HOME}/slurm_report/graham > ${HOME}/slurm_report/graham/cron_stdout_and_stderr.log 2>&1
```