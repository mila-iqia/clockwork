
We need a better-principled system for logging. Right now it's a bunch of print
statements used mostly for tracking the state of the program for debugging.
This is not all that useful in the context of a production app.

---

When the server fails to query the database, the interface should give some
kind of feedback to the user to let them know (as developer) that the
database was unreachable. This is especially important when we run in Docker Compose
and we can't easily see the stdout of flask.

---




