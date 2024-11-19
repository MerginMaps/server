import { Router } from 'vue-router'

declare module 'pinia' {
  export interface Pinia {
    router: Router
  }
}
