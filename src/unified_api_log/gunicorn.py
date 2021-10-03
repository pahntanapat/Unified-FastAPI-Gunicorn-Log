"""Unified Logging by Logguru for Gunicorn, Uvicorn, and FastAPI Application

Inspired and Modified from [Pawamoy&apos;s articles](https://pawamoy.github.io/posts/unify-logging-for-a-gunicorn-uvicorn-app/) 
"""

from signal import SIGINT
from gunicorn.app.base import BaseApplication
from gunicorn.arbiter import Arbiter
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
        self.arbiter = None
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
            self.arbiter = Arbiter(self)
            self.arbiter.run()
        except RuntimeError as e:
            self.logger("Error: %s" % e)
            stderr.flush()
            exit(1)

    def restart(self):
        restart_thr = Thread(target=self.__restart)
        restart_thr.start()
        return restart_thr

    def __restart(self):
        BaseApplication.reload(self)
        if self.arbiter is not None:
            self.arbiter.reload()

    def end(self):
        if self.arbiter is not None:
            self.arbiter.signal(SIGINT, None)

    def terminate(self):
        if self.arbiter is not None:
            self.arbiter.signal(SIGINT, None)


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

        if target is None:
            target = self.__run_and_end
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

    def __run_and_end(self):
        self.run_to_end()
        self.end()

    def start(self):
        super().start()
        MainProcess.run(self)

    def run_to_end(self):
        raise NotImplementedError(
            'Run to End is not implemented. Please override run_to_end or run method, or set target parameter in constructor.'
        )
