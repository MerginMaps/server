// Copyright (C) 2021 Lutra Consulting Limited. All rights reserved.
import routes from './module/routes'
import store from './module/store'
import router from '@/router'
export default {
  name: 'admin',
  routes: routes,
  store: store,
  addRoutes: () => {
    // add routes to router
    routes.forEach(route => {
      router.addRoute(route)
    })
  }

}
