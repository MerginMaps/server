# Copyright (C) 2019 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

import requests
import logging
from urllib.parse import urlparse
import json
import functools
from blinker import Namespace
import concurrent.futures


def is_valid_url(url):
    parsed = urlparse(url)
    return parsed.scheme and parsed.netloc


class Webhook:
    """
    Base class for using web hook.

    Please note you want either subclass and override data format as desired
    by target service or make sure you pass them correctly.
    """
    def __init__(self, name, url):
        self.name = name
        self.url = url

    def format_data(self, data):
        return data  # to be overwritten

    def request(self, data):
        return requests.post(self.url, data=json.dumps(data), headers={'Content-Type': 'application/json'})

    def send(self, sender, **kwargs):
        if not is_valid_url(self.url):
            logging.warning(f'Invalid url {self.url}, webhook {self.name} from sender {sender} failed: {str(kwargs)}')
            return
        data = kwargs.get('msg', '')
        msg = self.format_data(data)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(self.request, msg)
            resp = future.result()
            if not resp.ok:
                logging.warning(f'Webhook {self.name} from sender {sender} failed: {resp.text}')
            return resp


class WebhookManager:
    """ Base class to handle (blinker) signals connected to Webhook handlers. """
    def __init__(self):
        self.signals = Namespace()

    def check_signal(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            if args[0] not in self.signals:
                return
            return func(self, *args, **kwargs)
        return wrapper

    def register_signal(self, signal):
        self.signals.signal(signal)

    @check_signal
    def remove_signal(self, signal):
        self.signals.pop(signal)

    @check_signal
    def connect_handler(self, signal, handler):
        if isinstance(handler, Webhook):
            self.signals[signal].connect(handler.send, weak=False)

    @check_signal
    def disconnect_handler(self, signal, handler):
        self.signals[signal].disconnect(handler.send)

    @check_signal
    def emit_signal(self, signal, sender, **kwargs):
        return self.signals[signal].send(sender, **kwargs)

    check_signal = staticmethod(check_signal)
