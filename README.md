glaucoma-risk-calculator-analytics-rest-api
===========================================
[![License](https://img.shields.io/badge/license-Apache--2.0%20OR%20MIT-blue.svg)](https://opensource.org/licenses/Apache-2.0)
![Python version](https://img.shields.io/badge/python-2.7%20%7C%203.5%20%7C%203.6%20%7C%203.7%20%7C%203.8-blue)
![Python implementation](https://img.shields.io/badge/implementation-cpython-blue)
[![Build Status](https://travis-ci.org/offscale/glaucoma-risk-calculator-analytics-rest-api.svg?branch=master)](https://travis-ci.org/offscale/glaucoma-risk-calculator-analytics-rest-api)
[![Coverage Status](https://coveralls.io/repos/github/offscale/glaucoma-risk-calculator-analytics-rest-api/badge.svg)](https://coveralls.io/github/offscale/glaucoma-risk-calculator-analytics-rest-api)
[![black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort)

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
$ python -m glaucoma_risk_calculator_analytics_rest_api
```

Additionally there are environment variables, run `grep -F environ glaucoma_risk_calculator_analytics_rest_api` to see current ones. E.g.:

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
working_dir = /var/www/offscale/glaucoma-risk-calculator-analytics-rest-api
cmd = python
args = -m glaucoma_risk_calculator_analytics_rest_api
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
HOME=/var/www/offscale/glaucoma-risk-calculator-analytics-rest-api
SERVER=gunicorn
PORT=5454
RDBMS_URI=postgresql://username:password@host:port/database
GLAUCOMA_DATADIR=/
```

## License

Licensed under any of:

- Apache License, Version 2.0 ([LICENSE-APACHE](LICENSE-APACHE) or <https://www.apache.org/licenses/LICENSE-2.0>)
- MIT license ([LICENSE-MIT](LICENSE-MIT) or <https://opensource.org/licenses/MIT>)
- CC0 license ([LICENSE-CC0](LICENSE-CC0) or <https://creativecommons.org/publicdomain/zero/1.0/legalcode>)

at your option.

### Contribution

Unless you explicitly state otherwise, any contribution intentionally submitted
for inclusion in the work by you, as defined in the Apache-2.0 license, shall be
licensed as above, without any additional terms or conditions.
