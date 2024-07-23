<template>
  <div>
    <div class="d-flex page-title">
      {{ $t('StudyArmsForm.study_arm') + ': ' + arm.name }}
      <v-chip
        :color="arm.arm_colour"
        size="small"
        class="mt-2 ml-2"
        variant="flat"
      />
      <v-spacer />
      <v-btn
        size="small"
        :title="$t('_global.close')"
        class="ml-2"
        variant="text"
        @click="close"
      >
        <v-icon>{{ 'mdi-close' }}</v-icon>
      </v-btn>
    </div>
    <v-card elevation="0" class="rounded-0">
      <v-card-text>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyArmsForm.arm_short_name') }}
          </v-col>
          <v-col cols="2">
            {{ arm.short_name }}
          </v-col>
        </v-row>
        <v-row v-if="arm.arm_type">
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyArmsForm.arm_type') }}
          </v-col>
          <v-col cols="2">
            {{ arm.arm_type.sponsor_preferred_name }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyArmsForm.randomisation_group') }}
          </v-col>
          <v-col cols="2">
            {{ arm.randomization_group }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyArmsForm.arm_code') }}
          </v-col>
          <v-col cols="2">
            {{ arm.code }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyArmsForm.planned_number') }}
          </v-col>
          <v-col cols="2">
            {{ arm.number_of_subjects }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyArmsForm.description') }}
          </v-col>
          <v-col cols="2">
            {{ arm.description }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyArmsForm.connected_branches') }}
          </v-col>
          <v-col cols="10">
            <v-data-table
              class="elevation-0"
              :headers="branchesHeaders"
              :items="
                arm.arm_connected_branch_arms
                  ? arm.arm_connected_branch_arms
                  : []
              "
              item-value="branch_arm_uid"
            >
              <template #bottom />
              <template #[`item.name`]="{ item }">
                <router-link
                  :to="{
                    name: 'StudyBranchArmOverview',
                    params: {
                      study_id: selectedStudy.uid,
                      id: item.branch_arm_uid,
                      root_tab: $route.params.root_tab,
                    },
                  }"
                >
                  {{ item.name }}
                </router-link>
              </template>
            </v-data-table>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
  </div>
</template>

<script>
import { computed } from 'vue'
import arms from '@/api/arms'
import { useStudiesGeneralStore } from '@/stores/studies-general'

export default {
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    return {
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
    }
  },
  data() {
    return {
      arm: {},
      branchesHeaders: [
        { title: '#', key: 'order', width: '5%' },
        { title: this.$t('StudyBranchArms.name'), key: 'name' },
        { title: this.$t('StudyBranchArms.short_name'), key: 'short_name' },
        {
          title: this.$t('StudyBranchArms.randomisation_group'),
          key: 'randomization_group',
        },
        { title: this.$t('StudyBranchArms.code'), key: 'code' },
        { title: this.$t('StudyBranchArms.description'), key: 'description' },
      ],
    }
  },
  mounted() {
    arms
      .getStudyArm(this.$route.params.study_id, this.$route.params.id)
      .then((resp) => {
        this.arm = resp.data
      })
  },
  methods: {
    close() {
      this.$router.push({ name: 'StudyStructure', params: { tab: 'arms' } })
    },
  },
}
</script>
