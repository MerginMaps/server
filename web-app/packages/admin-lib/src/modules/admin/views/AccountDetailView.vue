<template>
  <admin-layout>
    <app-container>
      <app-section ground>
        <template #header>
          <h1 class="headline-h3">{{ $t('AccountDetails') }}</h1>
        </template>
      </app-section>
    </app-container>
    <template v-if="user">
      <app-container>
        <app-section class="p-4">
          <div
            class="flex flex-column align-items-center row-gap-3 text-center"
          >
            <PAvatar
              :label="$filters.getAvatar(user?.email, profile?.name)"
              size="xlarge"
              shape="circle"
              :pt="{
                root: {
                  class: 'font-semibold text-color-forest'
                }
              }"
            />
            <h3 class="headline-h2" data-cy="profile-name">
              {{
                profile?.name
                  ? `${profile.name} (${user?.username})`
                  : user.username
              }}
            </h3>
            <p
              class="m-0 paragraph-p6 overflow-wrap-anywhere"
              data-cy="profile-email"
            >
              <i
                v-if="!user?.verified_email"
                v-tooltip.top="{
                  value: $t('EmailVerificationStatus')
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
                <dt class="paragraph-p6 opacity-80 mb-2">
                  {{ $t('LastSignedIn') }}
                </dt>
                <dd class="font-semibold" data-cy="profile-last-signed-in">
                  {{ $filters.date(user.last_signed_in) || '-' }}
                </dd>
              </div>
              <div class="col-6 flex flex-column align-items-end">
                <dt class="paragraph-p6 opacity-80 mb-2">
                  {{ $t('Registered') }}
                </dt>
                <dd class="font-semibold" data-cy="profile-registered">
                  {{ $filters.date(user?.registration_date) }}
                </dd>
              </div>
            </dl>
          </div>
        </app-section>
      </app-container>
      <app-container v-if="userStore.loggedUser?.id !== user?.id">
        <app-section>
          <template #title>{{ $t('Advanced') }}</template>

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
                        ? $t('GrantAdminAccess')
                        : $t('RevokeAdminAccess')
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
                    user?.active
                      ? $t('DeactivateAccount')
                      : $t('ActivateAccount')
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
                  :label="$t('DeleteAccount')"
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
  useInstanceStore,
  useUserStore
} from '@mergin/lib'
import { computed, watch } from 'vue'
import { useRoute } from 'vue-router'

import returnTranslation from '@/../../lang/translate'
import AdminLayout from '@/modules/admin/components/AdminLayout.vue'
import { useAdminStore } from '@/modules/admin/store'

const route = useRoute()
const adminStore = useAdminStore()
const dialogStore = useDialogStore()
const instanceStore = useInstanceStore()
const userStore = useUserStore()
const t = (key: string) => returnTranslation(import.meta.env.VITE_LANG, key)

const settingsItems = computed<AppSettingsItemConfig[]>(() => [
  {
    key: 'notifications',
    title: t('ReceiveNotifications'),
    description: profile?.value?.receive_notifications
      ? t('UserHasEnabledReceivingNotifications')
      : t('UserHasDisabledNotifications')
  },
  {
    key: 'adminAccess',
    title: t('AccessToAdminPanel'),
    description: user.value?.is_admin
      ? t('UserHasAccessToTheAdminPanel')
      : t('UserDoesNotHaveAccessToTheAdminPanel')
  },
  {
    key: 'accountActivation',
    title: t('AccountActivation'),
    description: user?.value?.active
      ? t(
          'TheUsersAccountIsCurrentlyActiveDeactivationWillLeadToATemporaryBanFromMerginMapsUsage'
        )
      : t(
          'TheUsersAccountIsCurrentlyInactiveActivatingItWillAllowAccessToMerginMaps'
        )
  },
  {
    key: 'deleteAccount',
    title: t('DeleteAccount'),
    description: t(
      'DeletingThisUserWillRemoveThemAndAllTheirDataThisActionCannotBeUndone'
    )
  }
])

const user = computed(() => adminStore.user)
const profile = computed(() => adminStore.user?.profile)
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
  const props: ConfirmDialogProps = user.value.active
    ? {
        confirmText: t('Deactivate'),
        severity: 'warning',
        text: t('DoYouReallyWantDeactivateThisAccount'),
        description: t(
          'DeactivatingThisAccountWillLeadToATemporaryBanFromMerginMapsUsage'
        )
      }
    : {
        text: t('DoYouReallyWantActivateThisAccount'),
        confirmText: t('Activate')
      }
  const dialog = { header: t('UserActivation') }
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
    text: t('AreYouSureYouWantToPermanentlyDeleteThisAccount'),
    description: t(
      'DeletingThisUserWillRemoveThemAndAllTheirDataThisActionCannotBeUndoneTypeInUsernameToConfirm'
    ),
    hint: user.value.username,
    confirmText: t('DeletePermanently'),
    confirmField: {
      label: t('Username'),
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
    params: { props, listeners, dialog: { header: t('DeleteUser') } }
  })
}

const switchAdminAccess = async () => {
  const props: ConfirmDialogProps = !user.value?.is_admin
    ? {
        text: t('AreYouSureToGrantAccessToAdminPanelToThisUser'),
        description: t(
          'ThisPersonWillHaveFullManagementAccessToAllDataOnTheServerTheyWillSeeAllUsersAndProjectsAndCanUpdateOrRemoveThem'
        ),
        hint: user.value.username,
        confirmText: t('GrantAccess'),
        confirmField: {
          label: t('Username'),
          expected: user.value.username
        },
        severity: 'warning'
      }
    : {
        text: t('AreYouSureYouWantToRevokeAccessToAdminPanelToThisUser'),
        description: t('ThisPersonWillNoLongerHaveAccessToTheAdminPanel'),
        hint: user.value.username,
        confirmText: t('RevokeAccess'),
        confirmField: {
          label: t('Username'),
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
    params: { props, listeners, dialog: { header: t('AdminAccess') } }
  })
}
</script>

<style lang="scss" scoped>
.profile-view-detail-list {
  max-width: 640px;
  width: 100%;
}
</style>
