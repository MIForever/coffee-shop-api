import logging
import sys
from pythonjsonlogger import jsonlogger

from app.core.config import settings

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['time'] = self.formatTime(record, self.datefmt)

LOG_LEVEL = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

logHandler = logging.StreamHandler(sys.stdout)
if settings.LOG_FORMAT == 'json':
    formatter = CustomJsonFormatter('%(time)s %(level)s %(name)s %(message)s')
else:
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
logHandler.setFormatter(formatter)

logging.basicConfig(
    level=LOG_LEVEL,
    handlers=[logHandler],
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    force=True,
)

# Silence overly verbose loggers
logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
