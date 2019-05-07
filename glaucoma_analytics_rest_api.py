from datetime import datetime
from os import environ

from bottle import Bottle, response, request, HTTPResponse
from redis import Redis

rest_api = Bottle(catchall=False, autojson=True)
redis = Redis(host=environ.get('REDIS_HOST', 'localhost'),
              port=int(environ.get('REDIS_PORT', 6379)),
              db=int(environ.get('REDIS_DB', 0)))

__version__ = '0.0.1'


@rest_api.hook('after_request')
def enable_cors():
    response.headers['Access-Control-Allow-Origin'] = '*'  # Take out '*' in production!


def auth_needed(f):
    def inner(*args, **kwargs):
        token = request.get_header('X-Access-Token')
        if token is None or redis.get(token) is None:
            return HTTPResponse('Valid authentication required', 401)
        return f(*args, **kwargs)

    return inner


@rest_api.route('/api/py/analytics', apply=[auth_needed])
def analytics():
    return {'wow': 'yeah'}


@rest_api.route('/api')
@rest_api.route('/api/status')
def status():
    return {
        'rest_api_version': __version__,
        'server_time': datetime.now().strftime("%I:%M%p on %B %d, %Y")
    }


if __name__ == '__main__':
    rest_api.run(host=environ.get('HOST', '0.0.0.0'), port=environ.get('PORT', 5555),
                 debug=bool(environ.get('DEBUG', True)))
