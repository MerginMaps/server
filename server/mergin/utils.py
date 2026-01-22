# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
import math
from collections import namedtuple
from datetime import datetime, timedelta, timezone
from enum import Enum
import os
from flask import current_app, abort
from flask_sqlalchemy import Model
from marshmallow import Schema
from pathvalidate import sanitize_filename
from sqlalchemy import Column, JSON
from sqlalchemy.sql.elements import UnaryExpression
from typing import Optional


OrderParam = namedtuple("OrderParam", "name direction")


class OrderDirection(Enum):
    ASC = "asc"
    DESC = "desc"


def split_order_param(order_param: str) -> Optional[OrderParam]:
    """Split db query order parameter"""
    try:
        col, order = order_param.strip().split(" ")
        direction = OrderDirection(order.lower())
    except ValueError:
        return
    return OrderParam(col, direction)


def get_order_param(
    cls: Model, order_param: OrderParam, json_sort: dict = None, field_map: dict = None
) -> Optional[UnaryExpression]:
    """Return order by clause parameter for SQL query

    :param cls: Db model class
    :type cls: db.Model
    :param order_param: parsed order parameter
    :type order_param: OrderParam
    :param json_sort: type mapping for sort by json field, e.g. '{"storage": "int"}', defaults to None
    :type json_sort: dict
    :param field_map: mapping for translating public field names to internal DB columns, e.g. '{"size": "disk_usage"}'
    :type field_map: dict
    """
    # translate field name to column name
    db_column_name = order_param.name
    if field_map and order_param.name in field_map:
        db_column_name = field_map[order_param.name]
    # find candidate for nested json sort
    if "." in db_column_name:
        col, attr = db_column_name.split(".")
    else:
        col = db_column_name
        attr = None
    order_attr = cls.__table__.c.get(col, None)
    if not isinstance(order_attr, Column):
        abort(400, "Invalid order parameter")
    # sort by key in JSON field
    if attr:
        if not json_sort:
            return
        # unknown field
        if attr not in json_sort:
            return
        if not isinstance(order_attr.type, JSON):
            return

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

    if order_param.direction is OrderDirection.ASC:
        return order_attr.asc()
    elif order_param.direction is OrderDirection.DESC:
        return order_attr.desc()


def parse_order_params(
    cls: Model, order_params: str, json_sort: dict = None, field_map: dict = None
) -> list[UnaryExpression]:
    """Convert order parameters in query string to list of order by clauses.

    :param cls: Db model class
    :type cls: db.Model
    :param order_params: order parameter query string, e.g. 'name ASC,created DESC,meta.storage ASC'
    :type order_params: str
    :param json_sort: type mapping for sort by json field, e.g. '{"storage": "int"}', defaults to None
    :type json_sort: dict
    :param field_map: mapping response fields to database column names, e.g. '{"size": "disk_usage"}'
    :type field_map: dict

    :rtype: List[Column]
    """
    order_by_params = []
    for p in order_params.split(","):
        order_param = split_order_param(p)
        if not order_param:
            continue
        order_attr = get_order_param(cls, order_param, json_sort, field_map)
        if order_attr is not None:
            order_by_params.append(order_attr)
    return order_by_params


def format_time_delta(delta: timedelta) -> str:
    """Format timedelta difference approximately in days or hours"""
    days = round(delta.total_seconds() / (24 * 3600))
    if days > 1:
        difference = f"{days} days"
    elif delta.days > 0:
        difference = "1 day"
    else:
        hours = delta.total_seconds() / 3600
        if hours > 1:
            difference = f"{math.ceil(hours)} hours"
        elif hours > 0:
            difference = "1 hour"
        else:
            difference = "N/A"
    return difference


def save_diagnostic_log_file(app: str, username: str, body: bytes) -> str:
    """Save diagnostic log file to DIAGNOSTIC_LOGS_DIR"""

    content = body.decode("utf-8")
    datetime_iso_str = datetime.now(tz=timezone.utc).isoformat()
    file_name = sanitize_filename(
        username + "_" + app + "_" + datetime_iso_str + ".log"
    )
    to_folder = current_app.config.get("DIAGNOSTIC_LOGS_DIR")
    os.makedirs(to_folder, exist_ok=True)
    with open(os.path.join(to_folder, file_name), "w") as f:
        f.write(content)

    return file_name


def get_schema_fields_map(schema: Schema) -> dict:
    """
    Creates a mapping of schema field names to corresponding DB columns.
    This allows sorting by the API field name (e.g. 'size') while
    actually sorting by the database column (e.g. 'disk_usage').
    """
    mapping = {}
    for name, field in schema._declared_fields.items():
        if field and field.attribute:
            mapping[name] = field.attribute
    return mapping
