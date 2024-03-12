// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { RouteRecord } from 'vue-router'

/**
 * Enum for route names in the app's router.
 * Defines string constants for each route path used by project module.
 * Feel free to use it in application router as name attribute and in redirects from lib or app
 */
export enum ProjectRouteName {
  /**
   * Projects list
   * path: /projects
   */
  Projects = 'projects',
  /** Public projects */
  ProjectsExplore = 'explore',
  Projectsnamespace = 'namespace-projects',
  /** @deprecated */
  Blob = 'blob',
  /**
   * Detail of project
   * path: /projects/:namespace/:project
   */
  Project = 'project',
  /**
   * File browser
   * path: /projects/:namespace/:project/tree
   */
  ProjectTree = 'project-tree',
  ProjectSettings = 'project-settings',
  ProjectHistory = 'project-versions',
  ProjectCollaborators = 'project-collaborators',
  /** @deprecated */
  VersionDetail = 'project-versions-detail',
  FileVersionDetail = 'file-version-detail'
}

export default (): RouteRecord[] => []
