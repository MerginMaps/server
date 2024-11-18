# Mergin web-app

Monorepo for mergin frontend stuff:

- web application [./packages/app](./packages/app)
- admin web application [./packages/app](./packages/admin-app)

# Monorepo Structure

* this projects uses yarn workspaces
* monorepo consists of root directory with own package.json and individual workspaces in `packages` directory
* root package.json defines common devDependencies and it cannot hold any non-development dependency
* individual workspace package.json defines dependencies used in that particular workspace package
* frontend application (e.g. app) is also a workspace package (@mergin/app) held in directory [./packages/app](./packages/app).

Application constist of several packages in `packages` directory:

- @mergin/lib - Shared library for common features
- @mergin/admin-lib - Shared library for admin
- @mergin/app - Web appliacation"
- @mergin/admin-app - Web application for administration

Library packages with *-lib* name are containing shared code for *-app* applications.

Web application *@mergin/app* is using shared library *@mergin/lib*. Web application for administration *admin-app* is using shared library *@mergin/admin-lib*.

For details about development follow instructions in [development guide](../development.md).