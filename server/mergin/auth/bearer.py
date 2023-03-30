# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import hashlib
from itsdangerous import URLSafeTimedSerializer
from flask.sessions import TaggedJSONSerializer


def decode_token(secret_key, token, max_age=None):
    salt = "bearer-session"
    serializer = TaggedJSONSerializer()
    signer_kwargs = {"key_derivation": "hmac", "digest_method": hashlib.sha1}
    s = URLSafeTimedSerializer(
        secret_key, salt=salt, serializer=serializer, signer_kwargs=signer_kwargs
    )
    return s.loads(token, max_age=max_age)


def encode_token(secret_key, data):
    salt = "bearer-session"
    serializer = TaggedJSONSerializer()
    signer_kwargs = {"key_derivation": "hmac", "digest_method": hashlib.sha1}
    s = URLSafeTimedSerializer(
        secret_key, salt=salt, serializer=serializer, signer_kwargs=signer_kwargs
    )
    return s.dumps(data)
