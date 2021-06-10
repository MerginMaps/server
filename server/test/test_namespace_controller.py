# Copyright (C) 2020 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

import pytest
from .utils import add_user
from . import json_headers, TEST_ORG


@pytest.fixture(scope='function')
def test_namespace(client):
    add_user('user', 'user')
    add_user('user2', 'user2')


namespace_data = [
    ('user', 'user', 2),  # if query=user
    ('user', 'user2', 1),  # if query=user2
    ('organisation', TEST_ORG, 1),  # if query=TEST_ORG
    ('user', 'user3', 0),  # if query=user3, no namespace found
]


@pytest.mark.parametrize("namespace_type, query, expected", namespace_data)
def test_get_namespaces(client, test_organisation, test_namespace, namespace_type, query, expected):
    resp = client.get(f'/v1/namespaces/{namespace_type}?q={query}', headers=json_headers)
    assert len(resp.json) == expected
    if expected == 1:
        assert resp.json[0]['name'] == query
