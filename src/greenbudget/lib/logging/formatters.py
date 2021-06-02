import logging
from logging.handlers import SysLogHandler
import socket


class DynamicExtraArgumentFormatter(logging.Formatter):
    """
    A :obj:`logging.Formatter` extension that dynamically includes the `extra`
    arguments provided to the logger at the end of the log.  The `extra`
    arguments are appended to the base log format, defined by `fmt` - which
    is the `simple` formatter in Django's logging settings.

    Usage:
    -----
    >>> logger = logging.getLogger('greenbudget')
    >>> logger.info("Some message", extra={"foo": "bar", "apple": "banana"})
    >>> [greenbudget] INFO: "Some message" [foo=bar, apple=banana]
    """
    LOGGING_FORMAT_VERSION = "1"

    def __init__(self, fmt='[%(name)s] %(levelname)s: %(message)s',
            datefmt=None, style="%"):
        logging.Formatter.__init__(self, fmt, datefmt, style)
        self.hostname = socket.gethostname()
        self.syslog_handler = SysLogHandler()
        self._fmt = fmt

    def format(self, record: logging.LogRecord) -> str:
        # Determine what the extra arguments provided to the log method were.
        default_attrs = logging.LogRecord(
            None, None, None, None, None, None, None).__dict__.keys()
        extras = set(record.__dict__.keys()) - default_attrs

        # Concatenate those extra arguments with the base formatter.
        self._style._fmt = self._fmt
        if extras:
            self._style._fmt += " " + "[" + ", ".join([
                f'{attr} = %({attr})s' for attr in extras
            ]) + "]"

        return super().format(record)
