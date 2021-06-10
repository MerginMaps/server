// Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
// Do not distribute without the express permission of the author.

import { createApp, initialize } from './app'
import router from './router'
import store from './store'
import Registration from '@/views/Registration'


initialize().then((appData) => {
  // add default home root
  router.addRoute({
    path: '/',
    name: 'home',
    meta: { public: true },
    beforeEnter: (to, from, next) => {
      if (store.state.app.user !== null && store.state.app.user.username !== null) next('/dashboard')
      else next('/login')
    }
  })
  router.addRoute({
    beforeEnter: (to, from, next) => {
      if (store.state.app.user && store.state.app.user.username !== null) next('/dashboard')
      else if (!store.state.app.registration) next('/login')
      else next()
    },
    path: '/register',
    name: 'register',
    meta: { public: true },
    component: Registration
  }
  )
  store.commit('app', appData)
  createApp().$mount('#app')
})
