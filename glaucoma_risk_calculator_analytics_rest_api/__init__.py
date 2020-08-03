# coding: utf-8

from os import environ

from bottle import Bottle
from redis import Redis

__author__ = "Samuel Marks <@SamuelMarks>"
__version__ = "0.0.21"

environ["RDBMS_URI"] = environ["RDBMS_URI"].replace("postgres://", "postgresql://")

rest_api = Bottle(catchall=True, autojson=True)
redis = Redis(
    host=environ.get("REDIS_HOST", "localhost"),
    port=int(environ.get("REDIS_PORT", 6379)),
    db=int(environ.get("REDIS_DB", 0)),
)
is_test = bool(environ.get("TEST_MODE", False))
