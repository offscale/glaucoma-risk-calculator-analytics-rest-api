# coding: utf-8

from datetime import datetime
from json import dumps
from platform import python_version_tuple
from pprint import PrettyPrinter

from bottle import request, HTTPResponse

from glaucoma_risk_calculator_analytics_rest_api import is_test, redis

pp = PrettyPrinter(indent=4).pprint


def auth_needed(f):
    def inner(*args, **kwargs):
        token = request.get_header("X-Access-Token")
        # print('Got access token of', token, 'on endpoint', request.url, file=stderr)
        if (token is None or redis.get(token) is None) and not is_test:
            return HTTPResponse(
                body=dumps(
                    {
                        "error": "AuthError",
                        "error_message": "Valid authentication required",
                    }
                ),
                status=401,
                headers={"Content-type": "application/json"},
            )
        return f(*args, **kwargs)

    return inner


PY3 = python_version_tuple()[0] == "3"


def to_datetime_tz(dt):  # type: (str) -> datetime
    fmt = "%Y-%m-%dT%H:%M:%S.%f"
    if dt[-6] in frozenset(("+", "-")):
        return datetime.strptime(dt, fmt + "%z")
    elif dt[-1] == "Z":
        return datetime.strptime(dt, fmt + "Z")
    return datetime.strptime(dt, fmt)


def update_d(d, arg=None, **kwargs):
    if arg:
        d.update(arg)
    if kwargs:
        d.update(kwargs)
    return d


def maybe_to_dict(obj, to_dict):
    return obj.to_dict() if to_dict else obj
