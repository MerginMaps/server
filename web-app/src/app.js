// Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
// Do not distribute without the express permission of the author.

import Vue from 'vue'
import PortalVue from 'portal-vue'
import vuetify from './admin/plugins/vuetify'
import 'vuetify/dist/vuetify.min.css'
import 'material-icons/iconfont/material-icons.scss'
import '@fortawesome/fontawesome-free/css/all.css'
import '@mdi/font/css/materialdesignicons.css'
import 'vue-wysiwyg/dist/vueWysiwyg.css'

import App from './App.vue'
import router from './router'
import store from './store'
import http from './http'
import * as util from './util'
import wysiwyg from 'vue-wysiwyg'

import './admin/plugins/base'
import './admin/plugins/chartist'
import './admin/plugins/vee-validate'
import i18n from './admin/i18n'
import VueMeta from 'vue-meta'

import admin from './admin/module'
store.registerModule('admin', admin.store)
admin.addRoutes()

const initializeModule = (module) => {
  store.registerModule(module.name, module.store)
  module.addRoutes()
  store.dispatch(module.name + '/initialize', null, { root: true })
}

Vue.config.productionTip = false
Vue.use(PortalVue)
Vue.use(wysiwyg, {})
Vue.use(VueMeta)
Vue.prototype.$http = http

Vue.filter('filesize', (value, unit, digits = 2, minUnit = 'B') => { return util.formatFileSize(value, unit, digits, minUnit) })
Vue.filter('datetime', util.formatDateTime)
Vue.filter('date', util.formatDate)
Vue.filter('timediff', util.formatTimeDiff)
Vue.filter('remainingtime', util.formatRemainingTime)
Vue.filter('totitle', util.formatToTitle)
Vue.filter('currency', util.formatToCurrency)

if (process.env.NODE_ENV === 'development') {
  var initialize = require('./dev').default
} else {
  initialize = require('./prod').default
}

const createApp = () => {
  router.onError((e) => { store.commit('serverError', e.message) })
  return new Vue({
    router,
    store,
    vuetify,
    i18n,
    render: h => h(App)
  })
}

export { createApp, initialize, initializeModule }
