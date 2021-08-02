# Launching the Flask front-end locally for development purposes

This is a way to launch the web front-end from the "web_server" directory,
currently called "Clockwork Cluster", for development purposes.

At the current time, the code runs on Google Cloud with MongoDB Atlas,
but we suspect that this is not a tenable situation because of data usage,
especially if 500 students start using it.

The steps described in this file are for launching this server locally,
without authentication, and not for production. A production deployment
would probably involve nginx and gunicorn, or some other tools that do
the equivalent.

## launching flask

See "web_server/README.md" for steps on running this (outside of Docker).
