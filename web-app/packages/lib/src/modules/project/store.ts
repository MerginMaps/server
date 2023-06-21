// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { AxiosResponse } from 'axios'
import FileSaver from 'file-saver'
import keyBy from 'lodash/keyBy'
import omit from 'lodash/omit'
import Vue from 'vue'
import { Module } from 'vuex'

import { waitCursor } from '@/common/html_utils'
import { filesDiff } from '@/common/mergin_utils'
import { isAtLeastProjectRole, ProjectRole } from '@/common/permission_utils'
import { ProjectModule } from '@/modules/project/module'
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
  AccessRequestsPayload,
  GetProjectAccessRequestsPayload
} from '@/modules/project/types'
import { RootState } from '@/modules/types'

interface File {
  chunks: any
}

interface UploadFilesPayload {
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

const ProjectStore: Module<ProjectState, RootState> = {
  namespaced: true,
  state: {
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
  },

  mutations: {
    setAccessRequests(state, payload: AccessRequestsPayload) {
      state.accessRequests = payload.accessRequests
      state.accessRequestsCount = payload.count
    },
    setProject(state, payload: { project: ProjectDetail }) {
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
          const upload = state.uploads[enhancedProject.path]
          if (upload) {
            upload.diff = filesDiff(enhancedProject.files, upload.files)
          }
        }
      }
      state.project = enhancedProject
    },
    setProjects(state, payload: ProjectsPayload) {
      state.projects = payload.projects
      state.projectsCount = payload.count
    },
    projectVersions(state, payload: ProjectVersionsPayload) {
      state.versions = payload.versions
      state.versionsCount = payload.count
    },
    projectVersionsLoading(state, loading: boolean) {
      state.versionsLoading = loading
    },

