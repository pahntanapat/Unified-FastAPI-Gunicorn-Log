"""Unified Logging by Logguru for Gunicorn, Uvicorn, and FastAPI Application

Inspired and Modified from [Pawamoy&apos;s articles](https://pawamoy.github.io/posts/unify-logging-for-a-gunicorn-uvicorn-app/) 
"""

from signal import SIGTERM, SIGHUP
from gunicorn.app.base import BaseApplication
from gunicorn.arbiter import Arbiter
from loguru import logger
from sys import stderr, exit

from unified_api_log.log import StubbedGunicornLogger
from threading import Thread


class MainProcess(BaseApplication):
    """Our Gunicorn application."""
    def __init__(self, app, options=None, usage=None, prog=None):
        self.options = options or {}

        ## Override Logging configuration
        self.options.update({
            "accesslog": "-",
            "errorlog": "-",
            "worker_class": "uvicorn.workers.UvicornWorker",
            "logger_class": StubbedGunicornLogger
        })

        self.application = app
        self.sig = None
        super().__init__(usage, prog)

    def load_config(self):
        config = {
            key: value
            for key, value in self.options.items()
            if ((key in self.cfg.settings) and (value is not None))
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application

    def run(self):
        try:
            arbiter = Arbiter(self)
            self.sig = arbiter.signal
            arbiter.run()
        except RuntimeError as e:
            self.logger("Error: %s" % e)
            stderr.flush()
            exit(1)

    def restart(self):
        if self.sig is not None:
            self.sig(SIGHUP, None)

    def end(self):
        if self.sig is not None:
            self.sig(SIGTERM, None)


class InThread(Thread, MainProcess):
    def __init__(self,
                 app,
                 gunicorn_options=None,
                 usage=None,
                 prog=None,
                 group=None,
                 target=None,
                 name=None,
                 args=(),
                 kwargs=None,
                 *,
                 daemon=None):
        Thread.__init__(self,
                        group=group,
                        target=target,
                        name=name,
                        args=args,
                        kwargs=kwargs,
                        daemon=daemon)
        MainProcess.__init__(self,
                             app,
                             gunicorn_options,
                             usage=usage,
                             prog=prog)

    def start(self):
        super().start()
        MainProcess.run(self)