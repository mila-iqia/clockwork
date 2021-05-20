

```bash
# add entry to config, with "mila-api-boilerworks" being the github repo
cat >> ~/.ssh/config
Host github-slurm_monitoring_and_reporting
    Hostname github.com
    IdentityFile ~/.ssh/github_keys/slurm_monitoring_and_reporting-id_rsa
	
# in case it didn't exist beforehand, give it the right permissions
chmod 644 ~/.ssh/config
```

## create key pair
```bash
ssh-keygen -f ~/.ssh/github_keys/slurm_monitoring_and_reporting-id_rsa -t ecdsa -b 521

# make sure permissions are right
chmod -R 644 ~/.ssh/github_keys/*id_rsa.pub
chmod -R 600 ~/.ssh/github_keys/*id_rsa

# checkout the code locally
git clone git@github-slurm_monitoring_and_reporting:gyom/slurm_monitoring_and_reporting.git
```