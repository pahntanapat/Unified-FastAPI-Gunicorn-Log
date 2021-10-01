"""Unified Logging by Logguru for Gunicorn, Uvicorn, and FastAPI Application

Inspired and Modified from [Pawamoy&apos;s articles](https://pawamoy.github.io/posts/unify-logging-for-a-gunicorn-uvicorn-app/) 
"""

import logging
from sys import stdout
from typing import Union
from loguru import logger
from gunicorn.glogging import Logger
from gunicorn.app.base import BaseApplication

from unified_api_log.log import StubbedGunicornLogger
from threading import Thread


class MainProcess(BaseApplication):
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


class InThread(MainProcess, Thread):
    def __init__(self, app, options=None):
        Thread.__init__(self)
        MainProcess.__init__(self, app, options)