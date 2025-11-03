# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

from email_validator import validate_email, EmailNotValidError


def get_email_domain(email: str) -> str | None:
    try:
        result = validate_email(email, check_deliverability=False)
        return result.domain
    except EmailNotValidError:
        return
