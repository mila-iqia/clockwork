import json, os
from datetime import datetime

# Generate base url depending on whether we are inside docker container or not.
IN_DOCKER = os.environ.get("WE_ARE_IN_DOCKER", False)
BASE_URL = f"http://127.0.0.1:{5000 if IN_DOCKER else 15000}"


def get_fake_data():
    # Retrieve the fake data content
    with open("test_common/fake_data.json", "r") as infile:
        return json.load(infile)

def get_default_display_date(input_date):
    if input_date == None:
        return ""
    elif input_date == 0:
        # If the timestamp is 0, does not display a time
        return ""
    else:
        return datetime.fromtimestamp(input_date).strftime("%Y/%m/%d %H:%M") # The format is YYYY/MM/DD hh:mm