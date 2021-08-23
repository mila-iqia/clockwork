
# Single-repo SSH keys

So, this note is a bit strange because I set up the repo and keys
before renaming it and giving it to "mila-iqia".
This makes these setup instructions useful in general,
but somewhat useless on the computers where my repo is currently checked out.

## setup config

```bash
# add entry to config, with "clockwork" being the github repo
cat >> ~/.ssh/config
Host github-clockwork
    Hostname github.com
    IdentityFile ~/.ssh/github_keys/clockwork-id_rsa
	
# in case it didn't exist beforehand, give it the right permissions
chmod 644 ~/.ssh/config
```

## create key pair
```bash
ssh-keygen -f ~/.ssh/github_keys/clockwork-id_rsa -t ecdsa -b 521

# make sure permissions are right
chmod -R 644 ~/.ssh/github_keys/*id_rsa.pub
chmod -R 600 ~/.ssh/github_keys/*id_rsa

# checkout the code locally
git clone git@github-clockwork:mila-iqia/clockwork.git
```