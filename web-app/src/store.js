// Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
// Do not distribute without the express permission of the author.

import Vue from 'vue'
import Vuex from 'vuex'
import keyBy from 'lodash/keyBy'
import omit from 'lodash/omit'

import { filesDiff } from '@/mergin'
import http from '@/http'

Vue.use(Vuex)


export default new Vuex.Store({
  strict: process.env.NODE_ENV === 'development',
  state: {
    app: null,
    projects: [],
    project: null,
    uploads: {},
    users: [],
    namespace: '',
    organisation: null,
    organisations: [],
    invitations: [],
    orgInvitations: [],
    transfers: [],
    accessRequests: [],
    barColor: 'rgba(176, 177, 181 1), rgba(176, 177, 181 1)',
    barImage: 'https://demos.creative-tim.com/material-dashboard/assets/img/sidebar-1.jpg',
    drawer: null,
    account: null, // account object inc. service details currently browsed, e.g. user, organisation
    serverError: null
  },
  mutations: {
    app (state, app) {
      if (!app.user) {
        app.user = null
      }
      state.app = app
      state.namespace = app.user ? app.user.username : null
      state.organisations = app.organisations
    },
    user (state, user) {
      Vue.set(state.app, 'user', user)
      if (user) {
        state.namespace = user.username
      }
    },
    updateUserProfile (state, profile) {
      Vue.set(state.app.user, 'profile', profile)
    },
    updateVerifiedEmailFlag (state, verifiedEmail) {
      Vue.set(state.app.user, 'verified_email', verifiedEmail)
    },
    projects (state, projects) {
      state.projects = projects
    },
    users (state, users) {
      state.users = users
    },
    project (state, project) {
      if (project) {
        project.files = keyBy(project.files, 'path')
        project.path = [project.namespace, project.name].join('/')
        const upload = state.uploads[project.path]
        if (upload) {
          upload.diff = filesDiff(project.files, upload.files)
        }
      }
      state.project = project
    },
    upload (state, files = {}) {
      const upload = {
        files,
        diff: null,
        analysingFiles: []
      }
      // Object.defineProperty(upload)
      Vue.set(state.uploads, state.project.path, upload)
    },
    analysingFiles (state, files) {
      const upload = state.uploads[state.project.path]
      Vue.set(upload, 'analysingFiles', files)
    },
    finishFileAnalysis (state, path) {
      const upload = state.uploads[state.project.path]
      if (upload.analysingFiles) {
        // upload.analysingFiles = upload.analysingFiles.filter(p => p !== path)
        Vue.set(upload, 'analysingFiles', upload.analysingFiles.filter(p => p !== path))
      }
    },

    uploadFiles (state, files) {
      files = keyBy(files, 'path')
      const chunks = Object.values(files).filter(f => f.chunks !== undefined).map(f => f.chunks.length).reduce((sum, item) => sum + item)
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
    discardUpload (state, project) {
      Vue.delete(state.uploads, project)
    },
    startUpload (state) {
      const upload = state.uploads[state.project.path]
      if (upload) {
        upload.running = true
        upload.progress = 0
      }
    },
    chunkUploaded (state, project) {
      const upload = state.uploads[project]
      if (upload) {
        upload.loaded++
        if (upload.loaded === upload.total) {
          upload.running = false
        }
      }
    },
    cancelUpload (state, project) {
      const upload = state.uploads[state.project.path]
      if (upload) {
        upload.running = false
        upload.progress = 0
      }
    },
    deleteFiles (state, files) {
      let upload = state.uploads[state.project.path]
      if (!upload) {
        upload = {
          files: { ...state.project.files },
          diff: filesDiff({}, {})
        }
        Vue.set(state.uploads, state.project.path, upload)
      }

      files.forEach(path => {
        if (upload.files[path]) {
          Vue.delete(upload.files, path)
        } else { // should be folder
          const dirPrefix = path + '/'
          const removed = Object.keys(upload.files).filter(path => path.startsWith(dirPrefix))
          upload.files = omit(upload.files, removed)
        }
      })
      upload.diff = filesDiff(state.project.files, upload.files)
    },
    projectVersions (state, { project, versions }) {
      state.project.versions = versions
    },
    organisations (state, organisations) {
      state.organisations = organisations
    },
    organisation (state, organisation) {
      state.organisation = organisation
    },
    addOrganisation (state, organisation) {
      state.organisations.push(organisation)
    },
    invitations (state, invitations) {
      state.invitations = invitations
    },
    orgInvitations (state, invitations) {
      state.orgInvitations = invitations
    },
    addInvitation (state, invitation) {
      state.orgInvitations.push(invitation)
    },
    deleteInvitation (state, invitation) {
      const index = state.invitations.indexOf(invitation)
      state.invitations.splice(index, 1)
      const orgIndex = state.orgInvitations.indexOf(invitation)
      state.orgInvitations.splice(orgIndex, 1)
    },
    updateOrganisationMembers (state, access) {
      Object.entries(access).forEach(([key, value]) => {
        state.organisation[key] = value
      })
    },
    namespace (state, namespace) {
      state.namespace = namespace
    },
    transfers (state, transfers) {
      state.transfers = transfers
    },
    accessRequests (state, accessRequests) {
      state.accessRequests = accessRequests
    },
    deleteTransfer (state, item) {
      const index = state.transfers.indexOf(item)
      state.transfers.splice(index, 1)
    },
    SET_BAR_IMAGE (state, payload) {
      state.barImage = payload
    },
    SET_DRAWER (state, payload) {
      state.drawer = payload
    },
    serverError (state, msg) {
      state.serverError = msg
    }
  },
  getters: {
    isUserOwnerOfOrganisation: (state) => (name) => {
      const role = (state.app.user.profile && state.app.user.profile.organisations) ? state.app.user.profile.organisations[name] : null
      return (role) ? role === 'owner' : false
    },
    isUserMemberOfOrganisation: (state) => (name) => {
      if (state.app.user.profile === undefined) return false
      return name in state.app.user.profile.organisations
    },
    isProjectOwner: (state) => {
      return state.project.access.owners.includes(state.app.user.id)
    }
  },
  actions: {
    clearUserData (context) {
      context.commit('projects', [])
      context.commit('project', null)
      context.commit('user', null)
      context.commit('organisation', null)
      context.commit('organisations', [])
      context.commit('invitations', [])
    },
    async setOrganisation ({ commit, state }, name) {
      if (state.organisation && state.organisation.name === name) return
      const resp = await http.get(`/orgs/${name}`)
      commit('organisation', resp.data)
    }
  }
})
