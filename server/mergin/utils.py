# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
from sqlalchemy import Column


def parse_order_params(cls, order_params, json_sort=None):
    """Parse order parameters in query string

    :param cls: Db model class
    :type cls: db.Model
    :param order_params: order parameter string, e.g. 'name ASC,created DESC,meta.storage ASC'
    :type order_params: str

    :rtype: List[Column]
    """
    order_by_params = []
    for p in order_params.split(","):
        try:
            col, order = p.strip().split(" ")
        except ValueError:
            continue
        # find candidate for nested json sort
        if "." in col:
            col, attr = col.split(".")
        else:
            attr = None
        order_attr = cls.__table__.c.get(col, None)
        if not isinstance(order_attr, Column):
            continue
        # sort by key in JSON field
        if attr:
            # unknown field
            if attr not in json_sort:
                continue

            from sqlalchemy import JSON
            if not isinstance(order_attr.type, JSON):
                continue

            # cast expected type for json key sort
            # would result in something like "(json_column->>'attribute')::type"))
            if json_sort[attr] == "int":
                order_attr = order_attr[attr].as_numeric(20, 0)  # to handle bigint
            elif json_sort[attr] == "float":
                order_attr = order_attr[attr].as_float()
            elif json_sort[attr] == "bool":
                order_attr = order_attr[attr].as_boolean()
            else:
                order_attr = order_attr[attr].as_string()

        if order == "ASC":
            order_by_params.append(order_attr.asc())
        elif order == "DESC":
            order_by_params.append(order_attr.desc())
    return order_by_params
