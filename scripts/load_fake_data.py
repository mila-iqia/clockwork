"""
During the web development, we sometimes require some kind of data in 
the database in order to see how the GUI reacts, how items are displayed.

While "fake_data.json" is loaded automatically with the tests,
it is not the case when we load only the web server. This script exists
to remedy that problem, to be called manually by the user after starting
the web server with a command such as "flask run --host=0.0.0.0"
running in the "clockwork_dev" container.
"""


import os
import sys
import argparse

from pymongo import MongoClient
from test_common.fake_data import populate_fake_data


def main(argv):

    my_parser = argparse.ArgumentParser()
    my_parser.add_argument("--fake_data", type=str, default=None)
    my_parser.add_argument('--clear', action='store_true', help='Clear corresponding data instead of loading it.')

    args = my_parser.parse_args(argv[1:])
    print(args)

    assert os.environ["MONGODB_CONNECTION_STRING"]
    assert os.environ["MONGODB_DATABASE_NAME"]
    assert args.fake_data

    db = MongoClient(os.environ["MONGODB_CONNECTION_STRING"])
    cleanup_function = populate_fake_data(db[os.environ["MONGODB_DATABASE_NAME"]])
    print(f"Loaded data in database from {args.fake_data}.")

    # The minimalistic way (in terms of loc) to clear out the fake_data
    # is just to insert it and then call the cleanup_function.
    if args.clear:
        cleanup_function()
        print("Cleared out the data from the database.")

if __name__ == "__main__":
    main(sys.argv)

"""
python3 /clockwork/scripts/load_fake_data.py --fake_data=/clockwork/test_common/fake_data.py

"""