// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

/* eslint-disable camelcase */
import {
  ProjectRoleName,
  ProjectPermissionName,
  WorkspaceRoleName
} from '@/common/permission_utils'
import {
  PaginatedRequestParamsApi,
  PaginatedResponse,
  PaginatedResponseDefaults
} from '@/common/types'
import { UserSearch } from '@/modules/user/types'

export interface ProjectGridState {
  searchFilterByProjectName: string
  namespace: string
}

export interface PaginatedProjectsParams extends PaginatedRequestParamsApi {
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
  editors: number[]
  editorsnames: string[]
}

export type ProjectTags = 'valid_qgis' | 'mappin_use' | 'input_use'

export interface Project {
  name: string
  created?: string
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
  workspace_id: number
}

export interface PaginatedProjectsResponse extends PaginatedResponseDefaults {
  projects: ProjectListItem[]
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

export interface AccessRequest {
  expire: string
  id: number
  namespace: string
  project?: string
  project_name: string
  requested_by: string
  user: UserSearch
}

export type ProjectAccessRequestResponse = PaginatedResponse<AccessRequest>

export interface ProjectAccessRequestParams extends PaginatedRequestParamsApi {
  project_name?: string
}

export interface AccessRequestsPayload extends PaginatedResponseDefaults {
  accessRequests: AccessRequest[]
}

export interface GetUserAccessRequestsPayload {
  params: ProjectAccessRequestParams
}

export interface GetNamespaceAccessRequestsPayload {
  namespace: string
  params: ProjectAccessRequestParams
}

export interface AcceptProjectAccessRequestData {
  permissions: ProjectPermissionName
}

export interface GetAccessRequestsPayload extends GetUserAccessRequestsPayload {
  namespace?: string
}

export interface AcceptProjectAccessRequestPayload {
  itemId: number
  data: AcceptProjectAccessRequestData
  workspace?: string
}

export interface CancelProjectAccessRequestPayload {
  itemId: number
  workspace: string
}

export interface CreateProjectParams {
  name: string
  public?: boolean
  template?: string
}

export interface AccessUpdate {
  ownersnames: string[]
  writersnames: string[]
  editorsnames: string[]
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
  project_size: number
}

export type ProjectVersionListItem = Omit<
  ProjectVersion,
  'changesets' | 'changes'
> & {
  changes: {
    added: number
    removed: number
    updated: number
    updated_diff: number
  }
}

export interface PaginatedProjectVersions extends PaginatedResponseDefaults {
  versions: ProjectVersionListItem[]
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

export interface AddProjectCollaboratorPayload {
  role: ProjectRoleName
  user: string
}

export interface UpdateProjectCollaboratorPayload {
  role: ProjectRoleName
}

export interface UpdatePublicFlagParams {
  public?: boolean
}

export interface DownloadPayload {
  url: string
  versionId?: string
}

export interface FetchProjectVersionsPayload {
  workspace: string
  projectName: string
  params: FetchProjectVersionsParams
}

export interface ProjectVersionsTableItem extends ProjectVersionListItem {
  disabled: boolean
}

export interface DeleteProjectPayload {
  projectId: string
}

export interface VDataIteratorOptions {
  page: number
  itemsPerPage: number
  sortBy?: Array<{ key: string; order?: boolean | 'asc' | 'desc' }>
}

export interface SortingParams {
  sortBy: string
  sortDesc: boolean
}

export interface ProjectVersionFileChange {
  changes: {
    columns: number
    name: string
    new: string
  }[]
  table: string
  type: 'insert' | 'update' | 'delete'
}

export type ErrorCodes = 'UpdateProjectAccessError'

export type ProjectAccessDetailType = 'invitation' | 'member'

export interface ProjectAccessDetail {
  id: number | string
  type: ProjectAccessDetailType
  workspace_role: WorkspaceRoleName
  name?: string
  email: string
  username?: string
  role?: ProjectRoleName
  project_role?: ProjectRoleName | null
  invitation?: {
    expires_at: string
    projects?: {
      ids: string[]
      permissions: ProjectPermissionName
    }
  }
  last_signed_in: string
}

export interface ProjectCollaborator {
  id: number
  email: string
  username: string
  workspace_role: WorkspaceRoleName
  project_role: ProjectRoleName | null
  role: ProjectRoleName
  fullname: string
}

// router related types
export interface ProjectRouteParams {
  namespace?: string
  projectName?: string
  version_id?: string
  path?: string
}

export interface ProjectRouteQuery {
  version_id?: string
  file_path?: string
}
