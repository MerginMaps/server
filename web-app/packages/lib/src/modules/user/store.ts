// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import { defineStore, getActivePinia } from 'pinia'
import { isNavigationFailure } from 'vue-router'

import { getErrorMessage } from '@/common/error_utils'
import { waitCursor } from '@/common/html_utils'
import { createStorage, StorageProxy } from '@/common/local_storage'
import { isAtLeastRole, WorkspaceRole } from '@/common/permission_utils'
import { useDialogStore } from '@/modules/dialog/store'
import { useFormStore } from '@/modules/form/store'
import { useInstanceStore } from '@/modules/instance/store'
import { useNotificationStore } from '@/modules/notification/store'
import { useProjectStore } from '@/modules/project/store'
import {
  ResetPasswordPayload,
  ChangePasswordWithTokenPayload,
  ChangePasswordPayload,
  IsWorkspaceAdminPayload,
  LoginPayload,
  UserDetailResponse,
  WorkspaceIdPayload,
  WorkspaceResponse,
  SetWorkspaceIdPayload,
  UserSearchParams,
  EditUserProfileParams,
  LastSeenWorkspace
} from '@/modules/user/types'
import { UserApi } from '@/modules/user/userApi'

export interface UserState {
  loggedUser?: UserDetailResponse
  workspaces: WorkspaceResponse[]
  workspaceId: number
  lastWorkspaces: StorageProxy<LastSeenWorkspace[]>
}

const lastWorkspacesStorage = createStorage<LastSeenWorkspace[]>(
  'mm-last-workspaces',
  []
)

