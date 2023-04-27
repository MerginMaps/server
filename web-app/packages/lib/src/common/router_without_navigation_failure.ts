// Copyright (C) Lutra Consulting Limited
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

// TODO: V3_UPGRADE - check if still necessary
// import Router from 'vue-router'
//
// // fixed problem with vue router - catch Detecting Navigation Failures
//
// const originalPush = Router.prototype.push
// // eslint-disable-next-line @typescript-eslint/ban-ts-comment
// // @ts-ignore
// Router.prototype.push = function push(location, onResolve, onReject) {
//   if (onResolve || onReject)
//     return originalPush.call(this, location, onResolve, onReject)
//   return originalPush.call(this, location).catch((err) => {
//     if (Router.isNavigationFailure(err)) {
//       // resolve err
//       return err
//     }
//     // rethrow error
//     return Promise.reject(err)
//   })
// }
//
// export { Router }
