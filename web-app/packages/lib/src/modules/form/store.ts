// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import Vue from 'vue'
import { Module } from 'vuex'

import {
  ClearErrorsPayload,
  FormErrors,
  HandleErrorPayload,
  MerginComponentUuid,
  MerginComponentUuidPayload,
  SetFormErrorPayload
} from '@/modules/form/types'
import { RootState } from '@/modules/types'

export interface FormState {
  errors: Record<MerginComponentUuid, FormErrors>
}

const FormStore: Module<FormState, RootState> = {
  namespaced: true,
  state: {
    errors: {}
  },
  getters: {
    getErrorByComponentId: (state) => (payload: MerginComponentUuid) => {
      return state.errors[payload]
    }
  },
  mutations: {
    setFormErrors(state, payload: SetFormErrorPayload) {
      Vue.set(state.errors, payload.componentId, payload.errors)
    },
    resetFormErrors(state, payload: MerginComponentUuidPayload) {
      Vue.delete(state.errors, payload.componentId)
    }
  },
  actions: {
    clearErrors({ commit }, payload: ClearErrorsPayload) {
      commit('resetFormErrors', payload)
      if (!payload.keepNotification) {
        // reset error message in notification component
        commit('notificationModule/closeNotification', null, { root: true })
      }
    },
    async handleError({ commit, dispatch }, payload: HandleErrorPayload) {
      let errorMessage
      if (typeof payload.error?.response?.data === 'object') {
        // two types of error responses
        if (typeof payload.error.response.data.status === 'number') {
          errorMessage = payload.error.response.data.detail
        } else {
          commit('setFormErrors', {
            componentId: payload.componentId,
            errors: payload.error.response.data
          })
        }
      } else {
        errorMessage =
          payload?.error?.response?.data ??
          payload.generalMessage ??
          payload?.error ??
          'Error'
      }
      if (errorMessage) {
        // show error message in notification component
        await dispatch(
          'notificationModule/error',
          { text: errorMessage },
          { root: true }
        )
      }
    }
  }
}

export default FormStore
