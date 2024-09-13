<template>
  <article>
    <admin-layout>
      <app-container>
        <app-section ground>
          <template #header>
            <h1 class="headline-h3">Account details</h1>
          </template>
        </app-section>
      </app-container>

      <app-container>
        <app-section class="p-4">
          <div
            class="flex flex-column align-items-center row-gap-3 text-center"
          >
            <PAvatar
              v-if="user"
              :label="$filters.getAvatar(user?.email, user?.username)"
              shape="circle"
              :pt="{
                root: {
                  class: 'text-5xl font-semibold text-color-forest',
                  style: {
                    width: '120px',
                    height: '120px'
                  }
                }
              }"
            />
            <h3 class="headline-h2" data-cy="profile-username">
              {{ user?.username }}
            </h3>
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
              class="profile-view-detail-list grid grid-nogutter paragraph-p5"
            >
              <div
                class="col-6 flex flex-column align-items-start text-left flex-wrap"
              >
                <dt class="paragraph-p6 opacity-80 mb-2">Full name</dt>
                <dd class="font-semibold" data-cy="profile-name">
                  {{ profile.name || '-' }}
                </dd>
              </div>
              <div class="col-6 flex flex-column align-items-end">
                <dt class="paragraph-p6 opacity-80 mb-2">Registered</dt>
                <dd class="font-semibold" data-cy="profile-registered">
                  {{ $filters.date(user?.registration_date) }}
                </dd>
              </div>
            </dl>
          </div>
        </app-section>
      </app-container>
      <app-container>
        <app-section>
          <template #title>Advanced</template>
          <div class="flex flex-column row-gap-3 paragraph-p5 px-4 pb-4">
            <div
              :class="[
                'flex flex-column align-items-start',
                'row-gap-2',
                'md:align-items-center md:flex-row'
              ]"
            >
              <div class="flex-grow-1">
                <p class="title-t3">Receive notifications</p>
                <span class="paragraph-p6 opacity-80">
                  <template v-if="profile?.receive_notifications"
                    >User has enabled receiving notifications</template
                  >
                  <template v-else>User has disabled notifications.</template>
                </span>
              </div>
              <div class="flex-shrink-0 paragraph-p1">
                <i v-if="profile.receive_notifications" class="ti ti-check" />
                <i v-else class="ti ti-x" />
              </div>
            </div>

            <div
              :class="[
                'flex flex-column align-items-start',
                'row-gap-2',
                'md:align-items-center md:flex-row'
              ]"
            >
              <div class="flex-grow-1">
                <p class="title-t3">Access to admin panel</p>
                <span class="paragraph-p6 opacity-80">
                  Enabling this option will provide access to the admin panel.
                </span>
              </div>
              <div
                class="flex align-items-center flex-shrink-0"
                data-cy="profile-notification"
              >
                <PInputSwitch
                  :modelValue="user?.is_admin"
                  @change="switchAdminAccess"
                />
              </div>
            </div>

            <div
              :class="[
                'flex flex-column align-items-start',
                'row-gap-2',
                'md:align-items-center md:flex-row'
              ]"
            >
              <div class="flex-grow-1">
                <p class="title-t3">Account activation</p>
                <span class="paragraph-p6 opacity-80">
                  <template v-if="user?.active">
                    The user's account is currently active. Deactivation will
                    lead to a temporary ban from Mergin Maps usage.
                  </template>
                  <template v-else>
                    The user's account is currently inactive. Activating it will
                    allow access to Mergin Maps.
                  </template>
                </span>
              </div>
              <div class="flex-shrink-0">
                <PButton
                  @click="changeStatusDialog"
                  :severity="user?.active ? 'danger' : 'secondary'"
                  :label="
                    user?.active ? 'Deactivate account' : 'Activate account'
                  "
                  class="w-auto mr-1"
                />
              </div>
            </div>
            <div
              :class="[
                'flex flex-column align-items-start',
                'row-gap-2',
                'md:align-items-center md:flex-row'
              ]"
            >
              <div class="flex-grow-1">
                <p class="title-t3">Delete account</p>
                <span class="paragraph-p6 opacity-80"
                  >Deleting this user will remove them and all their data. This
                  action cannot be undone.</span
                >
              </div>
              <div class="flex-shrink-0">
                <PButton
                  @click="confirmDeleteUser"
                  severity="danger"
                  data-cy="profile-close-account-btn"
                  label="Delete account"
                />
              </div>
            </div>
          </div>
        </app-section>
      </app-container>
    </admin-layout>
  </article>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import {
  ConfirmDialog,
  useDialogStore,
  AppSection,
  AppContainer,
  UserResponse,
  ConfirmDialogProps
} from '@mergin/lib'

import AdminLayout from '@/modules/admin/components/AdminLayout.vue'
import { useAdminStore } from '@/modules/admin/store'

const route = useRoute()
const adminStore = useAdminStore()
const dialogStore = useDialogStore()

const user = computed<UserResponse>(() => adminStore.user)
const profile = computed(() => adminStore.user?.profile || {})
const routeUsername = computed(() => route?.params?.username)

const fetchProfile = (username: string) => {
  adminStore.user = null
  adminStore.fetchUserByName({ username })
}

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
  const props: ConfirmDialogProps = {
    confirmText: 'Yes',
    text: user.value.active
      ? 'Do you really want deactivate this account?'
      : 'Do you really want activate this account?'
  }
  const dialog = { header: 'User activation' }
  const listeners = {
    confirm: async () => {
      await adminStore.updateUser({
        username: user.value.username,
        data: {
          active: !user.value.active,
          is_admin: user.value.is_admin
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
  await adminStore.updateUser({
    username: user.value.username,
    data: {
      active: user.value.active,
      is_admin: !user.value.is_admin
    }
  })
}
</script>

<style lang="scss" scoped>
.profile-view-detail-list {
  max-width: 640px;
  width: 100%;
}
</style>
