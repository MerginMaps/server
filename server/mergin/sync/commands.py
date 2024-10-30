# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import shutil
import click
import os
import secrets
from datetime import datetime
from flask import Flask, current_app

from .files import UploadChanges
from .. import db
from .models import Project, ProjectAccess, ProjectVersion
from .utils import split_project_path


def add_commands(app: Flask):
    @app.cli.group()
    def project():
        """Project management commands."""
        pass

    @project.command()
    @click.argument("name")
    @click.argument("namespace")
    @click.argument("user")
    def create(name, namespace, user):  # pylint: disable=W0612
        """Create blank project"""
        workspace = current_app.ws_handler.get_by_name(namespace)
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
        p.access = ProjectAccess(p, public=False)
        changes = UploadChanges(added=[], updated=[], removed=[])
        pv = ProjectVersion(p, 0, user.id, changes, "127.0.0.1")
        pv.project = p
        db.session.commit()
        os.makedirs(p.storage.project_dir, exist_ok=True)
        print("Project created")

    @project.command()
    @click.argument("project-name")
    @click.option("--version", required=True)
    @click.option("--directory", type=click.Path(), required=True)
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
            print("ERROR: Project does not exist")
            return
        pv = ProjectVersion.query.filter_by(project_id=project.id, name=version).first()
        if not pv:
            print("ERROR:Project version does not exist")
            return
        if os.path.exists(directory):
            print(f"ERROR: Destination directory {directory} already exist")
            return

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
        print("Project downloaded successfully")

    @project.command()
    @click.argument("project-name")
    def remove(project_name):
        """Delete a project"""
        ws, name = split_project_path(project_name)
        workspace = current_app.ws_handler.get_by_name(ws)
        if not workspace:
            print("ERROR: Workspace does not exist")
            return
        project = (
            Project.query.filter_by(workspace_id=workspace.id, name=name)
            .filter(Project.storage_params.isnot(None))
            .first()
        )
        if not project:
            print("ERROR: Project does not exist")
            return
        project.removed_at = datetime.utcnow()
        project.removed_by = None
        db.session.commit()
        print("Project removed successfully")