    initUpload(state, payload) {
      const upload = {
        files: payload.files ?? {},
        diff: null,
        analysingFiles: []
      }
      Vue.set(state.uploads, state.project.path, upload)
    },
    analysingFiles(state, payload) {
      const upload = state.uploads[state.project.path]
      Vue.set(upload, 'analysingFiles', payload.files)
    },
    finishFileAnalysis(state, payload) {
      const upload = state.uploads[state.project.path]
      if (upload.analysingFiles) {
        // upload.analysingFiles = upload.analysingFiles.filter(p => p !== path)
        Vue.set(
          upload,
          'analysingFiles',
          upload.analysingFiles.filter((p) => p !== payload.path)
        )
      }
    },
    uploadFiles(state, payload: UploadFilesPayload) {
      let files = payload.files
      files = keyBy(files, 'path')
      const chunks = Object.values(files)
        .filter((f) => f.chunks !== undefined)
        .map((f) => f.chunks.length)
        .reduce((sum, item) => sum + item)
      const upload = {
        files,
        diff: filesDiff(state.project.files, files),
        running: false,
        progress: 0,
        loaded: 0,
        total: chunks
      }
      Vue.set(state.uploads, state.project.path, upload)
    },
    discardUpload(state, payload) {
      Vue.delete(state.uploads, payload.projectPath)
    },
    startUpload(state) {
      const upload = state.uploads[state.project.path]
      if (upload) {
        upload.running = true
        upload.progress = 0
      }
    },
    chunkUploaded(state, payload) {
      const upload = state.uploads[payload.project]
      if (upload) {
        upload.loaded++
        if (upload.loaded === upload.total) {
          upload.running = false
        }
      }
    },
    cancelUpload(state) {
      const upload = state.uploads[state.project.path]
      if (upload) {
        upload.running = false
        upload.progress = 0
      }
    },
    deleteFiles(state, payload) {
      let upload = state.uploads[state.project.path]
      if (!upload) {
        upload = {
          files: { ...state.project.files },
          diff: filesDiff({}, {})
        }
        Vue.set(state.uploads, state.project.path, upload)
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
      upload.diff = filesDiff(state.project.files, upload.files)
    },

    setCurrentNamespace(state, payload) {
      state.currentNamespace = payload.currentNamespace
    }
  },
  getters: {
    isProjectOwner: (state) =>
      isAtLeastProjectRole(state.project?.role, ProjectRole.owner),
    getProjectByName: (state) => (payload) => {
      return state.projects?.find((project) => project.name === payload.name)
    }
  },
  actions: {
    async initProjects({ dispatch, state }, payload: PaginatedProjectsPayload) {
      if (!(state.projects?.length > 0)) {
        await dispatch('getProjects', payload)
      }
    },

    async getProjects({ commit, dispatch }, payload: PaginatedProjectsPayload) {
      let response
      try {
        response = await ProjectApi.getPaginatedProject(payload.params)
        commit('setProjects', {
          projects: response.data?.projects,
          count: response.data?.count
        })
      } catch (_err) {
        await dispatch(
          'notificationModule/error',
          {
            text: 'Failed to load projects'
          },
          { root: true }
        )
      }
      return response
    },
    clearProjects({ commit }) {
      commit('setProjects', { projects: [], count: 0 })
      commit('setProject', { project: null })
    },

    async createProject({ commit }, payload) {
      waitCursor(true)
      try {
        await ProjectApi.createProject(payload.namespace, payload.data, true)
        commit('setProject', { project: null })
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
    async deleteProject({ commit, dispatch }, payload) {
      try {
        waitCursor(true)
        await ProjectApi.deleteProject(
          payload.namespace,
          payload.projectName,
          true
        )
        commit('setProject', { project: null })
        await dispatch('userModule/fetchUserProfile', undefined, { root: true })
        waitCursor(false)
        ProjectModule.routerService.replace({ path: '/' })
      } catch (e) {
        await dispatch(
          'notificationModule/error',
          { text: e.response.data?.detail || 'Failed to remove project' },
          { root: true }
        )
        waitCursor(false)
      }
    },
    async initUserAccessRequests(
      { dispatch },
      payload?: GetUserAccessRequestsPayload
    ) {
      await dispatch('fetchUserAccessRequests', {
        params: {
          page: 1,
          per_page: 10,
          order_params: 'expire DESC',
          ...payload?.params
        }
      })
    },

    async fetchUserAccessRequests(
      { commit, dispatch },
      payload: GetUserAccessRequestsPayload
    ) {
      try {
        const accessRequestResponse = await ProjectApi.fetchAccessRequests(
          payload.params
        )
        commit('setAccessRequests', {
          accessRequests: accessRequestResponse.data?.items,
          count: accessRequestResponse.data?.count
        })
      } catch {
        await dispatch(
          'notificationModule/error',
          { text: 'Failed to fetch project access requests' },
          {
            root: true
          }
        )
      }
    },

    async initNamespaceAccessRequests(
      { dispatch },
      payload: GetNamespaceAccessRequestsPayload
    ) {
      await dispatch('fetchNamespaceAccessRequests', {
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
      { commit, dispatch },
      payload: GetNamespaceAccessRequestsPayload
    ) {
      try {
        const accessRequestResponse =
          await ProjectApi.fetchNamespaceAccessRequests(
            payload.namespace,
            payload.params
          )
        commit('setAccessRequests', {
          accessRequests: accessRequestResponse.data?.items,
          count: accessRequestResponse.data?.count
        })
      } catch {
        await dispatch(
          'notificationModule/error',
          { text: 'Failed to fetch project access requests' },
          {
            root: true
          }
        )
      }
    },

    async getProjectAccessRequests(
      { dispatch },
      payload: GetProjectAccessRequestsPayload
    ) {
      if (payload.namespace) {
        await dispatch('fetchNamespaceAccessRequests', payload)
      } else {
        await dispatch('fetchUserAccessRequests', payload)
      }
    },

    async cancelProjectAccessRequest(
      { dispatch },
      payload: CancelProjectAccessRequestPayload
    ) {
      waitCursor(true)
      try {
        await ProjectApi.cancelProjectAccessRequest(payload.itemId, true)
      } catch (err) {
        const msg = err.response
          ? err.response.data?.detail
          : 'Failed to cancel access request'
        await dispatch(
          'notificationModule/error',
          { text: msg },
          {
            root: true
          }
        )
      } finally {
        waitCursor(false)
      }
    },

    async acceptProjectAccessRequest(
      state,
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

    async cloneProject({ commit }, payload) {
      const { namespace, project, data, cbSuccess } = payload
      try {
        waitCursor(true)
        await ProjectApi.cloneProject(namespace, project, data)
        waitCursor(false)
        cbSuccess()
        commit('setProject', { project: null })
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

    async fetchProject({ commit, dispatch }, payload: ProjectParams) {
      try {
        const projectResponse = await ProjectApi.fetchProject(
          payload.namespace,
          payload.projectName
        )
        commit('setProject', { project: projectResponse.data })
      } catch (e) {
        console.warn('Failed to load project data', e)
        await dispatch(
          'notificationModule/error',
          { text: 'Failed to load project data' },
          {
            root: true
          }
        )
      }
    },

    async unsubscribeProject({ commit, dispatch }, payload) {
      try {
        waitCursor(true)
        await ProjectApi.unsubscribeProject(payload.id)
        commit('setProject', { project: null })
        waitCursor(false)
      } catch (err) {
        const msg = err.response
          ? err.response.data?.detail
          : 'Failed to unsubscribe from project'
        await dispatch(
          'notificationModule/error',
          { text: msg },
          {
            root: true
          }
        )
        waitCursor(false)
      }
    },
    async fetchProjectDetail({ commit, dispatch }, payload) {
      const { callbackStatus, namespace, projectName, isLoggedUser } = payload
      try {
        const projectResponse = await ProjectApi.fetchProject(
          payload.namespace,
          payload.projectName
        )
        commit('setProject', { project: projectResponse.data })
      } catch (e) {
        callbackStatus(e.response.status)

        if (e.response.status !== 404 && e.response.status !== 403) {
          dispatch(
            'notificationModule/error',
            {
              text: 'Failed to load project data'
            },
            { root: true }
          )
        } else if (e.response.status === 403 && !isLoggedUser) {
          await ProjectModule.routerService.push(
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
              dispatch(
                'notificationModule/error',
                {
                  text: 'Failed to load project access requests data'
                },
                { root: true }
              )
            })
        }
      }
    },

    async fetchProjectVersions(
      { commit, dispatch },
      payload: FetchProjectVersionsPayload
    ) {
      try {
        commit('projectVersionsLoading', true)
        const response = await ProjectApi.fetchProjectVersions(
          payload.namespace,
          payload.projectName,
          payload.params
        )
        commit('projectVersions', {
          versions: response?.data?.versions,
          count: response?.data?.count
        })
      } catch (e) {
        await dispatch(
          'notificationModule/error',
          {
            text: 'Failed to fetch project versions'
          },
          { root: true }
        )
      } finally {
        commit('projectVersionsLoading', false)
      }
    },

    async saveProjectSettings(
      { commit },
      payload
    ): Promise<AxiosResponse<ProjectDetail>> {
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
        commit('setProject', { project: saveProjectSettingsResponse.data })
        waitCursor(false)
        return saveProjectSettingsResponse
      } finally {
        waitCursor(false)
      }
    },

    async pushProjectChunks({ commit }, payload) {
      const pushProjectChunksResponse = await ProjectApi.pushProjectChunks(
        payload.transaction,
        payload.chunk,
        payload.token,
        payload.data,
        true
      )
      commit('chunkUploaded', { project: payload.projectPath })
      return pushProjectChunksResponse
    },

    async pushFinishTransaction({ commit, dispatch }, payload) {
      const { projectPath, token, transaction } = payload
      try {
        const pushFinishTransactionResponse =
          await ProjectApi.pushFinishTransaction(transaction, token, true)
        commit('discardUpload', { projectPath })
        dispatch(
          'notificationModule/show',
          {
            text: `Upload finished: ${projectPath}`
          },
          { root: true }
        )
        commit('setProject', { project: pushFinishTransactionResponse.data })
        dispatch('userModule/fetchUserProfile', undefined, { root: true })
        waitCursor(false)
      } catch (err) {
        dispatch('pushCancelTransaction', { err, transaction })
      }
    },

    async pushProjectChanges({ dispatch }, payload) {
      const { data, projectPath } = payload
      try {
        return await ProjectApi.pushProjectChanges(projectPath, data)
      } catch (err) {
        const msg = (err.response && err.response.data?.detail) || 'Error'
        await dispatch(
          'notificationModule/error',
          { text: msg },
          { root: true }
        )
        return undefined
      }
    },

    async pushCancelTransaction({ commit, dispatch }, payload) {
      const { err, transaction } = payload
      commit('cancelUpload')
      const msg = err.__CANCEL__
        ? err.message
        : (err.response && err.response.data?.detail) || 'Error'
      dispatch('notificationModule/error', { text: msg }, { root: true })
      await ProjectApi.pushCancelTransaction(transaction)
      waitCursor(false)
    },

    async downloadArchive({ dispatch }, payload) {
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
          dispatch(
            'notificationModule/error',
            { text: resp.detail },
            { root: true }
          )
        })
      }
    }
  }
}

export default ProjectStore
