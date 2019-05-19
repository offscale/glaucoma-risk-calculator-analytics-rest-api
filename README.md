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

## Deployment
[Circus](https://circus.readthedocs.io) example:
```ini
[watcher:calc]
working_dir = /var/www/glaucoma/glaucoma-analytics-rest-api
cmd = python
args = -m glaucoma_analytics_rest_api
uid = g_user
numprocesses = 1
autostart = true
send_hup = true
stdout_stream.class = FileStream
stdout_stream.filename = /var/www/logs/calc.stdout.log
stdout_stream.max_bytes = 10485760
stdout_stream.backup_count = 4
stderr_stream.class = FileStream
stderr_stream.filename = /var/www/logs/calc.stderr.log
stderr_stream.max_bytes = 10485760
stderr_stream.backup_count = 4
virtualenv = /opt/venvs/glaucoma-analytics
virtualenv_py_ver = 3.5
copy_env = true

[env:calc]
TERM=rxvt-256color
SHELL=/bin/bash
USER=g_user
LANG=en_US.UTF-8
HOME=/var/www/glaucoma/glaucoma-analytics-rest-api
SERVER=gunicorn
PORT=5454
```
