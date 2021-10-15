from unified_api_log.gunicorn import InThread
from multiprocessing.queues import Queue
from multiprocessing.managers import SyncManager, ValueProxy
from typing import Dict, Any, Optional
import logging
from loguru import logger
from concurrent.futures import Future
from datetime import datetime

class TaskServer(InThread):
    input_queue: Queue
    result_dict: Dict[str, Any]
    keep_run: ValueProxy = None

    RESULT = 'result'
    UPDATE = 'update'

    @property
    def result(self):
        return self.result[self.RESULT]

    @result.setter
    def result(self, val):
        with self.lock:
            self.result_dict[self.RESULT] = val
            self.result_dict[self.UPDATE] = datetime.now()

    def __init__(self,
                 app=None,
                 gunicorn_options=None,
                 usage=None,
                 prog=None,
                 group=None,
                 name=None,
                 manager: Optional[SyncManager] = None,
                 *,
                 daemon=None):
        super().__init__(app=app,
                         gunicorn_options=gunicorn_options,
                         usage=usage,
                         prog=prog,
                         group=group,
                         name=name,
                         daemon=daemon)

        if manager is None:
            self.m = SyncManager()
        else:
            self.m = manager

        self.input_queue = self.m.Queue()
        self.keep_run = self.m.Value('b', True)
        self.result_dict = self.m.dict()
        self.lock = self.m.RLock()

        self.result = None

    @staticmethod
    def future_callback(future: Future, log_level=logging.INFO, name=None):
        def cb(future: Future):
            logger.log(log_level, 'Future name {} returns {}', name,
                       future.result())

        return future.add_done_callback(cb)

    def start(self, app=None):
        if app is not None:
            self.application = app
        super().start()