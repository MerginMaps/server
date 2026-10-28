# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

"""

  Common gunicorn configuration

  Gunicorn uses the following order of precidence for configuration
  values:

  1. Command-line (highest)
  2. Environment variable
  3. File referenced by --config (lowest)

  Put configuration common across all deployment environments here and
  add environment-specific items to the GUNICORN_CMD_ARGS env var.

=======
  WARNING: You may be tempted to *pythonise* the command-line arguments
  - instead, make sure you look at this page: the headings are the
  names the variables should have:

    https://docs.gunicorn.org/en/stable/settings.html#settings
"""
import logging

worker_class = "gevent"

workers = 2

worker_connections = 1000

backlog = 480

keepalive = 30

accesslog = "-"

errorlog = "-"

access_log_format = '[ACCESS] [%({X-Trace-Id}o)s] %({x-forwarded-for}i)s %(m)s %(U)s %(q)s %(H)s %(s)s %(B)s %(f)s "%(a)s" %(D)s %(p)s'

logconfig = "gunicorn-logging.conf"

max_requests = 20000

max_requests_jitter = 5000

timeout = 30

preload_app = False


"""
  The following server hook is executed when a worker times-out. It
  allows us to print a traceback which may well indicate where in the
  code we stopped telling the master process we were still alive.

  This function was lifted directly from here:
  https://github.com/benoitc/gunicorn/blob/master/examples/example_config.py

"""


def worker_abort(worker):
    worker.log.info("worker received SIGABRT signal")

    # get traceback info
    import threading, sys, traceback

    id2name = {th.ident: th.name for th in threading.enumerate()}
    code = []
    for threadId, stack in sys._current_frames().items():
        code.append("\n# Thread: %s(%d)" % (id2name.get(threadId, ""), threadId))
        for filename, lineno, name, line in traceback.extract_stack(stack):
            code.append('File: "%s", line %d, in %s' % (filename, lineno, name))
            if line:
                code.append("  %s" % (line.strip()))
    worker.log.info("\n".join(code))


class OneLineExceptionFormatter(logging.Formatter):
    """
    Reformat Exceptions with traceback to be single line.
    Please note that for custom flask/logging you need to exc_info=True for non-exception levels

    :Example:
        >>> application.logger.error("Crazy long \\n exception msg", exc_info=True)
        [2019-11-20 16:49:09 +0100] [17950] [ERROR] Crazy long || exception msg ||Traceback (most recent call last):||
        File "/__init__.py", line 163, in ping||    x = 1 / 0||ZeroDivisionError: division by zero
    """

    def format(self, record):
        from opentelemetry import trace

        # force fetch the ID if it's missing or zeroed
        if getattr(record, "otelTraceID", "0") in ["0", "-"]:
            span = trace.get_current_span().get_span_context()
            record.otelTraceID = format(span.trace_id, "032x") if span.is_valid else "-"

        # format message according to formatter class passed
        msg = super().format(record)
        if record.exc_text:
            msg = msg.replace("\n", "||")
        return msg


def post_worker_init(worker):
    """
    Runs in the worker after gevent monkey-patching and app loading.
    Do not load the app in post_fork, it would import ssl (via requests/urllib3) before it is patched
    and outgoing HTTPS requests would fail with RecursionError.
    """
    from mergin.config import Configuration
    from mergin.otel.instrument import instrument_flask_app

    # We initialize the OTel SDK here, inside the child process.
    # This ensures each worker gets its own fresh background exporter thread.
    if Configuration.OTEL_ENABLED:
        instrument_flask_app(worker.wsgi)
