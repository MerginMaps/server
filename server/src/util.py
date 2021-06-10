import datetime
import math
import os
import re
import six
import typing
from pathvalidate import sanitize_filename


def _deserialize(data, klass):
    """Deserializes dict, list, str into an object.

    :param data: dict, list or str.
    :param klass: class literal, or string of class name.

    :return: object.
    """
    if data is None:
        return None

    if klass in six.integer_types or klass in (float, str, bool):
        return _deserialize_primitive(data, klass)
    elif klass == object:
        return _deserialize_object(data)
    elif klass == datetime.date:
        return deserialize_date(data)
    elif klass == datetime.datetime:
        return deserialize_datetime(data)
    elif type(klass) == typing.GenericMeta:
        if klass.__extra__ == list:
            return _deserialize_list(data, klass.__args__[0])
        if klass.__extra__ == dict:
            return _deserialize_dict(data, klass.__args__[1])
    else:
        return deserialize_model(data, klass)


def _deserialize_primitive(data, klass):
    """Deserializes to primitive type.

    :param data: data to deserialize.
    :param klass: class literal.

    :return: int, long, float, str, bool.
    :rtype: int | long | float | str | bool
    """
    try:
        value = klass(data)
    except UnicodeEncodeError:
        value = six.u(data)
    except TypeError:
        value = data
    return value


def _deserialize_object(value):
    """Return a original value.

    :return: object.
    """
    return value


def deserialize_date(string):
    """Deserializes string to date.

    :param string: str.
    :type string: str
    :return: date.
    :rtype: date
    """
    try:
        from dateutil.parser import parse
        return parse(string).date()
    except ImportError:
        return string


def deserialize_datetime(string):
    """Deserializes string to datetime.

    The string should be in iso8601 datetime format.

    :param string: str.
    :type string: str
    :return: datetime.
    :rtype: datetime
    """
    try:
        from dateutil.parser import parse
        return parse(string)
    except ImportError:
        return string


def deserialize_model(data, klass):
    """Deserializes list or dict to model.

    :param data: dict, list.
    :type data: dict | list
    :param klass: class literal.
    :return: model object.
    """
    instance = klass()

    if not instance.swagger_types:
        return data

    for attr, attr_type in six.iteritems(instance.swagger_types):
        if data is not None \
                and instance.attribute_map[attr] in data \
                and isinstance(data, (list, dict)):
            value = data[instance.attribute_map[attr]]
            setattr(instance, attr, _deserialize(value, attr_type))

    return instance


def _deserialize_list(data, boxed_type):
    """Deserializes a list and its elements.

    :param data: list to deserialize.
    :type data: list
    :param boxed_type: class literal.

    :return: deserialized list.
    :rtype: list
    """
    return [_deserialize(sub_data, boxed_type)
            for sub_data in data]


def _deserialize_dict(data, boxed_type):
    """Deserializes a dict and its elements.

    :param data: dict to deserialize.
    :type data: dict
    :param boxed_type: class literal.

    :return: deserialized dict.
    :rtype: dict
    """
    return {k: _deserialize(v, boxed_type)
            for k, v in six.iteritems(data)}


def get_byte_string(size_bytes):
    """ Return string of size_bytes in string

    :param size_bytes: size_bytes to string.
    :type size_bytes: int

    :return: size bytes in string.
    :rtype: str
    """

    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    power = math.pow(1024, i)
    size = round(size_bytes / power, 2)
    return "%s %s" % (size, size_name[i])


def convert_byte(size_bytes, unit):
    """ Convert byte into other unit

    :param size_bytes: size_bytes to target.
    :type size_bytes: int

    :param unit: target unit .
    :type unit: str

    :return: size in target unit.
    :rtype: float
    """

    if size_bytes == 0:
        return "0B"
    units = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
    i = 0
    try:
        i = units.index(unit.upper())
    except ValueError:
        pass
    if i > 0:
        power = math.pow(1024, i)
        size_bytes = round(size_bytes / power, 2)
    return size_bytes


def is_name_allowed(string):
    """ Check if string is just has whitelisted character

    :param string: string to be checked.
    :type string: str

    :return: boolean of has just whitelisted character
    :rtype: bool
    """
    return re.match('^[\w ._\-~()\'!*:@,;]+$', string)


def mergin_secure_filename(filename):
    """ Change filename to be secured filename

    :param filename: string to be checked.
    :type filename: str

    :return: secured filename
    :rtype: str
    """
    filename = os.path.normpath(filename)
    return os.path.join(*[sanitize_filename(path, replacement_text="_") for path in filename.split(os.sep)])


def get_path_from_files(files, path, is_diff=False):
    """ Get path from files between getting sanitized or mergin_secure_filename

    :param files: list of files
    :type files: list

    :param path: path that will be checked
    :type path: str

    :return: secured filename
    :rtype: str
    """
    for file in files:
        if file['path'] == path:
            if is_diff:
                return file['diff']['sanitized_path'] if 'sanitized_path' in file else file['diff']['path']
            else:
                return file['sanitized_path'] if 'sanitized_path' in file else file['path']
    return mergin_secure_filename(path)
