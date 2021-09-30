"""Unified Logging by Logguru for Gunicorn, Uvicorn, and FastAPI Application

Inspired and Modified from [Pawamoy&apos;s articles](https://pawamoy.github.io/posts/unify-logging-for-a-gunicorn-uvicorn-app/) 
"""

import logging
from sys import stdout
from typing import Union
from loguru import logger
from gunicorn.glogging import Logger
from gunicorn.app.base import BaseApplication


class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth,
                   exception=record.exc_info).log(level, record.getMessage())


class StubbedGunicornLogger(Logger):
    def setup(self, cfg):
        self.loglevel = self.LOG_LEVELS.get(cfg.loglevel.lower(), logging.INFO)

        handler = logging.NullHandler()

        self.error_logger = logging.getLogger("gunicorn.error")
        self.error_logger.addHandler(handler)

        self.access_logger = logging.getLogger("gunicorn.access")
        self.access_logger.addHandler(handler)

        self.error_logger.setLevel(self.loglevel)
        self.access_logger.setLevel(self.loglevel)


class Gunicorn(BaseApplication):
    """Our Gunicorn application."""
    def __init__(self, app, options=None):
        self.options = options or {}

        ## Override Logging configuration
        self.options.update({
            "accesslog": "-",
            "errorlog": "-",
            "worker_class": "uvicorn.workers.UvicornWorker",
            "logger_class": StubbedGunicornLogger
        })

        self.application = app
        super().__init__()

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


def global_config(log_level: Union[str, int] = logging.INFO,
                  json: bool = True):
    if isinstance(log_level, str) and (log_level in logging._nameToLevel):
        log_level = logging.INFO

    intercept_handler = InterceptHandler()
    # logging.basicConfig(handlers=[intercept_handler], level=LOG_LEVEL)
    # logging.root.handlers = [intercept_handler]
    logging.root.setLevel(log_level)

    seen = set()
    for name in [
            *logging.root.manager.loggerDict.keys(),
            "gunicorn",
            "gunicorn.access",
            "gunicorn.error",
            "uvicorn",
            "uvicorn.access",
            "uvicorn.error",
    ]:
        if name not in seen:
            seen.add(name.split(".")[0])
            logging.getLogger(name).handlers = [intercept_handler]

    logger.configure(handlers=[{"sink": stdout, "serialize": json}])

    return logger