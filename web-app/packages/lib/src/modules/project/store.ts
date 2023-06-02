// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { AxiosResponse } from 'axios'
import FileSaver from 'file-saver'
import keyBy from 'lodash/keyBy'
import omit from 'lodash/omit'
import { defineStore } from 'pinia'

import { ProjectModule } from './module'

import { waitCursor } from '@/common/html_utils'
import { filesDiff } from '@/common/mergin_utils'
import { isAtLeastProjectRole, ProjectRole } from '@/common/permission_utils'
import { useNotificationStore } from '@/modules/notification/store'
import { ProjectApi } from '@/modules/project/projectApi'
import {
  AcceptProjectAccessRequestPayload,
  CancelProjectAccessRequestPayload,
  NamespaceAccessRequestsPayload,
  ProjectListItem,
  PaginatedProjectsPayload,
  ProjectAccessRequestResponse,
  ProjectsPayload,
  ProjectDetail,
  ProjectParams,
  EnhancedProjectDetail,
  ReloadProjectAccessRequestPayload
} from '@/modules/project/types'
import { useUserStore } from '@/modules/user/store'

interface File {
  chunks: any
}

export interface UploadFilesPayload {
  files: File[]
}

export interface ProjectState {
  accessRequests: ProjectAccessRequestResponse[] | undefined
  namespaceAccessRequests: ProjectAccessRequestResponse[] | undefined
  project: EnhancedProjectDetail
  projects: ProjectListItem[]
  projectsCount: number
  uploads: any
  currentNamespace: string
}

export const useProjectStore = defineStore('projectModule', {
  state: (): ProjectState => ({
    accessRequests: undefined,
    namespaceAccessRequests: undefined,
    project: null,
    projectsCount: 0,
    projects: undefined,
    uploads: {},
    currentNamespace: null
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
    },

    setNamespaceAccessRequests(payload) {
      this.namespaceAccessRequests = payload.accessRequests
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

    setProjectVersions(payload) {
      this.project.versions = payload.versions
    },

    initUpload(payload) {
      const upload = {
        files: payload.files ?? {},
        diff: null,
        analysingFiles: []
      }
      this.uploads[this.project.path] = upload
    },

    analysingFiles(payload) {
      const upload = this.uploads[this.project.path]
      upload.analysingFiles = payload.files
    },

    finishFileAnalysis(payload) {
      const upload = this.uploads[this.project.path]
      if (upload.analysingFiles) {
        upload.analysingFiles = upload.analysingFiles.filter(
          (p) => p !== payload.path
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
      this.uploads[this.project.path] = upload
    },

    discardUpload(payload) {
      delete this.uploads[payload.projectPath]
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
        this.uploads[this.project.path] = upload
      }

      payload.files.forEach((path) => {
        if (upload.files[path]) {
          delete upload.files[path]
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
        await ProjectModule.routerService.push({
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

    async deleteProject(payload) {
      const notificationStore = useNotificationStore()
      const userStore = useUserStore()

      try {
        waitCursor(true)
        await ProjectApi.deleteProject(
          payload.namespace,
          payload.projectName,
          true
        )
        this.setProject({ project: null })
        await userStore.fetchUserProfile()
        waitCursor(false)
        ProjectModule.routerService.replace({ path: '/' })
      } catch (e) {
        await notificationStore.error({
          text: e.response.data?.detail || 'Failed to remove project'
        })
        waitCursor(false)
      }
    },
    async initAccessRequests() {
      if (!(this.accessRequests?.length > 0)) {
        await this.fetchAccessRequests()
      }
    },

    async fetchAccessRequests() {
      const notificationStore = useNotificationStore()

      try {
        const accessRequestResponse = await ProjectApi.fetchAccessRequests()
        this.setAccessRequests({
          accessRequests: accessRequestResponse.data
        })
      } catch {
        await notificationStore.error({
          text: 'Failed to fetch project access requests'
        })
      }
    },

    async initNamespaceAccessRequests(payload: NamespaceAccessRequestsPayload) {
      if (!(this.namespaceAccessRequests?.length > 0)) {
        await this.fetchNamespaceAccessRequests(payload)
      }
    },

    async fetchNamespaceAccessRequests(
      payload: NamespaceAccessRequestsPayload
    ) {
      const notificationStore = useNotificationStore()

      try {
        const accessRequestResponse =
          await ProjectApi.fetchNamespaceAccessRequests(payload.namespace)
        this.setNamespaceAccessRequests({
          accessRequests: accessRequestResponse.data
        })
      } catch {
        await notificationStore.error({
          text: 'Failed to fetch project access requests'
        })
      }
    },

    async reloadProjectAccessRequests(
      payload: ReloadProjectAccessRequestPayload
    ) {
      if (payload.refetchGlobalAccessRequests) {
        if (payload.namespace) {
          await this.fetchNamespaceAccessRequests({
            namespace: payload.namespace
          })
        } else {
          await this.fetchAccessRequests()
        }
      } else {
        if (payload.namespace && payload.projectName) {
          // refetch project to update project access requests
          await this.fetchProject({
            projectName: payload.projectName,
            namespace: payload.namespace
          })
        } else {
          console.warn(
            'Cannot reload project access requests. Missing namespace or projectName.'
          )
        }
      }
    },

    async cancelProjectAccessRequest(
      payload: CancelProjectAccessRequestPayload
    ) {
      const notificationStore = useNotificationStore()

      waitCursor(true)
      try {
        await ProjectApi.cancelProjectAccessRequest(payload.itemId, true)
        await this.reloadProjectAccessRequests(payload)
      } catch (err) {
        const msg = err.response
          ? err.response.data?.detail
          : 'Failed to cancel access request'
        await notificationStore.error({ text: msg })
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
        await this.reloadProjectAccessRequests(payload)
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
        await ProjectModule.routerService.push({
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
        const msg = err.response
          ? err.response.data?.detail
          : 'Failed to unsubscribe from project'
        await notificationStore.error({ text: msg })
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
          await ProjectModule.routerService.push(
            `/login?redirect=/projects/${namespace}/${projectName}`
          )
        } else if (e.response.status === 403) {
          ProjectApi.fetchAccessRequests()
            .then((resp) => {
              for (const ar of resp.data) {
                if (
                  ar.namespace === namespace &&
                  ar.project_name === projectName
                ) {
                  callbackStatus(409)
                }
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

    async fetchProjectVersions(payload) {
      const notificationStore = useNotificationStore()

      try {
        const versionsResponse = await ProjectApi.fetchProjectVersions(
          payload.namespace,
          payload.projectName,
          payload.params
        )
        payload.cbSuccess(versionsResponse.data)
        this.setProjectVersions({ versions: versionsResponse.data?.versions })
      } catch (e) {
        await notificationStore.error({
          text: 'Failed to fetch project versions'
        })
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
        const msg = (err.response && err.response.data?.detail) || 'Error'
        await notificationStore.error({ text: msg })
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

    async downloadArchive(payload) {
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
    }
  }
})
