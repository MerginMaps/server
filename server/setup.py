# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

from setuptools import setup, find_packages

setup(
    name="mergin",
    version="2023.2.0",
    url="https://github.com/MerginMaps/mergin",
    license="AGPL-3.0-only",
    author="Lutra Consulting Limited",
    author_email="info@merginmaps.com",
    description="Mergin Maps server",
    long_description="Mergin Maps server",
    packages=find_packages(),
    include_package_data=True,
    platforms="any",
    install_requires=[
        "connexion",
        "flask",
        "python-dateutil",
        "flask-marshmallow",
        "marshmallow-sqlalchemy",
        "psycopg2-binary",
        "itsdangerous",
        "Flask-SQLAlchemy",
        "zipfly",
        "python-dotenv",
        "flask-login",
        "bcrypt",
        "flask-wtf",
        "flask-mail",
        "safe",
        "wtforms-json",
        "pytz",
        "pygeodiff",
        "pathvalidate",
        "celery",
        "result",
        "binaryornot",
        "python-decouple",
        "urllib3",
        "shapely",
        "psycogreen",
    ],
)
