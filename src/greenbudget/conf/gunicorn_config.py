import multiprocessing
import sys
import threading
import traceback

# The socket to bind.
bind = '0.0.0.0:8000'
# The number of pending connections.  This refers to the number of clients that
# can be waiting to be served.
backlog = 2048
access_log_format = (
    '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"')
errorlog = '-'
loglevel = 'debug'
accesslog = '-'

workers = multiprocessing.cpu_count() * 2 + 1

# Installs a trace function that spews every line of Python that is executed
# when running the server.  This is the nuclear option.
spew = False

# Detach the main Gunicorn process from the controlling terminal with a
# standard fork/fork sequence.
daemon = False
# The path to a pid file to write.
pidfile = None
# A mask for file permissions written by Gunicorn. Note that this affects
# socket permissions.
umask = 0
# Switch worker processes to run as this user.
user = None
# Switch worker process to run as this group.
group = None
# A directory to store temporary request data when requests are read. This will
# most likely be disappearing soon.
tmp_upload_dir = None

# A base to use with setproctitle to change the way that Gunicorn processes
# are reported to the system processes.
proc_name = None


def post_fork(server, worker):
    # Called just after a worker has been forked.
    server.log.info("Worker spawned (pid: %s)", worker.pid)


def pre_fork(server, worker):
    # Called just prior to forking the worker subprocess.
    pass


def pre_exec(server):
    # Called just prior to forking off a secondary.
    server.log.info("Forked child, re-executing.")


def when_ready(server):
    server.log.info("Server is ready. Spawning workers")


def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

    id2name = {th.ident: th.name for th in threading.enumerate()}
    code = []
    for threadId, stack in sys._current_frames().items():
        code.append("\n# Thread: %s(%d)" % (id2name.get(threadId, ""),
            threadId))
        for filename, lineno, name, line in traceback.extract_stack(stack):
            code.append('File: "%s", line %d, in %s' % (filename,
                lineno, name))
            if line:
                code.append("  %s" % (line.strip()))
    worker.log.debug("\n".join(code))


def worker_abort(worker):
    worker.log.info("worker received SIGABRT signal")
