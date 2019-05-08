from datetime import datetime

from bottle import response

from glaucoma_analytics_rest_api import rest_api, __version__
from glaucoma_analytics_rest_api.analytics import run
from glaucoma_analytics_rest_api.utils import auth_needed


@rest_api.hook('after_request')
def enable_cors():
    response.headers['Access-Control-Allow-Origin'] = '*'  # Take out '*' in production!


@rest_api.route('/api/py/analytics', apply=[auth_needed])
def analytics():
    return run()


@rest_api.route('/api')
@rest_api.route('/api/status')
def status():
    return {
        'rest_api_version': __version__,
        'server_time': datetime.now().strftime("%I:%M%p on %B %d, %Y")
    }
