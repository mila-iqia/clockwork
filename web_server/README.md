# Clockwork cluster web server

## How to deply to Google Cloud

Create `app.yaml` from `missing_secrets_app.yaml`.
Put the missing secrets in there, pertaining to Atlas Mongodb and OAuth.

```bash
gcloud app deploy gcloud_app.yaml
```

## How to run locally (no authentication)

You can run this with your own python environment, either with
your own instance of a mongodb server, or with the same one
on Atlas that the Google Cloud deployment uses.

```bash

```

## How to run at Mila (with authentication)

This is work in progress.

- set up DNS server
- set up nginx
- set up Google authentication stuff
- make decisions about your mongodb instance
- make decisions about using Docker compose, running directly in the virtual machine, or maybe even having a Kubernetes setup