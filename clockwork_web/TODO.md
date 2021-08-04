
Figure out a strategy to have the web server use a mongodb server specified by config.
We'll use environment variables for that. We'll read the same from google app
than from the version running inside of a local Docker.

Visit Atlas to make sure that everything is setup nicely.

Adapt the user.py file (among other things, to avoid mentioning "biblioplex").

make the main server use authentication

---

Later on we might want to rename things instead of using "web_server" and "scraper_slurm".
I don't want to write "clockwork_cluster" in so many places before I know if it's the name
of the project, or the name of the web server.

This looks a bit clumsy, although it's not too bad:

    clockwork_cluster (project) --- clockwork_cluster (python module)
                                --- scraper_slurm     (python module)

---

When provisionning the database, you'll need to have the nested structure:
    clockwork (collection)  -- users (collection)
                            -- jobs  (collection)
                            -- nodes (collection)

---

We need a better-principled system for logging. Right now it's a bunch of print
statements used mostly for tracking the state of the program for debugging.
This is not all that useful in the context of a production app.

---

When the server fails to query the database, the interface should give some
kind of feedback to the user to let them know (as developer) that the
database was unreachable. This is especially important when we run in Docker Compose
and we can't easily see the stdout of flask.