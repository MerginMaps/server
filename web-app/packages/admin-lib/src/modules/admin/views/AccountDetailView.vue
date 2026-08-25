<template>
  <admin-layout>
    <app-container>
      <app-section ground>
        <template #header>
          <h1 class="headline-h3">Account details</h1>
        </template>
      </app-section>
    </app-container>
    <template v-if="user">
      <app-container>
        <app-section class="p-4">
          <div class="flex flex-column row-gap-3">
            <div class="flex align-items-center gap-2">
              <PAvatar
                :label="$filters.getAvatar(user?.email, profile?.name)"
                shape="circle"
                :pt="{
                  root: {
                    class: 'font-semibold flex-shrink-0',
                    style: {
                      width: '2.25rem',
                      height: '2.25rem',
                      fontSize: '1rem'
                    }
                  }
                }"
              />
              <h2 class="headline-h2" data-cy="profile-name">
                {{
                  profile?.name
                    ? `${profile.name} (${user?.username})`
                    : user.username
                }}
              </h2>
            </div>
            <p
              class="m-0 paragraph-p6 overflow-wrap-anywhere"
              data-cy="profile-email"
            >
              <i
                v-if="!user?.verified_email"
                v-tooltip.top="{
                  value: 'Email verification status'
                }"
                class="ti ti-alert-circle-filled"
                style="color: var(--grape-color)"
              ></i>
              {{ user?.email }}
            </p>
            <dl
              class="project-view-detail-list paragraph-p5 flex flex-column gap-3"
            >
              <div>
                <dt class="paragraph-p6 opacity-80">User ID</dt>
                <dd class="font-semibold" data-cy="profile-id">
                  <button
                    type="button"
                    class="id-copy-pill"
                    v-tooltip.top="'Copy to clipboard'"
                    :aria-label="`Copy user ID ${user?.id}`"
                    :disabled="!user?.id"
                    @click="copyId"
                  >
                    <span>{{ user?.id }}</span>
                    <i class="ti ti-copy"></i>
                  </button>
                </dd>
              </div>
              <div>
                <dt class="paragraph-p6 opacity-80">Last signed in</dt>
                <dd class="font-semibold" data-cy="profile-last-signed-in">
                  {{ $filters.date(user.last_signed_in) || '-' }}
                </dd>
              </div>
              <div>
                <dt class="paragraph-p6 opacity-80">Registered</dt>
                <dd class="font-semibold" data-cy="profile-registered">
                  {{ $filters.date(user?.registration_date) }}
                </dd>
              </div>
            </dl>
          </div>
        </app-section>
      </app-container>
      <slot name="additionalContent" />
      <app-container v-if="userStore.loggedUser?.id !== user?.id">
        <app-section>
          <template #title>Advanced</template>

          <app-settings :items="settingsItems">
            <template #notifications>
              <div class="flex-shrink-0 paragraph-p1">
                <PInputSwitch
                  :model-value="profile?.receive_notifications"
                  disabled
                />
              </div>
            </template>
            <template #adminAccess>
              <div class="flex-shrink-0 paragraph-p1">
                <div
                  class="flex align-items-center flex-shrink-0"
                  data-cy="profile-notification"
                >
                  <PButton
                    :severity="user?.is_admin ? 'danger' : 'warning'"
                    :disabled="
                      !instanceStore.configData?.enable_superadmin_assignment
                    "
                    @click="switchAdminAccess"
                    :label="
                      !user?.is_admin
                        ? 'Grant admin access'
                        : 'Revoke admin access'
                    "
                  />
                </div>
              </div>
            </template>
            <template #accountActivation>
              <div class="flex-shrink-0">
                <PButton
                  @click="changeStatusDialog"
                  :severity="user?.active ? 'warning' : 'secondary'"
                  :label="
                    user?.active ? 'Deactivate account' : 'Activate account'
                  "
                  class="w-auto mr-1"
                />
              </div>
            </template>
            <template #deleteAccount>
              <div class="flex-shrink-0">
                <PButton
                  @click="confirmDeleteUser"
                  severity="danger"
                  data-cy="profile-close-account-btn"
                  label="Delete account"
                />
              </div>
            </template>
          </app-settings>
        </app-section>
      </app-container>
    </template>
  </admin-layout>
</template>

<script setup lang="ts">
import {
  ConfirmDialog,
  useDialogStore,
  AppSection,
  AppContainer,
  ConfirmDialogProps,
  AppSettings,
  AppSettingsItemConfig,
  useCopyToClipboard,
  useInstanceStore,
  useUserStore
} from '@mergin/lib'
import { computed, watch, watchEffect } from 'vue'
import { useRoute } from 'vue-router'

import AdminLayout from '@/modules/admin/components/AdminLayout.vue'
import { getAdminTitle } from '@/modules/admin/routes'
import { useAdminStore } from '@/modules/admin/store'

