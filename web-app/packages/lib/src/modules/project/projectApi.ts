// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { AxiosResponse, CancelToken } from 'axios'

import { getDefaultRetryOptions, validateStatus } from '@/common/http'
import { ProjectModule } from '@/modules/project/module'
import {
  AcceptProjectAccessRequestData,
  CloneProjectParams,
  CreateProjectParams,
  FetchProjectVersionsParams,
  PaginatedProjectsParams,
  PaginatedProjectsResponse,
  PaginatedProjectVersions,
  ProjectAccessRequestResponse,
  ProjectAccessRequestParams,
  ProjectDetail,
  ProjectTemplate,
  PushProjectChangesParams,
  PushProjectChangesResponse,
  SaveProjectSettings,
  ProjectVersion,
  ProjectAccessDetail,
  ProjectAccess,
  ProjectVersionFileChange,
  UpdateProjectCollaboratorPayload,
  UpdatePublicFlagParams,
  ProjectCollaborator,
  AddProjectCollaboratorPayload
} from '@/modules/project/types'

export const ProjectApi = {
  async getProject(
    namespace: string,
    projectName: string
  ): Promise<AxiosResponse<ProjectDetail>> {
    return ProjectModule.httpService(`/v1/project/${namespace}/${projectName}`)
  },

  async createProject(
    namespace: string,
    data: CreateProjectParams,
    withRetry?: boolean
  ): Promise<AxiosResponse<void>> {
    return ProjectModule.httpService.post(`/v1/project/${namespace}`, data, {
      ...(withRetry ? getDefaultRetryOptions() : {})
    })
  },

  async cloneProject(
    namespace: string,
    projectName: string,
    data: CloneProjectParams,
    withRetry?: boolean
  ): Promise<AxiosResponse<void>> {
    return ProjectModule.httpService.post(
      `/v1/project/clone/${namespace}/${projectName}`,
      data,
      {
        ...(withRetry ? getDefaultRetryOptions() : {})
      }
    )
  },

  async deleteProject(
    id: string,
    withRetry?: boolean
  ): Promise<AxiosResponse<void>> {
    return ProjectModule.httpService.post(`/v2/projects/${id}/scheduleDelete`, {
      ...(withRetry ? getDefaultRetryOptions() : {})
    })
  },

  async unsubscribeProject(id: string): Promise<AxiosResponse<void>> {
    return ProjectModule.httpService.post(`/app/project/unsubscribe/${id}`)
  },

  async getProjectFileByUrl(url: string): Promise<AxiosResponse<string>> {
    return ProjectModule.httpService.get(url)
  },

  async getPaginatedProject(
    params: PaginatedProjectsParams
  ): Promise<AxiosResponse<PaginatedProjectsResponse>> {
    return ProjectModule.httpService('/v1/project/paginated', { params })
  },

  saveProjectSettings(
    namespace: string,
    projectName: string,
    data: SaveProjectSettings,
    withRetry?: boolean
  ): Promise<AxiosResponse<ProjectDetail>> {
    return ProjectModule.httpService.put(
      `/v1/project/${namespace}/${projectName}`,
      data,
      {
        ...(withRetry ? getDefaultRetryOptions() : {}),
        validateStatus
      }
    )
  },

  async fetchProjectVersions(
    workspace: string,
    projectName: string,
    params: FetchProjectVersionsParams
  ): Promise<AxiosResponse<PaginatedProjectVersions>> {
    return ProjectModule.httpService.get(
      `/v1/project/versions/paginated/${workspace}/${projectName}`,
      {
        params
      }
    )
  },

  /**
   * List of project access requests initiated by current user in session
   */
  async fetchAccessRequests(
    params: ProjectAccessRequestParams
  ): Promise<AxiosResponse<ProjectAccessRequestResponse>> {
    return ProjectModule.httpService('/app/project/access-requests', { params })
  },

  /**
   * Paginated list of incoming project access requests to workspace
   */
  async fetchNamespaceAccessRequests(
    namespace: string,
    params: ProjectAccessRequestParams
  ): Promise<AxiosResponse<ProjectAccessRequestResponse>> {
    return ProjectModule.httpService(
      `/app/project/access-request/${namespace}`,
      { params }
    )
  },

  async acceptProjectAccessRequest(
    itemId: number,
    data: AcceptProjectAccessRequestData,
    withRetry?: boolean
  ): Promise<AxiosResponse<void>> {
    return ProjectModule.httpService.post(
      `/app/project/access-request/accept/${itemId}`,
      data,
      {
        ...(withRetry ? getDefaultRetryOptions() : {})
      }
    )
  },
  async cancelProjectAccessRequest(
    itemId: number,
    withRetry?: boolean
  ): Promise<AxiosResponse<void>> {
    return ProjectModule.httpService.delete(
      `/app/project/access-request/${itemId}`,
      {
        ...(withRetry ? getDefaultRetryOptions() : {})
      }
    )
  },
  async createProjectAccessRequest(
    namespace: string,
    projectName: string,
    withRetry?: boolean
  ): Promise<AxiosResponse<void>> {
    return ProjectModule.httpService.post(
      `/app/project/access-request/${namespace}/${projectName}`,
      {},
      {
        ...(withRetry ? getDefaultRetryOptions() : {})
      }
    )
  },

  async addProjectCollaborator(
    id: string,
    data: AddProjectCollaboratorPayload
  ): Promise<AxiosResponse<ProjectCollaborator>> {
    return ProjectModule.httpService.post(
      `/v2/projects/${id}/collaborators`,
      data,
      {
        validateStatus
      }
    )
  },

  async updateProjectCollaborator(
    id: string,
    userId: number,
    data: UpdateProjectCollaboratorPayload
  ): Promise<AxiosResponse<ProjectCollaborator>> {
    return ProjectModule.httpService.patch(
      `/v2/projects/${id}/collaborators/${userId}`,
      data,
      {
        validateStatus
      }
    )
  },

  async updatePublicFlag(
    id: string,
    data: UpdatePublicFlagParams,
    withRetry?: boolean
  ): Promise<AxiosResponse<ProjectAccess>> {
    return ProjectModule.httpService.patch(`/app/project/${id}/public`, data, {
      ...(withRetry ? getDefaultRetryOptions() : {})
    })
  },

  async removeProjectCollaborator(
    id: string,
    userId: number
  ): Promise<AxiosResponse<void>> {
    return ProjectModule.httpService.delete(
      `/v2/projects/${id}/collaborators/${userId}`,
      {
        validateStatus
      }
    )
  },

  async pushProjectChanges(
    url: string,
    data: PushProjectChangesParams
  ): Promise<AxiosResponse<PushProjectChangesResponse>> {
    return ProjectModule.httpService.post(`/v1/project/push/${url}`, data)
  },

  async pushProjectChunks(
    transaction: string,
    chunk: string,
    token: CancelToken,
    data: object,
    withRetry?: boolean
  ): Promise<AxiosResponse<void>> {
    return ProjectModule.httpService.post(
      `/v1/project/push/chunk/${transaction}/${chunk}`,
      data,
      {
        cancelToken: token,
        ...(withRetry ? getDefaultRetryOptions() : {})
      }
    )
  },

  async pushFinishTransaction(
    transaction: string,
    token: CancelToken,
    withRetry?: boolean
  ): Promise<AxiosResponse<void>> {
    return ProjectModule.httpService.post(
      `/v1/project/push/finish/${transaction}`,
      null,
      {
        cancelToken: token,
        ...(withRetry ? getDefaultRetryOptions() : {})
      }
    )
  },

  async pushCancelTransaction(
    transaction: string
  ): Promise<AxiosResponse<void>> {
    return ProjectModule.httpService.post(
      `/v1/project/push/cancel/${transaction}`
    )
  },

  constructDownloadProjectUrl(projectId: string) {
    return ProjectModule.httpService.absUrl(
      `/app/projects/${projectId}/download`
    )
  },

  constructDownloadProjectVersionUrl(projectId: string, versionId: string) {
    return ProjectModule.httpService.absUrl(
      `/app/projects/${projectId}/download?version=${versionId}`
    )
  },

  constructDownloadProjectFileUrl(
    namespace: string,
    projectName: string,
    file: string
  ) {
    return ProjectModule.httpService.absUrl(
      `/v1/project/raw/${namespace}/${projectName}?file=${file}&random=${Math.random()}`
    )
  },

  async getProjectVersion(
    projectId: string,
    versionName: string
  ): Promise<AxiosResponse<ProjectVersion>> {
    return ProjectModule.httpService.get(
      `/v1/project/version/${projectId}/${versionName}`
    )
  },

  async getProjectTemplates(): Promise<AxiosResponse<ProjectTemplate[]>> {
    return ProjectModule.httpService.get('/app/project/templates')
  },

  async downloadFile(url: string): Promise<AxiosResponse<Blob>> {
    return ProjectModule.httpService.get(url, { responseType: 'blob' })
  },

  async prepareArchive(url: string): Promise<AxiosResponse<void>> {
    return ProjectModule.httpService.post(url)
  },

  /** Request head of file download */
  async getHeadDownloadFile(url: string): Promise<AxiosResponse<void>> {
    return ProjectModule.httpService.head(url)
  },

  // Kept for EE (collaborators + invitation) access, TODO: remove when a separate invitation endpoint is implemented
  async getProjectAccess(
    projectId: string
  ): Promise<AxiosResponse<ProjectAccessDetail[]>> {
    return ProjectModule.httpService.get(`/app/project/${projectId}/access`)
  },

  async getVersionChangeset(
    workspace: string,
    projectName: string,
    versionId: string,
    path: string
  ): Promise<AxiosResponse<ProjectVersionFileChange[]>> {
    return ProjectModule.httpService.get(
      `/v1/resource/changesets/${workspace}/${projectName}/${versionId}?path=${path}`
    )
  },

  async getProjectCollaborators(
    projectId: string
  ): Promise<AxiosResponse<ProjectCollaborator[]>> {
    return ProjectModule.httpService.get(
      `/v2/projects/${projectId}/collaborators`
    )
  }
}
