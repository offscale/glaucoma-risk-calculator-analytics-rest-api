# coding: utf-8

from __future__ import print_function

from os import environ
from sys import stderr

from glaucoma_risk_calculator_analytics_rest_api import rest_api, routes

_version = routes.__version__

if __name__ == "__main__":
    print(
        "Serving glaucoma_risk_calculator_analytics_rest_api {routes_version}".format(
            routes_version=_version
        ),
        file=stderr,
    )
    rest_api.run(
        host=environ.get("HOST", "0.0.0.0"),
        port=environ.get("PORT", 5555),
        server=environ.get("SERVER", "wsgiref"),
        debug=bool(environ.get("DEBUG", environ.get("NO_DEBUG", True))),
    )
