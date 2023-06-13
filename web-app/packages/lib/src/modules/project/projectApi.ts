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
  PaginatedAdminProjectsParams,
  PaginatedAdminProjectsResponse,
  PaginatedProjectsParams,
  PaginatedProjectsResponse,
  PaginatedProjectVersionsResponse,
  ProjectAccessRequestResponse,
  ProjectDetail,
  ProjectTemplate,
  PushProjectChangesParams,
  PushProjectChangesResponse,
  SaveProjectSettings,
  UpdateProjectAccessParams
} from '@/modules/project/types'
import { PaginatedRequestParams } from '@/common'

export const ProjectApi = {
  async fetchProject(
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
    namespace: string,
    projectName: string,
    withRetry?: boolean
  ): Promise<AxiosResponse<void>> {
    return ProjectModule.httpService.delete(
      `/v1/project/${namespace ? `${namespace}/${projectName}` : projectName}`,
      {
        ...(withRetry ? getDefaultRetryOptions() : {})
      }
    )
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

  // TODO: refactor to admin-lib?
  async getPaginatedAdminProject(
    params: PaginatedAdminProjectsParams
  ): Promise<AxiosResponse<PaginatedAdminProjectsResponse>> {
    return ProjectModule.httpService('/app/admin/projects', { params })
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
    namespace: string,
    projectName: string,
    params: FetchProjectVersionsParams
  ): Promise<AxiosResponse<PaginatedProjectVersionsResponse>> {
    return ProjectModule.httpService.get(
      `/v1/project/versions/paginated/${namespace}/${projectName}`,
      { params }
    )
  },

  /**
   * List of project access requests initiated by current user in session
   */
  async fetchAccessRequests(
    params: PaginatedRequestParams
  ): Promise<AxiosResponse<ProjectAccessRequestResponse>> {
    return ProjectModule.httpService('/app/project/access-requests', { params })
  },

  /**
   * Paginated list of incoming project access requests to workspace
   */
  async fetchNamespaceAccessRequests(
    namespace: string,
    params: PaginatedRequestParams
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

  async updateProjectAccessForUser(
    id: string,
    data: UpdateProjectAccessParams,
    withRetry?: boolean
  ): Promise<AxiosResponse<void>> {
    return ProjectModule.httpService.patch(`/app/project/${id}/access`, data, {
      ...(withRetry ? getDefaultRetryOptions() : {})
    })
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
    data: any,
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

  constructDownloadProjectUrl(namespace: string, projectName: string) {
    return ProjectModule.httpService.absUrl(
      `/v1/project/download/${namespace}/${projectName}?format=zip`
    )
  },

  constructDownloadProjectVersionUrl(
    namespace: string,
    projectName: string,
    versionId: string
  ) {
    return ProjectModule.httpService.absUrl(
      `/v1/project/download/${namespace}/${projectName}?version=${versionId}&format=zip`
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
  ): Promise<AxiosResponse<string>> {
    return ProjectModule.httpService.get(
      `/v1/project/version/${projectId}/${versionName}`
    )
  },

  async getProjectTemplates(): Promise<AxiosResponse<ProjectTemplate[]>> {
    return ProjectModule.httpService.get('/app/project/templates')
  },

  /**
   * Permanently remove project
   * @param id removed project id
   * @return Result promise
   */
  async removeProject(id: number): Promise<AxiosResponse<void>> {
    return await ProjectModule.httpService.delete(
      `/app/project/removed-project/${id}`,
      {
        'axios-retry': { retries: 5 }
      }
    )
  },

  /**
   * Restore removed project
   * @param id (Int) removed project id
   * @return Result promise
   */
  async restoreProject(id: number): Promise<AxiosResponse<void>> {
    return await ProjectModule.httpService.post(
      `/app/project/removed-project/restore/${id}`,
      null,
      { 'axios-retry': { retries: 5 } }
    )
  },

  async downloadFile(url: string): Promise<AxiosResponse<Blob>> {
    return ProjectModule.httpService.get(url, { responseType: 'blob' })
  }
}
