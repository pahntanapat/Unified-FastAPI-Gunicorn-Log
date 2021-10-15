import logging
from sys import stdout
from typing import Union
from loguru import logger
from gunicorn.glogging import Logger

try:
    from orjson import dumps
except:
    from json import dumps


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


# BUILT_IN_TYPE = (int, float, str)


def orjson_log_sink(msg):
    r = msg.record
    rec = {
        'elapsed': r['elapsed'].total_seconds(),
        'time': r['time'].isoformat(),
        'level': {
            'name': r['level'].name,
            'no': r['level'].no,
        },
        'process': {
            'id': r['process'].id,
            'name': r['process'].name
        },
        'thread': {
            'id': r['thread'].id,
            'name': r['thread'].name
        },
        'file': r['file'].path
    }

    if r['exception']:
        rec['exception'] = str(msg)

    for k, v in r.items():
        print(k, type(v), v)
        if k in rec:
            continue
        rec[k] = v

    print(dumps(rec), flush=True)


def json_log_config(log_level: Union[str, int] = logging.INFO,
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

    if json:
        logger.configure(handlers=[{
            "sink": orjson_log_sink,
            "serialize": json,
            'diagnose': True,
            'backtrace': True
        }])
    else:
        logger.configure(handlers=[{
            "sink": stdout,
            "serialize": False,
            'format':
            '<green>{time}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level> | <level>{extra}</level>',
            'diagnose': True,
            'backtrace': True
        }])

    return logger