from collections import OrderedDict
from datetime import datetime
import json
import logging
from logging.handlers import SysLogHandler
import socket
import traceback

from . import global_ctx


BUILTIN_ATTRS = {
    'args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
    'funcName', 'levelname', 'levelno', 'lineno', 'module', 'msecs',
    'message', 'msg', 'name', 'pathname', 'process', 'processName',
    'relativeCreated', 'stack_info', 'thread', 'threadName'
}


def fix_circular_refs(o, _seen=None):
    """
    If a JSON object has keys that are repeated in lower levels of the tree,
    the JSON encoding will fail due to circular references.  This method will
    remove those circular references so the encoding will not fail.
    """
    _seen = _seen or set()
    if id(o) in _seen:
        # This is a circular reference, we need to remove it,
        return '<cycle>'
    _seen.add(id(o))
    res = o
    if isinstance(o, dict):
        res = {
            fix_circular_refs(k, _seen): fix_circular_refs(v, _seen)
            for k, v in o.items()
        }
    elif isinstance(o, (list, tuple, set, frozenset)):
        res = type(o)(fix_circular_refs(v, _seen) for v in o)
    # Now we need to remove the ID again, only want nested references to count.
    _seen.remove(id(o))
    return res


def safer_format_traceback(exc_typ, exc_val, exc_tb):
    """
    Safely format an exception traceback into a safe string.

    There are common attacks that try to write arbitrary data to a server's
    log files.  This can happen if, for instance, a malicious user triggers
    a ValueError with a carefully-crafted payload.

    This function formats the traceback using "%r" for the actual exception
    data, which passes it through repr() so that any special chars are
    safely escaped.
    """
    lines = ["Uncaught exception:\n"]
    lines.extend(traceback.format_tb(exc_tb))
    lines.append("%r\n" % (exc_typ,))
    lines.append("%r\n" % (exc_val,))
    return "".join(lines)


class SafeJSONEncoder(json.JSONEncoder):
    """
    :obj:`json.JSONEncoder` extension that will remove circular references
    from the encoding JSON to prevent encoding errors due to these circular
    references.
    """
    def default(self, o):
        return repr(o)

    def encode(self, o):
        return super().encode(fix_circular_refs(o))

    def iterencode(self, o, **kwargs):
        return super().iterencode(fix_circular_refs(o), **kwargs)


class JsonLogFormatter(logging.Formatter):
    """
    :obj:`logging.Formatter` that transforms the logging record into machine
    readable JSON.

    This was adapted from the following projects:

    https://github.com/mozilla-services/python-dockerflow/blob/master/src/dockerflow/logging.py  # noqa
    https://github.com/DanHoerst/json-log-formatter/blob/master/json_log_formatter/__init__.py  # noqa

    Usage:
    -----
    >>> logger = logging.getLogger('greenbudget')
    >>> logger.info("Some message", extra={"foo": "bar", "apple": "banana"})
    >>> {
    >>>   "message": "Some message",
    >>>   "foo": "bar",
    >>>   "apple": "banana",
    >>> }
    """
    LOGGING_FORMAT_VERSION = "1"

    def __init__(self, fmt=None, datefmt=None, style="%",
            logger_name="greenbudget"):
        logging.Formatter.__init__(self, fmt, datefmt, style)
        self.logger_name = logger_name
        self.hostname = socket.gethostname()
        self.syslog_handler = SysLogHandler()

    def format(self, record):
        data = OrderedDict({
            'logger': record.name,
            'level': self.syslog_handler.mapPriority(record.levelname),
            'time': datetime.utcnow().isoformat(),
        })

        # Only include the `msg` if it has content and is not already a JSON
        # blob.
        message = record.getMessage()
        if (message and not message.startswith("{")
                and not message.endswith("}")):
            data["msg"] = message

        data['hostname'] = self.hostname
        if global_ctx.user:
            data['user_id'] = global_ctx.user.pk
        if global_ctx.remote_addr:
            data['remote_addr'] = global_ctx.remote_addr

        # Include any other custom attributes set on the record.
        data.update({
            attr_name: record.__dict__[attr_name]
            for attr_name in record.__dict__
            if attr_name not in BUILTIN_ATTRS
        })

        # If there is an error, let's format it for some nice output.
        if record.exc_info is not None:
            data["error"] = repr(record.exc_info[1])
            data["traceback"] = safer_format_traceback(*record.exc_info)

        return json.dumps(data, cls=SafeJSONEncoder)


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
