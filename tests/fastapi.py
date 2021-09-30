from datetime import datetime
import logging
from os import cpu_count, environ
from fastapi import FastAPI, Response
from fastapi.responses import ORJSONResponse
from unified_api_log.gunicorn import global_config, Gunicorn

DEBUG = environ.get('DEBUG', False)

app = FastAPI(
    debug=DEBUG,
    title='RESUME: The Medical Speech-to-Text API',
    description=
    'Convert medical speech either conversation or dictation to medical record document',
    default_response_class=ORJSONResponse,
    version='0.1.0')


@app.get('/test')
def test(response: Response):
    response.set_cookie('start', datetime.now().isoformat(), max_age=3600)
    return {'response_time': datetime.now().isoformat()}


if __name__ == '__main__':
    logger = global_config(log_level=(logging.DEBUG if
                                      (DEBUG) else logging.INFO),
                           json=(not DEBUG))
    cpu = cpu_count() * 2
    Gunicorn({"bind": "0.0.0.0:80", "workers": cpu, "threads": cpu * 2})
