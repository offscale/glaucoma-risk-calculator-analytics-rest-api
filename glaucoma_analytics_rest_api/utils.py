from datetime import datetime
from platform import python_version_tuple

from bottle import request, HTTPResponse

from glaucoma_analytics_rest_api import redis


def auth_needed(f):
    def inner(*args, **kwargs):
        token = request.get_header('X-Access-Token')
        if token is None or redis.get(token) is None:
            return HTTPResponse('Valid authentication required', 401)
        return f(*args, **kwargs)

    return inner


PY3 = python_version_tuple()[0] == '3'


def to_datetime_tz(dt):  # type: (str) -> datetime
    fmt = '%Y-%m-%dT%H:%M:%S.%f'
    if dt[-6] in frozenset(('+', '-')):
        return datetime.strptime(dt, fmt + '%z')
    elif dt[-1] == 'Z':
        return datetime.strptime(dt, fmt + 'Z')
    return datetime.strptime(dt, fmt)
