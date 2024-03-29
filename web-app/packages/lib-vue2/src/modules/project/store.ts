// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { AxiosResponse } from 'axios'
import FileSaver from 'file-saver'
import keyBy from 'lodash/keyBy'
import omit from 'lodash/omit'
import { defineStore, getActivePinia } from 'pinia'
import Vue from 'vue'

import { getErrorMessage } from '@/common/error_utils'
import { waitCursor } from '@/common/html_utils'
import { filesDiff } from '@/common/mergin_utils'
import { isAtLeastProjectRole, ProjectRole } from '@/common/permission_utils'
import { useNotificationStore } from '@/modules/notification/store'
import { ProjectApi } from '@/modules/project/projectApi'
import {
  AcceptProjectAccessRequestPayload,
  CancelProjectAccessRequestPayload,
  GetNamespaceAccessRequestsPayload,
  ProjectListItem,
  PaginatedProjectsPayload,
  ProjectsPayload,
  ProjectDetail,
  ProjectParams,
  EnhancedProjectDetail,
  FetchProjectVersionsPayload,
  ProjectVersion,
  ProjectVersionsPayload,
  ProjectAccessRequest,
  GetUserAccessRequestsPayload,
  GetProjectAccessRequestsPayload,
  DownloadPayload,
  DeleteProjectPayload
} from '@/modules/project/types'
import { useUserStore } from '@/modules/user/store'

interface File {
  chunks: unknown
}

export interface UploadFilesPayload {
  files: File[]
}

export interface ProjectState {
  accessRequests: ProjectAccessRequest[]
  accessRequestsCount: number
  project: EnhancedProjectDetail
  projects: ProjectListItem[]
  projectsCount: number
  uploads: any
  currentNamespace: string
  versions: ProjectVersion[]
  versionsCount: number
  versionsLoading: boolean
}

