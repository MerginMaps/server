# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# GNU Affero General Public License v3.0 - see licence.txt for more details.

# we need to monkey patch before app is loaded resolve this:
# "gunicorn/workers/ggevent.py:65: MonkeyPatchWarning: Monkey-patching ssl after ssl has already been imported may lead
# to errors, including RecursionError on Python 3.6. It may also silently lead to incorrect behaviour on Python 3.7.
# Please monkey-patch earlier. See https://github.com/gevent/gevent/issues/1016.
# Modules that had direct imports (NOT patched): ['urllib3.util, 'urllib3.util.ssl']"
# which comes from using requests (its deps) lib in webhooks

import os
if not os.getenv("NO_MONKEY_PATCH", False):
    import gevent.monkey
    gevent.monkey.patch_all(subprocess=True)

import logging
from src import create_app

application = create_app()


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
        msg = super().format(record)  # format message according to formatter class passed
        if record.exc_text:
            msg = msg.replace('\n', '||')
        return msg
