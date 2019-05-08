from bottle import request, HTTPResponse

from glaucoma_analytics_rest_api import redis


def auth_needed(f):
    def inner(*args, **kwargs):
        token = request.get_header('X-Access-Token')
        if token is None or redis.get(token) is None:
            return HTTPResponse('Valid authentication required', 401)
        return f(*args, **kwargs)

    return inner