export const useProjectStore = defineStore('projectModule', {
  state: (): ProjectState => ({
    accessRequests: [],
    accessRequestsCount: 0,
    project: null,
    projectsCount: 0,
    projects: undefined,
    uploads: {},
    currentNamespace: null,
    versions: [],
    versionsCount: 0,
    versionsLoading: false
  }),

  getters: {
    isProjectOwner: (state) =>
      isAtLeastProjectRole(state.project?.role, ProjectRole.owner),
    getProjectByName(state) {
      return (payload) => {
        return state.projects?.find((project) => project.name === payload.name)
      }
    }
  },

  actions: {
    setAccessRequests(payload) {
      this.accessRequests = payload.accessRequests
      this.accessRequestsCount = payload.count
    },

    setProject(payload: { project: ProjectDetail }) {
      let enhancedProject: EnhancedProjectDetail = null
      if (payload.project) {
        enhancedProject = {
          ...omit(payload.project, ['files'])
        }
        if (enhancedProject) {
          enhancedProject.files = keyBy(payload.project.files, 'path')
          enhancedProject.path = [
            enhancedProject.namespace,
            enhancedProject.name
          ].join('/')
          const upload = this.uploads[enhancedProject.path]
          if (upload) {
            upload.diff = filesDiff(enhancedProject.files, upload.files)
          }
        }
      }
      this.project = enhancedProject
    },
    setProjects(payload: ProjectsPayload) {
      this.projects = payload.projects
      this.projectsCount = payload.count
    },
    setProjectVersions(payload: ProjectVersionsPayload) {
      this.versions = payload.versions
      this.versionsCount = payload.count
    },
    projectVersionsLoading(loading: boolean) {
      this.versionsLoading = loading
    },

    initUpload(payload) {
      const upload = {
        files: payload.files ?? {},
        diff: null,
        analysingFiles: []
      }
      Vue.set(this.uploads, this.project.path, upload)
    },

    analysingFiles(payload) {
      const upload = this.uploads[this.project.path]
      Vue.set(upload, 'analysingFiles', payload.files)
    },

    finishFileAnalysis(payload) {
      const upload = this.uploads[this.project.path]
      if (upload.analysingFiles) {
        Vue.set(
          upload,
          'analysingFiles',
          upload.analysingFiles.filter((p) => p !== payload.path)
        )
      }
    },

    uploadFiles(payload: UploadFilesPayload) {
      let files = payload.files
      files = keyBy(files, 'path')
      const chunks = Object.values(files)
        .filter((f) => f.chunks !== undefined)
        .map((f) => f.chunks.length)
        .reduce((sum, item) => sum + item)
      const upload = {
        files,
        diff: filesDiff(this.project.files, files),
        running: false,
        progress: 0,
        loaded: 0,
        total: chunks
      }
      Vue.set(this.uploads, this.project.path, upload)
    },

    discardUpload(payload) {
      Vue.delete(this.uploads, payload.projectPath)
    },

    startUpload() {
      const upload = this.uploads[this.project.path]
      if (upload) {
        upload.running = true
        upload.progress = 0
      }
    },

    chunkUploaded(payload) {
      const upload = this.uploads[payload.project]
      if (upload) {
        upload.loaded++
        if (upload.loaded === upload.total) {
          upload.running = false
        }
      }
    },

    cancelUpload() {
      const upload = this.uploads[this.project.path]
      if (upload) {
        upload.running = false
        upload.progress = 0
      }
    },

    deleteFiles(payload) {
      let upload = this.uploads[this.project.path]
      if (!upload) {
        upload = {
          files: { ...this.project.files },
          diff: filesDiff({}, {})
        }
        Vue.set(this.uploads, this.project.path, upload)
      }

      payload.files.forEach((path) => {
        if (upload.files[path]) {
          Vue.delete(upload.files, path)
        } else {
          // should be folder
          const dirPrefix = path + '/'
          const removed = Object.keys(upload.files).filter((path) =>
            path.startsWith(dirPrefix)
          )
          upload.files = omit(upload.files, removed)
        }
      })
      upload.diff = filesDiff(this.project.files, upload.files)
    },

    setCurrentNamespace(payload) {
      this.currentNamespace = payload.currentNamespace
    },

    async initProjects(payload: PaginatedProjectsPayload) {
      if (!(this.projects?.length > 0)) {
        await this.getProjects(payload)
      }
    },

    async getProjects(payload: PaginatedProjectsPayload) {
      const notificationStore = useNotificationStore()

      let response
      try {
        response = await ProjectApi.getPaginatedProject(payload.params)
        this.setProjects({
          projects: response.data?.projects,
          count: response.data?.count
        })
      } catch (_err) {
        await notificationStore.error({
          text: 'Failed to load projects'
        })
      }
      return response
    },

    clearProjects() {
      this.setProjects({ projects: [], count: 0 })
      this.setProject({ project: null })
    },

    async createProject(payload) {
      waitCursor(true)
      try {
        await ProjectApi.createProject(payload.namespace, payload.data, true)
        this.setProject({ project: null })
        await getActivePinia().router.push({
          name: 'project',
          params: {
            namespace: payload.namespace,
            projectName: payload.data.name
          }
        })
      } finally {
        waitCursor(false)
      }
    },

    async deleteProject(payload: DeleteProjectPayload) {
      const notificationStore = useNotificationStore()
      const userStore = useUserStore()

      try {
        waitCursor(true)
        await ProjectApi.deleteProject(payload.projectId, true)
        this.setProject({ project: null })
        await userStore.fetchUserProfile()
        waitCursor(false)
        getActivePinia().router.replace({ path: '/' })
      } catch (e) {
        await notificationStore.error({
          text: getErrorMessage(e, 'Failed to remove project')
        })
        waitCursor(false)
      }
    },
    async initUserAccessRequests(payload?: GetUserAccessRequestsPayload) {
      await this.fetchUserAccessRequests({
        params: {
          page: 1,
          per_page: 10,
          order_params: 'expire DESC',
          ...payload?.params
        }
      })
    },

    async fetchUserAccessRequests(payload: GetUserAccessRequestsPayload) {
      const notificationStore = useNotificationStore()

      try {
        const accessRequestResponse = await ProjectApi.fetchAccessRequests(
          payload.params
        )
        this.setAccessRequests({
          accessRequests: accessRequestResponse.data?.items,
          count: accessRequestResponse.data?.count
        })
      } catch {
        await notificationStore.error({
          text: 'Failed to fetch project access requests'
        })
      }
    },

    async initNamespaceAccessRequests(
      payload: GetNamespaceAccessRequestsPayload
    ) {
      await this.fetchNamespaceAccessRequests({
        ...payload,
        params: {
          page: 1,
          per_page: 10,
          order_params: 'expire DESC',
          ...payload.params
        }
      })
    },

    async fetchNamespaceAccessRequests(
      payload: GetNamespaceAccessRequestsPayload
    ) {
      const notificationStore = useNotificationStore()

      try {
        const accessRequestResponse =
          await ProjectApi.fetchNamespaceAccessRequests(
            payload.namespace,
            payload.params
          )
        this.setAccessRequests({
          accessRequests: accessRequestResponse.data?.items,
          count: accessRequestResponse.data?.count
        })
      } catch {
        await notificationStore.error({
          text: 'Failed to fetch project access requests'
        })
      }
    },

    async getProjectAccessRequests(payload: GetProjectAccessRequestsPayload) {
      if (payload.namespace) {
        await this.fetchNamespaceAccessRequests({
          namespace: payload.namespace,
          ...payload
        })
      } else {
        await this.fetchUserAccessRequests(payload)
      }
    },

    async cancelProjectAccessRequest(
      payload: CancelProjectAccessRequestPayload
    ) {
      const notificationStore = useNotificationStore()

      waitCursor(true)
      try {
        await ProjectApi.cancelProjectAccessRequest(payload.itemId, true)
      } catch (err) {
        await notificationStore.error({
          text: getErrorMessage(err, 'Failed to cancel access request')
        })
      } finally {
        waitCursor(false)
      }
    },

    async acceptProjectAccessRequest(
      payload: AcceptProjectAccessRequestPayload
    ) {
      waitCursor(true)
      try {
        await ProjectApi.acceptProjectAccessRequest(
          payload.itemId,
          payload.data,
          true
        )
      } finally {
        waitCursor(false)
      }
    },

    async cloneProject(payload) {
      const { namespace, project, data, cbSuccess } = payload
      try {
        waitCursor(true)
        await ProjectApi.cloneProject(namespace, project, data)
        waitCursor(false)
        cbSuccess()
        this.setProject({ project: null })
        await getActivePinia().router.push({
          name: 'project',
          params: {
            namespace: data.namespace,
            projectName: data.project
          }
        })
      } catch (err) {
        waitCursor(false)
        throw err
      }
    },

    async fetchProject(payload: ProjectParams) {
      const notificationStore = useNotificationStore()

      try {
        const projectResponse = await ProjectApi.fetchProject(
          payload.namespace,
          payload.projectName
        )
        this.setProject({ project: projectResponse.data })
      } catch (e) {
        console.warn('Failed to load project data', e)
        await notificationStore.error({ text: 'Failed to load project data' })
      }
    },

    async unsubscribeProject(payload) {
      const notificationStore = useNotificationStore()

      try {
        waitCursor(true)
        await ProjectApi.unsubscribeProject(payload.id)
        this.setProject({ project: null })
        waitCursor(false)
      } catch (err) {
        await notificationStore.error({
          text: getErrorMessage(err, 'Failed to unsubscribe from project')
        })
        waitCursor(false)
      }
    },

    async fetchProjectDetail(payload) {
      const notificationStore = useNotificationStore()

      const { callbackStatus, namespace, projectName, isLoggedUser } = payload
      try {
        const projectResponse = await ProjectApi.fetchProject(
          payload.namespace,
          payload.projectName
        )
        this.setProject({ project: projectResponse.data })
      } catch (e) {
        callbackStatus(e.response.status)

        if (e.response.status !== 404 && e.response.status !== 403) {
          notificationStore.error({
            text: 'Failed to load project data'
          })
        } else if (e.response.status === 403 && !isLoggedUser) {
          await getActivePinia().router.push(
            `/login?redirect=/projects/${namespace}/${projectName}`
          )
        } else if (e.response.status === 403) {
          ProjectApi.fetchAccessRequests({
            page: 1,
            per_page: 1,
            project_name: payload.projectName
          })
            .then((resp) => {
              if (resp.data.count) {
                callbackStatus(409)
              }
            })
            .catch(() => {
              notificationStore.error({
                text: 'Failed to load project access requests data'
              })
            })
        }
      }
    },

    async fetchProjectVersions(payload: FetchProjectVersionsPayload) {
      const notificationStore = useNotificationStore()

      try {
        this.projectVersionsLoading(true)
        const response = await ProjectApi.fetchProjectVersions(
          payload.namespace,
          payload.projectName,
          payload.params
        )
        this.setProjectVersions({
          versions: response.data?.versions,
          count: response.data?.count
        })
      } catch (e) {
        await notificationStore.error({
          text: 'Failed to fetch project versions'
        })
      } finally {
        this.projectVersionsLoading(false)
      }
    },

    async saveProjectSettings(payload): Promise<AxiosResponse<ProjectDetail>> {
      const { namespace, newSettings, projectName } = payload

      try {
        waitCursor(true)
        const saveProjectSettingsResponse =
          await ProjectApi.saveProjectSettings(
            namespace,
            projectName,
            newSettings,
            true
          )
        this.setProject({ project: saveProjectSettingsResponse.data })
        waitCursor(false)
        return saveProjectSettingsResponse
      } finally {
        waitCursor(false)
      }
    },

    async pushProjectChunks(payload) {
      const pushProjectChunksResponse = await ProjectApi.pushProjectChunks(
        payload.transaction,
        payload.chunk,
        payload.token,
        payload.data,
        true
      )
      this.chunkUploaded({ project: payload.projectPath })
      return pushProjectChunksResponse
    },

    async pushFinishTransaction(payload) {
      const notificationStore = useNotificationStore()
      const userStore = useUserStore()

      const { projectPath, token, transaction } = payload
      try {
        const pushFinishTransactionResponse =
          await ProjectApi.pushFinishTransaction(transaction, token, true)
        this.discardUpload({ projectPath })
        notificationStore.show({
          text: `Upload finished: ${projectPath}`
        })
        this.setProject({ project: pushFinishTransactionResponse.data })
        await userStore.fetchUserProfile()
        waitCursor(false)
      } catch (err) {
        this.pushCancelTransaction({ err, transaction })
      }
    },

    async pushProjectChanges(payload) {
      const notificationStore = useNotificationStore()

      const { data, projectPath } = payload
      try {
        return await ProjectApi.pushProjectChanges(projectPath, data)
      } catch (err) {
        await notificationStore.error({ text: getErrorMessage(err, 'Error') })
        return undefined
      }
    },

    async pushCancelTransaction(payload) {
      const notificationStore = useNotificationStore()

      const { err, transaction } = payload
      this.cancelUpload()
      const msg = err.__CANCEL__
        ? err.message
        : (err.response && err.response.data?.detail) || 'Error'
      notificationStore.error({ text: msg })
      await ProjectApi.pushCancelTransaction(transaction)
      waitCursor(false)
    },

    async downloadArchive(payload: DownloadPayload) {
      const notificationStore = useNotificationStore()

      try {
        const resp = await ProjectApi.downloadFile(payload.url)
        const fileName =
          resp.headers['content-disposition'].split('filename=')[1]
        FileSaver.saveAs(resp.data, fileName)
      } catch (e) {
        // parse error details from blob
        let resp
        const blob = new Blob([e.response.data], { type: 'text/plain' })
        blob.text().then((text) => {
          resp = JSON.parse(text)
          notificationStore.error({ text: resp.detail })
        })
      }
    },

    constructDownloadProjectUrl(payload: {
      namespace: string
      projectName: string
    }) {
      return ProjectApi.constructDownloadProjectUrl(
        payload.namespace,
        payload.projectName
      )
    }
  }
})
