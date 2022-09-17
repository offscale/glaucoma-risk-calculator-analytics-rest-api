# -*- coding: utf-8 -*-

from __future__ import print_function

from datetime import datetime, timedelta

from bottle import request, response
from dateutil.parser import parse

from glaucoma_risk_calculator_analytics_rest_api import __version__, rest_api
from glaucoma_risk_calculator_analytics_rest_api.analytics import (
    analytics2,
    analytics3,
    sydney,
)
from glaucoma_risk_calculator_analytics_rest_api.utils import PY3, auth_needed

if PY3:
    # noinspection PyCompatibility
    from urllib.parse import unquote
else:
    # noinspection PyCompatibility
    from urllib import unquote


@rest_api.hook("after_request")
def enable_cors():
    response.headers["Access-Control-Allow-Origin"] = "*"  # Take out '*' in production!


@rest_api.route("/api/py/analytics2", apply=[auth_needed])
def analytics2_route():
    return analytics_body(analytics2)


@rest_api.route("/api/py/analytics3", apply=[auth_needed])
def analytics3_route():
    return analytics_body(analytics3)


def analytics_body(function):
    if request.params.startDatetime and request.params.endDatetime:
        try:
            event_start = parse(unquote(request.params.startDatetime))
            event_end = parse(unquote(request.params.endDatetime))
        except ValueError as e:
            response.status = 400
            return {"error": e.__class__.__name__, "error_message": "{}".format(e)}
    else:
        # Limit selection to 8AM Monday until 2:30PM Monday
        # (which corresponds with the OPSM event start & end time)
        event_start = datetime(year=2019, month=3, day=11, hour=8, tzinfo=sydney)
        event_end = event_start + timedelta(hours=6, minutes=60)
    try:
        return function(event_start, event_end)
    except ValueError as e:
        response.status = 400
        return {"error": e.__class__.__name__, "error_message": "{}".format(e)}


@rest_api.route("/api")
@rest_api.route("/api/status")
@rest_api.route("/api/py")
def status():
    return {
        "rest_api_version": __version__,
        "server_time": datetime.now().strftime("%I:%M%p on %B %d, %Y"),
    }
