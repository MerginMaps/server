// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { RouteLocationNormalizedLoaded, RouteRecord } from 'vue-router'

import { ProjectRouteParams, ProjectRouteQuery } from './types'

import { DEFAULT_PAGE_TITLE } from '@/common/route_utils'

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

export const getProjectTitle = (route: RouteLocationNormalizedLoaded) => {
  const name = route.name as ProjectRouteName
  const params = route.params as ProjectRouteParams
  const query = route.query as ProjectRouteQuery
  const { projectName, path, version_id } = params as ProjectRouteParams
  const titles: Record<ProjectRouteName, string | string[]> = {
    [ProjectRouteName.Projects]: ['Projects'],
    [ProjectRouteName.ProjectsExplore]: ['Public projects'],
    [ProjectRouteName.Project]: ['Project details'],
    [ProjectRouteName.ProjectTree]: [
      query.file_path || 'Files',
      route.params.projectName as string
    ],
    [ProjectRouteName.ProjectSettings]: ['Settings', projectName],
    [ProjectRouteName.ProjectHistory]: [
      query.version_id || 'History',
      projectName
    ].filter(Boolean),
    [ProjectRouteName.ProjectCollaborators]: ['Collaborators', projectName],
    [ProjectRouteName.FileVersionDetail]: [
      path,
      `Version ${version_id as string}`
    ],
    [ProjectRouteName.VersionDetail]: DEFAULT_PAGE_TITLE,
    [ProjectRouteName.Blob]: DEFAULT_PAGE_TITLE
  }
  return titles[name]
}

export default (): RouteRecord[] => []
