<!--
Copyright (C) Lutra Consulting Limited

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
-->

<template>
  <article class="overview">
    <div class="grid" v-if="usage">
      <overview-card v-if="usage?.active_monthly_contributors" class="col-12 sm:col-6 lg:col-3">
        <template #heading>Active monthly contributors</template>
        <div
          class="w-full"
          :style="{
            height: '40px'
          }"
        >
          <PProgressBar
            :value="0"
            :show-value="false"
          ></PProgressBar>
        </div>
        <template #title
              ><span
                >{{ this.usage?.active_monthly_contributors[0] }}</span
              ></template
            >
            <template #subtitle>this month</template>
        <template #footer>
            <PButton
              @click=""
              class="w-full"
              label="See more"
            />
          </template>
      </overview-card>
      <overview-card v-if="usage?.storage" class="col-12 sm:col-6 lg:col-3">
        <template #heading>Used storage</template>
        <div
          class="w-full"
          :style="{
            height: '40px'
          }"
        >
          <PProgressBar
            :value="0"
            :show-value="false"
          ></PProgressBar>
        </div>
        <template #title
              ><span
                >{{ this.usage?.storage }}</span
              ></template
            >
      </overview-card>
      <overview-card v-if="usage?.users" class="col-12 sm:col-6 lg:col-3">
        <template #heading>Registered accounts</template>
        <div
          class="w-full"
          :style="{
            height: '40px'
          }"
        >
          <PProgressBar
            :value="0"
            :show-value="false"
          ></PProgressBar>
        </div>
        <template #title
              ><span
                >{{ this.usage?.users }}</span
              ></template
            >
        <template #footer>
            <PButton
              @click="$router.push({name: AdminRoutes.PROJECTS})"
              class="w-full"
              label="Manage users"
            />
          </template>
      </overview-card>
    </div>
  </article>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { OverviewCard } from "@mergin/lib"
import {AdminRoutes, useAdminStore} from "@/modules";
import { mapState } from "pinia";
import {useRouter} from "vue-router";

export default defineComponent({
  name: 'OverviewView',
  components: { OverviewCard },
  computed: {
    AdminRoutes() {
      return AdminRoutes
    },
    ...mapState(useAdminStore, ['usage', useRouter()]),
  },
  methods: {
    getUsage(): any {
      const adminStore = useAdminStore()
      adminStore.getServerUsage()
    }
  },
  mounted() {
    this.getUsage();
  }
})

</script>


<style lang="scss" scoped>
.overview {
  margin-bottom: 30px;

  &-cards {
    min-height: 290px;
  }
}
</style>