const route = useRoute()
const adminStore = useAdminStore()
const dialogStore = useDialogStore()
const instanceStore = useInstanceStore()
const userStore = useUserStore()

const settingsItems = computed<AppSettingsItemConfig[]>(() => [
  {
    key: 'notifications',
    title: 'Receive notifications',
    description: profile?.value?.receive_notifications
      ? 'User has enabled receiving notifications'
      : 'User has disabled notifications.'
  },
  {
    key: 'adminAccess',
    title: 'Access to admin panel',
    description: user.value?.is_admin
      ? 'User has access to the admin panel.'
      : 'User does not have access to the admin panel.'
  },
  {
    key: 'accountActivation',
    title: 'Account activation',
    description: user?.value?.active
      ? "The user's account is currently active. Deactivation will lead to a temporary ban from Mergin Maps usage."
      : "The user's account is currently inactive. Activating it will allow access to Mergin Maps."
  },
  {
    key: 'deleteAccount',
    title: 'Delete account',
    description:
      'Deleting this user will remove them and all their data. This action cannot be undone.'
  }
])

const { copy } = useCopyToClipboard()
const copyId = () => copy(user.value?.id, 'User ID')

const user = computed(() => adminStore.user)
const profile = computed(() => adminStore.user?.profile)
const routeUsername = computed(() => route?.params?.username)

const fetchProfile = (username: string) => {
  adminStore.user = null
  adminStore.fetchUserByName({ username })
}

watchEffect(() => {
  // We need to handle the title separately, as the account's email is not
  // available in the route and only loads after the profile is fetched
  if (user.value?.email) {
    document.title = getAdminTitle(route, {
      accountEmail: user.value.email
    })?.[0]
  }
})

watch(
  routeUsername,
  (username) => {
    if (username) {
      fetchProfile(username as string)
    }
  },
  { immediate: true }
)

const changeStatusDialog = () => {
  const props: ConfirmDialogProps = user.value.active
    ? {
        confirmText: 'Deactivate',
        severity: 'warning',
        text: 'Do you really want deactivate this account?',
        description:
          'Deactivating this account will lead to a temporary ban from Mergin Maps usage.'
      }
    : {
        text: 'Do you really want activate this account?',
        confirmText: 'Activate'
      }
  const dialog = { header: 'User activation' }
  const listeners = {
    confirm: async () => {
      await adminStore.updateUser({
        username: user.value.username,
        data: {
          active: !user.value.active
        }
      })
    }
  }
  dialogStore.show({
    component: ConfirmDialog,
    params: {
      props,
      listeners,
      dialog
    }
  })
}

const confirmDeleteUser = () => {
  const props: ConfirmDialogProps = {
    text: `Are you sure you want to permanently delete this account?`,
    description: `Deleting this user will remove them
      and all their data. This action cannot be undone. Type in username to confirm:`,
    hint: user.value.username,
    confirmText: 'Delete permanently',
    confirmField: {
      label: 'Username',
      expected: user.value.username
    },
    severity: 'danger'
  }
  const listeners = {
    confirm: async () =>
      await adminStore.deleteUser({ username: user.value.username })
  }
  dialogStore.show({
    component: ConfirmDialog,
    params: { props, listeners, dialog: { header: 'Delete user' } }
  })
}

const switchAdminAccess = async () => {
  const props: ConfirmDialogProps = !user.value?.is_admin
    ? {
        text: `Are you sure to grant access to admin panel to this user?`,
        description: `This person will have full management access to all data on the server. They will see all users and projects and can update or remove them.`,
        hint: user.value.username,
        confirmText: 'Grant access',
        confirmField: {
          label: 'Username',
          expected: user.value.username
        },
        severity: 'warning'
      }
    : {
        text: `Are you sure you want to revoke access to admin panel to this user?`,
        description: `This person will no longer have access to the admin panel.`,
        hint: user.value.username,
        confirmText: 'Revoke access',
        confirmField: {
          label: 'Username',
          expected: user.value.username
        },
        severity: 'danger'
      }
  const listeners = {
    confirm: async () =>
      await adminStore.updateUser({
        username: user.value.username,
        data: {
          is_admin: !user.value.is_admin
        }
      })
  }
  dialogStore.show({
    component: ConfirmDialog,
    params: { props, listeners, dialog: { header: 'Admin access' } }
  })
}
</script>

<style lang="scss" scoped>
h2 {
  color: var(--text-color);
}

.project-view-detail-list {
  max-width: 640px;
  width: 100%;
}

.id-copy-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  margin: -0.25rem -0.5rem;
  padding: 0.25rem 0.5rem;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--text-color);
  font: inherit;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.15s ease;

  &:hover {
    background: var(--surface-hover);
  }

  &:disabled {
    cursor: default;
    opacity: 0.6;

    &:hover {
      background: transparent;
    }
  }

  i {
    font-size: 0.95rem;
    color: inherit;
  }
}
</style>
