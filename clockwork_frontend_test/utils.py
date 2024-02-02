import os

# Generate base url depending on whether we are inside docker container or not.
IN_DOCKER = os.environ.get("WE_ARE_IN_DOCKER", False)
BASE_URL = f"http://127.0.0.1:{5000 if IN_DOCKER else 15000}"
