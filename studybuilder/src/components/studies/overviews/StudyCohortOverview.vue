<template>
  <div>
    <div class="d-flex page-title">
      {{ $t('StudyCohorts.study_cohort') + ': ' + cohort.name }}
      <v-chip
        :color="cohort.colour_code"
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
        icon="mdi-close"
        @click="close"
      />
    </div>
    <v-card elevation="0" class="rounded-0">
      <v-card-text>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyCohorts.cohort_short_name') }}
          </v-col>
          <v-col cols="2">
            {{ cohort.short_name }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyCohorts.cohort_code') }}
          </v-col>
          <v-col cols="2">
            {{ cohort.code }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyCohorts.number_of_subjects') }}
          </v-col>
          <v-col cols="2">
            {{ cohort.number_of_subjects }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyCohorts.description') }}
          </v-col>
          <v-col cols="2">
            {{ cohort.description }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyCohorts.connected_arms') }}
          </v-col>
          <v-col cols="10">
            <v-data-table
              class="elevation-0"
              :headers="armsHeaders"
              :items="cohort.arm_roots"
              item-value="arm_uid"
            >
              <template #bottom />
              <template #[`item.name`]="{ item }">
                <router-link
                  :to="{
                    name: 'StudyArmOverview',
                    params: {
                      study_id: selectedStudy.uid,
                      id: item.arm_uid,
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
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyCohorts.connected_branches') }}
          </v-col>
          <v-col cols="10">
            <v-data-table
              class="elevation-0"
              :headers="branchesHeaders"
              :items="cohort.branch_arm_roots || []"
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
              <template #[`item.arm_root.name`]="{ item }">
                <router-link
                  :to="{
                    name: 'StudyArmOverview',
                    params: {
                      study_id: selectedStudy.uid,
                      id: item.arm_root.arm_uid,
                      root_tab: $route.params.root_tab,
                    },
                  }"
                >
                  {{ item.arm_root.name }}
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
import arms from '@/api/arms'
import { computed } from 'vue'
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
      cohort: {},
      armsHeaders: [
        { title: '#', key: 'order', width: '5%' },
        {
          title: this.$t('StudyArmsTable.type'),
          key: 'arm_type.sponsor_preferred_name',
          width: '7%',
        },
        { title: this.$t('StudyArmsTable.name'), key: 'name' },
        { title: this.$t('StudyArmsTable.short_name'), key: 'short_name' },
        {
          title: this.$t('StudyArmsTable.randomisation_group'),
          key: 'randomization_group',
        },
        { title: this.$t('StudyArmsTable.code'), key: 'code' },
        { title: this.$t('StudyArmsTable.description'), key: 'description' },
      ],
      branchesHeaders: [
        { title: '#', key: 'order', width: '5%' },
        {
          title: this.$t('StudyBranchArms.arm_name'),
          key: 'arm_root.name',
          historyHeader: 'arm_root_uid',
        },
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
      .getStudyCohort(this.$route.params.study_id, this.$route.params.id)
      .then((resp) => {
        this.cohort = resp.data
      })
  },
  methods: {
    close() {
      this.$router.push({ name: 'StudyStructure', params: { tab: 'cohorts' } })
    },
  },
}
</script>
