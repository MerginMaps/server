// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import FileSaver from 'file-saver'
import keyBy from 'lodash/keyBy'
import omit from 'lodash/omit'
import Vue from 'vue'
import { Module } from 'vuex'

import { CustomError } from '@/common/errors'
import { waitCursor } from '@/common/html_utils'
import { filesDiff } from '@/common/mergin_utils'
import { isAtLeastProjectRole, ProjectRole } from '@/common/permission_utils'
import { ProjectModule } from '@/modules/project/module'
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
import { RootState } from '@/modules/types'

interface File {
  chunks: any
}

interface UploadFilesPayload {
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

const ProjectStore: Module<ProjectState, RootState> = {
  namespaced: true,
  state: {
    accessRequests: undefined,
    namespaceAccessRequests: undefined,
    project: null,
    projectsCount: 0,
    projects: undefined,
    uploads: {},
    currentNamespace: null
  },

  mutations: {
    setAccessRequests(state, payload) {
      state.accessRequests = payload.accessRequests
    },
    setNamespaceAccessRequests(state, payload) {
      state.namespaceAccessRequests = payload.accessRequests
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
    projectVersions(state, payload) {
      state.project.versions = payload.versions
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

    async createProject({ commit, dispatch }, payload) {
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
      } catch (err) {
        await dispatch(
          'formModule/handleError',
          {
            componentId: payload.componentId,
            error: err,
            generalMessage: 'Failed to create project.'
          },
          { root: true }
        )
        throw err
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
    async initAccessRequests({ dispatch, state }) {
      if (!(state.accessRequests?.length > 0)) {
        await dispatch('fetchAccessRequests')
      }
    },

    async fetchAccessRequests({ commit, dispatch }) {
      try {
        const accessRequestResponse = await ProjectApi.fetchAccessRequests()
        commit('setAccessRequests', {
          accessRequests: accessRequestResponse.data
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
      { dispatch, state },
      payload: NamespaceAccessRequestsPayload
    ) {
      if (!(state.namespaceAccessRequests?.length > 0)) {
        await dispatch('fetchNamespaceAccessRequests', payload)
      }
    },

    async fetchNamespaceAccessRequests(
      { commit, dispatch },
      payload: NamespaceAccessRequestsPayload
    ) {
      try {
        const accessRequestResponse =
          await ProjectApi.fetchNamespaceAccessRequests(payload.namespace)
        commit('setNamespaceAccessRequests', {
          accessRequests: accessRequestResponse.data
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

    async reloadProjectAccessRequests(
      { dispatch },
      payload: ReloadProjectAccessRequestPayload
    ) {
      if (payload.refetchGlobalAccessRequests) {
        if (payload.namespace) {
          await dispatch('fetchNamespaceAccessRequests', {
            namespace: payload.namespace
          })
        } else {
          await dispatch('fetchAccessRequests')
        }
      } else {
        if (payload.namespace && payload.projectName) {
          // refetch project to update project access requests
          await dispatch('fetchProject', {
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
      { dispatch },
      payload: CancelProjectAccessRequestPayload
    ) {
      waitCursor(true)
      try {
        await ProjectApi.cancelProjectAccessRequest(payload.itemId, true)
        await dispatch('reloadProjectAccessRequests', payload)
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
      { dispatch },
      payload: AcceptProjectAccessRequestPayload
    ) {
      waitCursor(true)
      try {
        await ProjectApi.acceptProjectAccessRequest(
          payload.itemId,
          payload.data,
          true
        )
        await dispatch('reloadProjectAccessRequests', payload)
      } catch (err) {
        const msg = err.response
          ? err.response.data?.detail
          : 'Failed to accept access request'
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

    async fetchProjectVersions({ commit, dispatch }, payload) {
      try {
        const versionsResponse = await ProjectApi.fetchProjectVersions(
          payload.namespace,
          payload.projectName,
          payload.params
        )
        payload.cbSuccess(versionsResponse.data)
        commit('projectVersions', { versions: versionsResponse.data?.versions })
      } catch (e) {
        await dispatch(
          'notificationModule/error',
          {
            text: 'Failed to fetch project versions'
          },
          { root: true }
        )
      }
    },

    async saveProjectSettings({ commit, dispatch }, payload) {
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
      } catch (err) {
        await dispatch(
          'notificationModule/error',
          {
            text: err.response.data?.detail || 'Failed to save project settings'
          },
          { root: true }
        )
        waitCursor(false)
        return new CustomError('Failed to save project settings', err?.response)
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
