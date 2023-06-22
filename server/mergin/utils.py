# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
from sqlalchemy import Column

def parse_order_params(cls, order_params):
    """Parse order parameters in query string

    :param cls: Db model class
    :type cls: db.Model
    :param order_params: order parameter string, e.g. 'name ASC,created DESC'
    :type order_params: str

    :rtype: List[Column]
    """
    order_by_params = []
    for p in order_params.split(","):
        try:
            col, order = p.strip().split(" ")
        except ValueError:
            continue
        order_attr = cls.__table__.c.get(col, None)
        if not isinstance(order_attr, Column):
            continue

        if order == "ASC":
            order_by_params.append(order_attr.asc())
        elif order == "DESC":
            order_by_params.append(order_attr.desc())
    return order_by_params