from os import environ

from bottle import Bottle
from redis import Redis

__version__ = '0.0.5'
__author__ = 'Samuel Marks <@SamuelMarks>'

rest_api = Bottle(catchall=False, autojson=True)
redis = Redis(host=environ.get('REDIS_HOST', 'localhost'),
              port=int(environ.get('REDIS_PORT', 6379)),
              db=int(environ.get('REDIS_DB', 0)))
