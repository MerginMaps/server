<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <page-view
    :style="`padding-left: ${
      drawer ? 280 : 20
    }px; overflow-y: auto; padding-right:20px; margin-right: 0px;`"
  >
    <v-layout class="column fill-height main-content">
      <v-container>
        <slot name="usageInfo" />
        <v-row v-if="projectsCount === 0 && canCreateProject">
          <v-card outlined class="bubble mt-3">
            <h3>Welcome {{ loggedUser.username }}, are you ready to start?</h3>
            <p>
              First create new project, add people to it or explore public
              project for more inspiration
            </p>
            <v-btn color="orange" @click="newProjectDialog(loggedUser.email)"
              ><span style="color: white">New project</span>
            </v-btn>
          </v-card>
        </v-row>
        <v-row>
          <v-col class="pa-0">
            <v-card class="bubble mt-3" outlined>
              <h3>Download Mergin Maps Input app</h3>
              <p>
                Capture geo-info easily through your mobile/tablet with the
                Mergin Maps Input app. Designed to be compatible with all mobile
                devices - even those with small screens.
              </p>
              <v-row>
                <v-col cols="7" md="3" sm="3">
                  <div class="store-button">
                    <a
                      href="https://play.google.com/store/apps/details?id=uk.co.lutraconsulting&utm_source=mergin-website&utm_medium=banner&utm_campaign=input"
                      target="_blank"
                    >
                      <img
                        alt="Get it on Google Play"
                        src="https://play.google.com/intl/en_us/badges/images/generic/en_badge_web_generic.png"
                        height="70px"
                      />
                    </a>
                  </div>
                </v-col>
                <v-col cols="7" md="3" sm="3">
                  <div class="store-button app-store-button">
                    <a
                      href="https://apps.apple.com/us/app/input/id1478603559?ls=1&utm_source=mergin-website&utm_medium=banner&utm_campaign=input"
                      target="_blank"
                    >
                      <img
                        alt="Get it on Apple store"
                        src="@/assets/App_Store.svg"
                        height="48px"
                      />
                    </a>
                  </div>
                </v-col>
                <v-col cols="7" md="3" sm="3">
                  <div class="store-button huawei-store-button">
                    <a
                      href="https://appgallery.huawei.com/app/C104422773"
                      target="_blank"
                    >
                      <img
                        alt="Explore it on AppGallery"
                        src="@/assets/huawei.svg"
                        height="48px"
                      />
                    </a>
                  </div>
                </v-col>
              </v-row>
            </v-card>
          </v-col>
        </v-row>
        <slot name="content"></slot>
      </v-container>
    </v-layout>
  </page-view>
</template>

<script lang="ts">
import { mapActions, mapState } from 'pinia'
import { defineComponent } from 'vue'

import { useDialogStore } from '@/modules'
import PageView from '@/modules/layout/components/PageView.vue'
import { useLayoutStore } from '@/modules/layout/store'
import ProjectForm from '@/modules/project/components/ProjectForm.vue'
import { useProjectStore } from '@/modules/project/store'
import { useUserStore } from '@/modules/user/store'

export default defineComponent({
  name: 'DashboardViewTemplate',
  components: {
    PageView
  },
  props: {
    canCreateProject: {
      type: Boolean,
      default: false
    }
  },
  computed: {
    ...mapState(useLayoutStore, ['drawer']),
    ...mapState(useUserStore, ['loggedUser']),
    ...mapState(useProjectStore, ['projectsCount'])
  },
  async created() {
    await this.fetchAccessRequests()
  },
  methods: {
    ...mapActions(useDialogStore, ['show']),
    ...mapActions(useProjectStore, {
      fetchAccessRequests: 'fetchAccessRequests'
    }),

    newProjectDialog() {
      const dialog = { maxWidth: 500, persistent: true }
      this.show({
        component: ProjectForm,
        params: {
          dialog
        }
      })
    }
  }
})
</script>

<style scoped lang="scss">
@import 'src/sass/dashboard';

.v-navigation-drawer {
  -webkit-overflow-scrolling: touch;
  display: -webkit-box;
  display: -ms-flexbox;
  display: flex;
  -webkit-box-orient: vertical;
  -webkit-box-direction: normal;
  -ms-flex-direction: column;
  flex-direction: column;
  left: 0;
  max-width: 100%;
  overflow: hidden;
  pointer-events: auto;
  top: 0;
  -webkit-transition-duration: 0.2s;
  transition-duration: 0.2s;
  -webkit-transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  will-change: transform;
  -webkit-transition-property: width, -webkit-transform;
  transition-property: width, -webkit-transform;
  transition-property: transform, width;
  transition-property: transform, width, -webkit-transform;
}

.store-button {
  text-align: center;
}

.app-store-button {
  padding-top: 11px;
}

.huawei-store-button {
  padding-top: 10px;
}

@media only screen and (max-width: 599px) {
  .store-button {
    text-align: left;
  }

  .app-store-button {
    padding-left: 12px;
    padding-top: 0;
  }
  .huawei-store-button {
    padding-left: 12px;
    padding-top: 0;
  }
}

@media only screen and (min-width: 600px) and (max-width: 960px) {
  .app-store-button {
    margin-left: 25%;
  }
  .huawei-store-button {
    margin-left: 35%;
  }
}
</style>
