glaucoma-analytics-rest-api
===========================

Python API for Glaucoma Risk Calculator analytics.

## Dependencies
Python (2 or 3)

## Installation
```sh
$ pip install -r requirements.txt
$ pip install .
```

## Usage
```sh
$ python -m glaucoma_analytics_rest_api
```

Additionally there are environment variables, run `grep -F environ glaucoma_analytics_rest_api` to see current ones. E.g.:

    Variable    |  Default
    -------------------------
    REDIS_HOST  |  localhost
    REDIS_PORT  |  6379
    REDIS_DB    |  0
    HOST        |  0.0.0.0
    PORT        |  5555
    DEBUG       |  True
