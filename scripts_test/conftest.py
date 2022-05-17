"""
This is a special file that pytest will find first.
"""

import pytest

import scripts
from scripts_test.config import register_config

register_config("mongo.connection_string", "")
register_config("mongo.database_name", "clockwork")
