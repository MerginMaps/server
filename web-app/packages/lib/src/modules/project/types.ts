// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

/* eslint-disable camelcase */
import {
  ProjectRoleName,
  ProjectPermissionName
} from '@/common/permission_utils'
import {
  PaginatedRequestParams,
  PaginatedRequestParamsApi,
  PaginatedResponse,
  PaginatedResponseDefaults
} from '@/common/types'
import { UserSearch } from '@/modules/user/types'

export interface ProjectGridState {
  searchFilterByProjectName: string
  searchFilterByNamespace: string
  namespace: string
  searchFilterByDay: number
}

export interface PaginatedProjectsParams extends PaginatedRequestParams {
  descending?: boolean
  namespace?: string
  only_namespace?: string
  name?: string
  user?: string
  last_updated_in?: number
  flag?: string
  as_admin?: boolean
  public?: boolean
  only_public?: boolean
}

export interface PaginatedAdminProjectsParams extends PaginatedRequestParams {
  workspace?: string
  name?: string
}

export interface ProjectItemPermissions {
  delete: boolean
  update: boolean
  upload: boolean
}

export interface ProjectAccess {
  owners: number[]
  ownersnames: string[]
  public: boolean
  readers: number[]
  readersnames: string[]
  writers: number[]
  writersnames: string[]
}

export type ProjectTags = 'valid_qgis' | 'mappin_use' | 'input_use'

export interface Project {
  name: string
  created?: string
}

export interface AdminProjectListItem extends Project {
  disk_usage: number
  id: string
  name: string
  namespace: string
  updated: string
  version: string
  removed_at: string
  removed_by: string
}

export interface ProjectListItem extends Project {
  access: ProjectAccess
  creator: number | null
  disk_usage: number
  has_conflict: boolean
  id: string
  name: string
  namespace: string
  permissions: ProjectItemPermissions
  tags: ProjectTags[]
  updated: string
  version: string
}

export interface FileInfo {
  path: string
  checksum: string
  size: number
  mtime?: string
}

export interface FileDiff {
  path: string
  checksum: string
  size?: number
}

export interface UpdateFileInfo extends FileInfo, FileDiff {
  // specified size again with required modifier
  size: number
}

export interface UploadFileInfo extends FileInfo {
  chunks: string[]
}

export type FileChangeType = 'added' | 'updated' | 'removed'

export interface FileInfoHistory extends UpdateFileInfo {
  change: FileChangeType
  expiration?: string
}

export interface HistoryFileInfo {
  path?: string
  checksum?: string
  size?: number
  mtime?: string
  diff?: FileDiff
  history?: FileInfoHistory
}

export interface ProjectListItemFiles extends FileInfo, HistoryFileInfo {
  // specified size again with required modifier
  path: string
  checksum: string
  size: number
}

export interface ProjectDetail extends ProjectListItem {
  role: ProjectRoleName
  files?: ProjectListItemFiles[]
}

export interface PaginatedProjectsResponse extends PaginatedResponseDefaults {
  projects: ProjectListItem[]
}

export interface PaginatedAdminProjectsResponse
  extends PaginatedResponseDefaults {
  projects: AdminProjectListItem[]
}

export interface PaginatedProjectsPayload {
  params: PaginatedProjectsParams
}

export interface ProjectsPayload extends PaginatedResponseDefaults {
  projects: ProjectListItem[]
}

export interface CloneProjectParams {
  project: string
  namespace: string
  merginComponentUuid: string
}

export interface ProjectParams {
  projectName: string
  namespace: string
}

export interface ProjectAccessRequest {
  expire: string
  id: number
  namespace: string
  project?: string
  project_name: string
  requested_by: string
  user: UserSearch
}

export type ProjectAccessRequestResponse =
  PaginatedResponse<ProjectAccessRequest>

export interface AccessRequestsPayload extends PaginatedResponseDefaults {
  accessRequests: ProjectAccessRequest[]
}

export interface GetUserAccessRequestsPayload {
  params: PaginatedRequestParamsApi
}

export interface GetNamespaceAccessRequestsPayload {
  namespace: string
  params: PaginatedRequestParamsApi
}

export interface AcceptProjectAccessRequestData {
  permissions: ProjectPermissionName
}

export interface GetProjectAccessRequestsPayload
  extends GetUserAccessRequestsPayload {
  namespace?: string
}

export interface AcceptProjectAccessRequestPayload {
  itemId: number
  data: AcceptProjectAccessRequestData
  namespace?: string
}

export interface CancelProjectAccessRequestPayload {
  itemId: number
  namespace: string
}

export interface CreateProjectParams {
  name: string
  public?: boolean
  template?: string
}

export interface AccessUpdate {
  ownersnames: string[]
  writersnames: string[]
  readersnames: string[]
  public: boolean
}

export interface SaveProjectSettings {
  access: AccessUpdate
}

export interface FetchProjectVersionsParams {
  page: number
  per_page: number
  descending: boolean
}

export interface ChangesetError {
  size?: number
  error?: string
}

export interface ChangesetSuccessSummaryItem {
  table?: string
  insert?: number
  update?: number
  delete?: number
}

export interface ChangesetSuccess {
  size?: number
  summary?: ChangesetSuccessSummaryItem[]
}

export interface ProjectVersion {
  name: string
  author: string
  created: string
  changes: {
    added: FileInfo[]
    removed: FileInfo[]
    updated: FileInfo[]
  }
  project_name: string
  namespace: string
  user_agent: string
  changesets: ChangesetSuccess | ChangesetError
}

export interface PaginatedProjectVersionsResponse
  extends PaginatedResponseDefaults {
  versions: ProjectVersion[]
}

export interface PushProjectChangesParams {
  version: string
  changes: {
    added: UploadFileInfo[]
    removed: FileInfo[]
    updated: UpdateFileInfo[]
  }
}

export type PushProjectChangesResponse =
  | ProjectDetail
  | {
      transaction: string
    }

export interface ProjectTemplate {
  id: string
  name: string
  namespace: string
  version: string
}

export type EnhancedProjectDetail = ProjectDetail & {
  files: Record<string, ProjectListItemFiles>
  path: string
}

export interface UpdateProjectAccessParams {
  user_id: number
  role: ProjectRoleName
}

export interface FetchProjectVersionsPayload extends ProjectParams {
  params: FetchProjectVersionsParams
}

export interface ProjectVersionsPayload extends PaginatedResponseDefaults {
  versions: ProjectVersion[]
}

export interface ProjectVersionsItem extends ProjectVersion {
  disabled: boolean
}
