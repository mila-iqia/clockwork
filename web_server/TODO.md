
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