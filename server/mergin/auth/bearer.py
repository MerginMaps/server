# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import hashlib
from datetime import datetime, timezone
from itsdangerous import URLSafeTimedSerializer
from itsdangerous.exc import SignatureExpired, BadSignature
from flask.sessions import TaggedJSONSerializer


def decode_token(secret_key, salt, token):
    serializer = TaggedJSONSerializer()
    signer_kwargs = {"key_derivation": "hmac", "digest_method": hashlib.sha1}
    s = URLSafeTimedSerializer(
        secret_key, salt=salt, serializer=serializer, signer_kwargs=signer_kwargs
    )
    token_data = s.loads(token)
    try:
        expire = datetime.fromisoformat(token_data.get("expire"))
    except (ValueError, TypeError):
        raise BadSignature("Invalid token")

    if expire < datetime.now(timezone.utc):
        raise SignatureExpired("Token expired")

    return token_data


def encode_token(secret_key, salt, data):
    serializer = TaggedJSONSerializer()
    signer_kwargs = {"key_derivation": "hmac", "digest_method": hashlib.sha1}
    s = URLSafeTimedSerializer(
        secret_key, salt=salt, serializer=serializer, signer_kwargs=signer_kwargs
    )
    return s.dumps(data)
