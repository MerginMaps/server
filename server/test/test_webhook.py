# Copyright (C) 2019 Lutra Consulting Limited. All rights reserved.
# GNU Affero General Public License v3.0 - see licence.txt for more details.

import pytest
import responses
from blinker.base import NamedSignal
from src.webhooks import WebhookManager, Webhook


@pytest.fixture
def mocked_resp():
    with responses.RequestsMock() as resp:
        yield resp


def test_webhook_manager(mocked_resp, caplog):
    wm = WebhookManager()
    wm.register_signal('test')
    assert 'test' in wm.signals
    assert isinstance(wm.signals['test'], NamedSignal)

    wm.connect_handler('test', 'handler')
    assert not wm.signals['test'].receivers
    handler = Webhook('Handler', 'unknown_url')
    wm.connect_handler('test', handler)
    assert wm.signals['test'].receivers

    wm.emit_signal('test', 'Sender', foo='bar')
    assert caplog.record_tuples[0][2] == 'Invalid url unknown_url, webhook Handler from sender Sender failed: {\'foo\': \'bar\'}'

    wm.disconnect_handler('test', handler)
    assert not wm.signals['test'].receivers

    mocked_resp.add(responses.POST, 'http://webhook-test.com', body='{}', status=200, content_type='application/json')
    handler = Webhook('Handler', 'http://webhook-test.com')
    wm.connect_handler('test', handler)
    resp = wm.emit_signal('test', 'Sender', foo='bar')[0][1]
    assert resp.ok

    wm.remove_signal('test')
    assert not wm.signals
