# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import shutil
import sys
import click
import os
import secrets
from datetime import datetime
from flask import Flask, current_app
from sqlalchemy import func

from .files import UploadChanges
from ..app import db
from .models import Project, ProjectVersion
from .utils import split_project_path
from ..auth.models import User
from ..utils import normalize_input


def add_commands(app: Flask):
    @app.cli.group()
    def project():
        """Project management commands."""
        pass

    @project.command()
    @click.argument("name", callback=normalize_input(lowercase=False))
    @click.argument("namespace", callback=normalize_input())
    @click.argument("username", callback=normalize_input())
    def create(name, namespace, username):  # pylint: disable=W0612
        """Create blank project"""
        workspace = current_app.ws_handler.get_by_name(namespace)
        if not workspace:
            click.secho("ERROR: Workspace not found", fg="red", err=True)
            sys.exit(1)
        user = User.query.filter(func.lower(User.username) == username).first()
        if not user:
            click.secho("ERROR: User not found", fg="red", err=True)
            sys.exit(1)
        p = Project.query.filter_by(name=name, workspace_id=workspace.id).first()
        if p:
            click.secho("ERROR: Project name already exists", fg="red", err=True)
            sys.exit(1)
        project_params = dict(
            creator=user,
            name=name,
            workspace=workspace,
            storage_params={
                "type": "local",
                "location": os.path.join(secrets.token_hex(1), secrets.token_hex(16)),
            },
        )
        p = Project(**project_params)
        p.updated = datetime.utcnow()
        db.session.add(p)
        changes = UploadChanges(added=[], updated=[], removed=[])
        pv = ProjectVersion(p, 0, user.id, changes, "127.0.0.1")
        db.session.add(pv)
        db.session.commit()
        os.makedirs(p.storage.project_dir, exist_ok=True)
        click.secho("Project created", fg="green")

    @project.command()
    @click.argument("project-name", callback=normalize_input(lowercase=False))
    @click.option("--version", type=int, required=True)
    @click.option(
        "--directory",
        type=click.Path(),
        required=True,
        callback=normalize_input(lowercase=False),
    )
    def download(project_name, version, directory):  # pylint: disable=W0612
        """Download files for project at particular version"""
        ws, name = split_project_path(project_name)
        workspace = current_app.ws_handler.get_by_name(ws)
        project = (
            Project.query.filter_by(workspace_id=workspace.id, name=name)
            .filter(Project.storage_params.isnot(None))
            .first()
        )
        if not project:
            click.secho("ERROR: Project does not exist", fg="red", err=True)
            sys.exit(1)
        pv = ProjectVersion.query.filter_by(project_id=project.id, name=version).first()
        if not pv:
            click.secho("ERROR: Project version does not exist", fg="red", err=True)
            sys.exit(1)
        if os.path.exists(directory):
            click.secho(
                f"ERROR: Destination directory '{directory}' already exist",
                fg="red",
                err=True,
            )
            sys.exit(1)

        os.mkdir(directory)
        files = pv.files
        for f in files:
            project.storage.restore_versioned_file(f.path, version)
            f_dir = os.path.dirname(f.path)
            if f_dir:
                os.makedirs(os.path.join(directory, f_dir), exist_ok=True)
            shutil.copy(
                os.path.join(project.storage.project_dir, f.location),
                os.path.join(directory, f.path),
            )
        click.secho("Project downloaded", fg="green")

    @project.command()
    @click.argument("project-name", callback=normalize_input(lowercase=False))
    def remove(project_name):
        """Delete a project"""
        ws, name = split_project_path(project_name)
        workspace = current_app.ws_handler.get_by_name(ws)
        if not workspace:
            click.secho("ERROR: Workspace does not exist", fg="red", err=True)
            sys.exit(1)
        project = (
            Project.query.filter_by(workspace_id=workspace.id, name=name)
            .filter(Project.storage_params.isnot(None))
            .first()
        )
        if not project:
            click.secho("ERROR: Project does not exist", fg="red", err=True)
            sys.exit(1)
        project.removed_at = datetime.utcnow()
        project.removed_by = None
        db.session.commit()
        click.secho("Project removed", fg="green")