export const useUserStore = defineStore('userModule', {
  state: (): UserState => ({
    loggedUser: null,
    workspaces: [],
    workspaceId: undefined,
    lastWorkspaces: lastWorkspacesStorage
  }),

  getters: {
    isLoggedIn: (state) => {
      const instanceStore = useInstanceStore()
      return (
        instanceStore.initData?.authenticated ||
        state.loggedUser?.username != null
      )
    },
    isSuperUser() {
      const instanceStore = useInstanceStore()
      return this.isLoggedIn && instanceStore.initData?.superuser
    },
    isGlobalWorkspaceAdmin() {
      return isAtLeastRole(this.getPreferredWorkspace?.role, WorkspaceRole.admin)
    },
    getPreferredWorkspace: (state) => {
      return state.loggedUser?.workspaces?.find(
        (workspace) => workspace.id === state.loggedUser.preferred_workspace
      )
    },
    getUserFullName: (state) => {
      return state.loggedUser?.name && state.loggedUser?.name !== ''
        ? state.loggedUser.name
        : state.loggedUser?.username
        ? state.loggedUser.username
        : ''
    },
    isWorkspaceAdmin() {
      return (payload?: IsWorkspaceAdminPayload): boolean => {
        const workspace = payload?.id
          ? this.getWorkspaceById({ id: payload.id })
          : this.currentWorkspace
        return isAtLeastRole(workspace?.role, WorkspaceRole.admin)
      }
    },
    isWorkspaceOwner() {
      return (payload?: IsWorkspaceAdminPayload): boolean => {
        const workspace = payload?.id
          ? this.getWorkspaceById({ id: payload.id })
          : this.currentWorkspace
        return isAtLeastRole(workspace?.role, WorkspaceRole.owner)
      }
    },
    currentWorkspace: (state) => {
      return state.workspaces.find(
        (workspace) => workspace.id === state.workspaceId
      )
    },
    getWorkspaceById(state) {
      return (payload: WorkspaceIdPayload): WorkspaceResponse | undefined => {
        return state.workspaces.find((workspace) => workspace.id === payload.id)
      }
    },
    getWorkspaceByName(state) {
      return (payload) => {
        return state.workspaces.find(
          (workspace) => workspace.name === payload.name
        )
      }
    },
    isWorkspaceUser: (state) => {
      return (payload: WorkspaceIdPayload) => {
        return state.workspaces.some((workspace) => workspace.id === payload.id)
      }
    }
  },

  actions: {
    updateLoggedUser(payload) {
      this.loggedUser = payload.loggedUser
    },

    updateVerifiedEmail(payload) {
      this.loggedUser.verified_email = payload.verifiedEmail
    },

    setWorkspaces(payload) {
      this.workspaces = payload.workspaces
    },

    setWorkspaceId(payload) {
      this.workspaceId = payload.id
    },

    async editUserProfile(payload: {
      editedUser: EditUserProfileParams
      componentId?: string
    }) {
      const dialogStore = useDialogStore()
      const notificationStore = useNotificationStore()
      const formStore = useFormStore()

      waitCursor(true)
      try {
        await UserApi.editUserProfile(payload.editedUser, true)
        dialogStore.close()
        this.updateLoggedUser({
          loggedUser: payload.editedUser
        })
        await this.fetchUserProfile()
        await notificationStore.show({ text: 'Profile has been changed' })
      } catch (error) {
        await formStore.handleError({
          componentId: payload.componentId,
          error,
          generalMessage: 'Failed to change profile'
        })
      } finally {
        waitCursor(false)
      }
    },

    async fetchUserProfile() {
      const notificationStore = useNotificationStore()

      let resp
      try {
        resp = await UserApi.fetchUserProfile()
        this.updateLoggedUser({ loggedUser: resp.data })
        this.updateVerifiedEmail({
          verifiedEmail: resp.data.verified_email
        })
      } catch {
        await notificationStore.error({
          text: "Failed to fetch user's profile"
        })
      }
      return resp?.data
    },

    async closeUserProfile() {
      const notificationStore = useNotificationStore()

      waitCursor(true)
      try {
        await UserApi.closeUserProfile(true)
        this.updateLoggedUser({
          loggedUser: null
        })
        // taken from logout action, router would return error because user is considered as logged in
        location.href = '/'
      } catch (err) {
        await notificationStore.error({
          text: getErrorMessage(err, 'Unable to close account')
        })
      } finally {
        waitCursor(false)
      }
    },

    async redirectAfterLogin(payload) {
      const notificationStore = useNotificationStore()

      try {
        getActivePinia()
          .router.push(payload.currentRoute.query.redirect)
          .catch((e) => {
            if (!isNavigationFailure(e)) {
              Promise.reject(e)
            }
          })
      } catch (e) {
        await notificationStore.error({
          text: e
        })
      }
    },

    async redirectFromLoginAfterLogin(payload) {
      if (payload.currentRoute.path === '/login') {
        getActivePinia()
          .router.push({ path: '/' })
          .catch((e) => {
            if (!isNavigationFailure(e)) {
              Promise.reject(e)
            }
          })
      }
    },

    async userLogin(payload: LoginPayload) {
      const instanceStore = useInstanceStore()
      const formStore = useFormStore()

      try {
        await UserApi.login(payload.data)
        await instanceStore.initApp()
      } catch (error) {
        await formStore.handleError({
          componentId: payload.componentId,
          error,
          generalMessage: 'Failed to login'
        })
      }
    },

    async resetPassword(payload: ResetPasswordPayload) {
      const notificationStore = useNotificationStore()
      const formStore = useFormStore()

      try {
        await UserApi.resetPassword({ email: payload.email })
        await getActivePinia().router.push({ path: '/login' })
        await notificationStore.show({
          text: 'Email with password reset link was sent to your email address'
        })
      } catch (error) {
        await formStore.handleError({
          componentId: payload.componentId,
          error,
          generalMessage: 'Failed to send confirmation email'
        })
      }
    },

    async changePasswordWithToken(payload: ChangePasswordWithTokenPayload) {
      const formStore = useFormStore()

      waitCursor(true)
      try {
        await UserApi.changePasswordWithToken(payload.token, payload.data, true)
        // callback - set => this.success = true
        payload.callback(true)
        waitCursor(false)
      } catch (e) {
        waitCursor(false)
        // callback - set => this.success = false
        payload.callback(false)
        await formStore.handleError({
          componentId: payload.componentId,
          error: e,
          generalMessage: 'Failed to change password'
        })
      }
    },

    async resendConfirmationEmail(payload) {
      const notificationStore = useNotificationStore()

      try {
        await UserApi.resendEmail()
        await notificationStore.show({
          text: `Email was sent to address: ${payload.email}`
        })
      } catch (err) {
        await notificationStore.error({
          text: 'Failed to send confirmation email, please check your address in user profile settings'
        })
      }
    },

    async changePassword(payload: ChangePasswordPayload) {
      const notificationStore = useNotificationStore()
      const formStore = useFormStore()
      const dialogStore = useDialogStore()

      waitCursor(true)
      try {
        await UserApi.changePassword(payload.data, true)
        dialogStore.close()
        await notificationStore.show({ text: 'Password has been changed' })
      } catch (error) {
        await formStore.handleError({
          componentId: payload.componentId,
          error,
          generalMessage: 'Failed to change password'
        })
      } finally {
        waitCursor(false)
      }
    },

    clearUserData() {
      const projectStore = useProjectStore()

      projectStore.clearProjects()
      this.updateLoggedUser({ loggedUser: null })
    },

    async getWorkspace(payload) {
      const notificationStore = useNotificationStore()

      let newWorkspace
      try {
        const workspaceResponse = await UserApi.getWorkspaceById(payload.id)
        newWorkspace = workspaceResponse.data
        this.setWorkspaceId({ id: payload.id })
        await this.updateWorkspacesWithWorkspaceChange({
          workspace: newWorkspace
        })
      } catch (_err) {
        await notificationStore.error({
          text: 'Failed to load workspace'
        })
      }
      return newWorkspace
    },

    async getWorkspaces(): Promise<void> {
      const notificationStore = useNotificationStore()

      let workspacesResponse
      try {
        workspacesResponse = await UserApi.getWorkspaces()
        this.setWorkspaces({ workspaces: workspacesResponse.data })
      } catch (_err) {
        await notificationStore.error({
          text: 'Failed to load workspaces'
        })
      }
      return workspacesResponse
    },

    async updateWorkspacesWithWorkspaceChange(payload) {
      // update this.workspaces
      if (this.workspaces) {
        const idx = this.workspaces.findIndex(
          (workspace) => workspace.id === payload.workspace.id
        )
        if (idx !== -1) {
          this.setWorkspaces({
            workspaces: [
              ...this.workspaces.slice(0, idx),
              payload.workspace,
              ...this.workspaces.slice(idx + 1)
            ]
          })
        }
      }
    },

    async setWorkspace(payload: SetWorkspaceIdPayload) {
      if (this.workspaceId === payload.workspaceId) {
        return
      }
      this.setWorkspaceId({ id: payload.workspaceId })
      if (!payload.skipStorage) {
        // Append current workspace with last seen parameter
        this.lastWorkspaces.value = [
          ...this.lastWorkspaces.value.filter(
            (item) =>
              item.id !== payload.workspaceId ||
              item.userId !== this.loggedUser.id
          ),
          {
            lastSeen: Date.now(),
            id: payload.workspaceId,
            userId: this.loggedUser.id
          }
        ]
      }
    },

    getLastWorkspaceFromStorage(): WorkspaceResponse | undefined {
      if (this.loggedUser?.id === undefined) return

      const lastSeenWorkspace = [...this.lastWorkspaces.value]
        .sort((a, b) => {
          return b.lastSeen - a.lastSeen
        })
        .find((item) => item.userId === this.loggedUser?.id)

      return (
        lastSeenWorkspace && this.getWorkspaceById({ id: lastSeenWorkspace.id })
      )
    },

    async cleanupLastSeenWorkspaces() {
      this.lastWorkspaces.value = this.lastWorkspaces.value.filter(
        (item) => item.userId !== this.loggedUser?.id
      )
    },

    /**
     * Checks the current workspace that the user is in.
     *
     * Tries to get the current workspace ID from the local storage array of last seen ws.
     * If not found, tries to use the preferred workspace ID from the user profile.
     * If still not found, defaults to using the first workspace in the user's list of workspaces.
     *
     * Sets the current workspace in the store, and saves to local storage if needed.
     */
    async checkCurrentWorkspace() {
      try {
        await this.getWorkspaces()
        let foundWorkspace = this.getLastWorkspaceFromStorage()
        if (this.workspaces.length > 0) {
          let skipStorage = true
          if (!foundWorkspace) {
            // try to use preferred_workspace from user profile response
            const preferredWorkspaceId = this.loggedUser?.preferred_workspace
            foundWorkspace = this.getWorkspaceById({
              id: preferredWorkspaceId
            })
            if (foundWorkspace?.id) {
              // do not skip saving in local storage when using preferredWorkspace
              skipStorage = false
            }
          }
          // use id from found workspace, if not found fallback to first workspace from user workspaces
          const currentWorkspaceIdToSet =
            foundWorkspace?.id ?? this.workspaces[0].id
          await this.setWorkspace({
            workspaceId: currentWorkspaceIdToSet,
            // do not save workspaceId to storage as it could be:
            // * already there, if was loaded from local storage
            // * used the first user workspace as fallback, then it is not a user choice
            skipStorage
          })
        } else {
          await this.cleanupLastSeenWorkspaces()
        }
      } catch (e) {
        console.warn('Loading of stored user workspace id has failed.', e)
      }
    },

    async logout() {
      await UserApi.logout()
    },

    /**
     * Searches for authorized users matching the given search parameters.
     *
     * @param params - Search parameters to filter users by.
     * @returns Promise resolving to API response with matching users.
     */
    async getAuthUserSearch(params: UserSearchParams) {
      return await UserApi.getAuthUserSearch(params)
    },

    /**
     * Searches for users that match the given search parameters,
     * filtering out any users that are already members of the current project.
     *
     * @param params - Object containing the search parameters
     * @returns Promise resolving to the filtered API response
     */
    async getAuthNotProjectUserSearch(params: UserSearchParams) {
      const projectStore = useProjectStore()
      const access = projectStore.project.access
      const projectUsers = [
        ...access.readers,
        ...access.writers,
        ...access.owners
      ]

      const response = await UserApi.getAuthUserSearch(params)
      if (access) {
        response.data = response.data.filter(
          (item) => !projectUsers.find((id) => id === item.id)
        )
      }
      return response
    }
  }
})
