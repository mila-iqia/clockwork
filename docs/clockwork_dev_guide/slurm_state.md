# Obtaining the state of the remote clusters

## mapping of slurm fields

TODO : describe some of the decisions about mapping states from "raw_sacct" to "sacct".

## some MongoSH commands

When you want to wipe out the contents of a collection (e.g. "jobs")
but not remove an associated "index" that has been configured,
you can use the MongoSH terminal inside MongoDB Compass.
```
use clockwork
db.jobs.deleteMany({})
```
