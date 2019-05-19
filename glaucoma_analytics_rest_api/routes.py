from datetime import datetime, timedelta
from sys import stderr

import arrow
from arrow.parser import ParserError
from bottle import response, request

from glaucoma_analytics_rest_api import rest_api, __version__
from glaucoma_analytics_rest_api.analytics import run, sydney
from glaucoma_analytics_rest_api.utils import auth_needed, PY3

if PY3:
    from urllib.parse import unquote
else:
    from urllib import unquote


@rest_api.hook('after_request')
def enable_cors():
    response.headers['Access-Control-Allow-Origin'] = '*'  # Take out '*' in production!


@rest_api.route('/api/py/analytics', apply=[auth_needed])
def analytics():
    if request.params.startDatetime and request.params.endDatetime:
        try:
            event_start = arrow.get(unquote(request.params.startDatetime))
            event_end = arrow.get(unquote(request.params.endDatetime))
        except ParserError as e:
            response.status = 400
            return {'error': e.__class__.__name__,
                    'error_message': '{}'.format(e)}
    else:
        # Limit selection to 8AM Monday until 2:30PM Monday
        # (which corresponds with the OPSM event start & end time)
        event_start = datetime(year=2019, month=3, day=11, hour=8, tzinfo=sydney)
        event_end = event_start + timedelta(hours=6, minutes=60)
    try:
        return run(event_start, event_end)
    except Exception as e:
        response.status = 400
        print(e, file=stderr)
        return {'error': e.__class__.__name__,
                'error_message': '{}'.format(e)}


@rest_api.route('/api')
@rest_api.route('/api/status')
def status():
    return {
        'rest_api_version': __version__,
        'server_time': datetime.now().strftime("%I:%M%p on %B %d, %Y")
    }
