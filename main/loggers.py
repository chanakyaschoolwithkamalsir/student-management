import logging
from logging.handlers import TimedRotatingFileHandler

logger = logging.getLogger(__name__)
logger.propagate = False
# logging.basicConfig(level=logging.INFO)
logger.setLevel(logging.INFO)
## Format for Loggers
logFormatter = logging.Formatter(
    "[%(asctime)s-%(levelname)s]-%(filename)s-%(funcName)s-%(threadName)s-[Line-%(lineno)d]:%(message)s",
    "%Y-%m-%d %H:%M:%S",
)
## Timed Rotation Files with backup upto 3 files.
filehandler = TimedRotatingFileHandler("logs.log", when="d", interval=1, backupCount=3)
filehandler.suffix = "%Y%m%d"

filehandler.setFormatter(logFormatter)
logger.addHandler(filehandler)
## Console Loggers to view the loggers
consolehandler = logging.StreamHandler()
consolehandler.setLevel(logging.INFO)
consolehandler.setFormatter(logFormatter)
logger.addHandler(consolehandler)
if not logger.hasHandlers():
    logger.addHandler(consolehandler)