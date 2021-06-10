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

bind = '0.0.0.0:5000'

worker_class = 'gevent'

workers = 2

worker_connections = 1000

backlog = 480

keepalive = 30

accesslog = '-'

errorlog = '-'

access_log_format = '[ACCESS] %({x-forwarded-for}i)s %(m)s %(U)s %(q)s %(H)s %(s)s %(B)s %(f)s "%(a)s" %(D)s %(p)s'

logconfig = 'gunicorn-logging.conf'

max_requests = 20000

max_requests_jitter = 5000

"""
  The following server hook is executed when a worker times-out. It 
  allows us to print a traceback which may well indicate where in the 
  code we stopped telling the master process we were still alive.
  
  This function was lifted directly from here:
  https://github.com/benoitc/gunicorn/blob/master/examples/example_config.py
  
"""


def worker_abort(worker):
    worker.log.info("worker received SIGABRT signal")

    ## get traceback info
    import threading, sys, traceback
    id2name = {th.ident: th.name for th in threading.enumerate()}
    code = []
    for threadId, stack in sys._current_frames().items():
        code.append("\n# Thread: %s(%d)" % (id2name.get(threadId,""),
            threadId))
        for filename, lineno, name, line in traceback.extract_stack(stack):
            code.append('File: "%s", line %d, in %s' % (filename,
                lineno, name))
            if line:
                code.append("  %s" % (line.strip()))
    worker.log.info("\n".join(code))