## Uncomment for debug d
from sys import path

path.append('src')

from datetime import datetime
import logging
from time import sleep
from loguru import logger
from sys import argv
from os import cpu_count, environ
from fastapi import FastAPI, Response
from unified_api_log.gunicorn import InThread
from unified_api_log.log import global_config

DEBUG = not (environ.get('DEBUG', argv[1] if (len(argv) > 1) else False)
             in {0, '0', '', None, False, 'false', 'False'})

app = FastAPI(
    debug=DEBUG,
    title='RESUME: The Medical Speech-to-Text API',
    description=
    'Convert medical speech either conversation or dictation to medical record document',
    version='0.0.1')


@app.get('/')
def test(response: Response):
    response.set_cookie('start', datetime.now().isoformat(), max_age=3600)
    return {'response_time': datetime.now().isoformat(), 'debug': DEBUG}


server = None


def some_thread():
    logger.info('Message from Thread')
    sleep(10)
    if server is None:
        logger.warning('Server global var is {}'.format(server))
    else:

        ## If restart server in function, the variable of server will not work after this
        logger.warning('Restart server')
        server.restart()

        sleep(10)
        logger.warning('End server')
        server.end()


if __name__ == '__main__':
    ## Config Log
    global_config(log_level=(logging.DEBUG if (DEBUG) else logging.INFO),
                  json=(not DEBUG))

    logger.info('Debug mode: {}'.format(DEBUG))

    cpu = cpu_count() * 2
    logger.info('Use CPU Workers = {}'.format(cpu))

    ## Run FastAPI in Gunicorn

    server = InThread(app, {
        "bind": "0.0.0.0:80",
        "workers": cpu,
        "threads": cpu * 2
    },
                      target=some_thread)

    server.start()
    logger.info('message after server start in main thread')
    server.join()
    logger.info('message after server thread join in main thread')
