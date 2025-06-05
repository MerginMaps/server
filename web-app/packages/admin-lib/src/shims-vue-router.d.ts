import 'vue-router'

declare module 'vue-router' {
  interface RouteMeta {
    title?: string | string[] | ((route, extended) => string | string[])
  }
}
