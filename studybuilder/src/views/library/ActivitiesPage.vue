<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('Sidebar.library.activities') }}
      <HelpButtonWithPanels
        :help-text="$t('_help.ActivitiesTable.general')"
        :items="helpItems"
      />
    </div>
    <v-tabs v-model="tab" bg-color="white">
      <v-tab v-for="item of tabs" :key="item.tab" :value="item.tab">
        {{ item.name }}
      </v-tab>
    </v-tabs>
    <v-window v-model="tab">
      <v-window-item value="activities">
        <ActivitiesTable source="activities" />
      </v-window-item>
      <v-window-item value="activity-groups">
        <ActivitiesTable source="activity-groups" />
      </v-window-item>
      <v-window-item value="activity-subgroups">
        <ActivitiesTable source="activity-sub-groups" />
      </v-window-item>
      <v-window-item value="activities-by-grouping">
        <ActivitiesTable source="activities-by-grouping" />
      </v-window-item>
      <v-window-item value="activity-instances">
        <ActivitiesTable source="activity-instances" />
      </v-window-item>
      <v-window-item value="requested-activities">
        <ActivitiesTable source="activities" requested />
      </v-window-item>
    </v-window>
  </div>
</template>

<script>
import ActivitiesTable from '@/components/library/ActivitiesTable.vue'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels.vue'
import { useAppStore } from '@/stores/app'

export default {
  components: {
    ActivitiesTable,
    HelpButtonWithPanels,
  },
  setup() {
    const appStore = useAppStore()
    return {
      addBreadcrumbsLevel: appStore.addBreadcrumbsLevel,
    }
  },
  data() {
    return {
      tab: null,
      tabs: [
        { tab: 'activities', name: this.$t('ActivityTable.activities') },
        {
          tab: 'activity-groups',
          name: this.$t('ActivityTable.activity_groups'),
        },
        {
          tab: 'activity-subgroups',
          name: this.$t('ActivityTable.activity_subgroups'),
        },
        {
          tab: 'activities-by-grouping',
          name: this.$t('ActivityTable.activities_overview'),
        },
        { tab: 'activity-instances', name: this.$t('ActivityTable.instances') },
        {
          tab: 'requested-activities',
          name: this.$t('ActivityTable.requested'),
        },
      ],
      helpItems: [
        'ActivityTable.activities',
        'ActivityTable.activity_groups',
        'ActivityTable.activity_subgroups',
        'ActivityTable.activities_overview',
        'ActivityTable.instances',
        'ActivityTable.requested',
        'ActivityTable.activity_name',
        'ActivityTable.sentence_case_name',
        'ActivityTable.abbreviation',
        'ActivityTable.definition',
        'ActivityTable.nci_concept_id',
        'ActivityTable.topic_code',
        'ActivityTable.adam_code',
        'ActivityTable.activity_group',
        'ActivityTable.activity_subgroup',
        'ActivityTable.is_data_collected',
        'ActivityTable.activity',
        'ActivityTable.instance',
        'ActivityTable.is_required_for_activity',
        'ActivityTable.is_default_selected_for_activity',
        'ActivityTable.is_data_sharing',
        'ActivityTable.is_legacy_usage',
        'ActivityTable.rationale_for_request',
      ],
    }
  },
  watch: {
    tab(newValue) {
      const tab = newValue || this.tabs[0].tab
      this.$router.push({
        name: 'Activities',
        params: { tab },
      })
      const tabName = this.tabs.find((el) => el.tab === tab).name
      this.addBreadcrumbsLevel(
        tabName,
        { name: 'Activities', params: { tab } },
        3,
        true
      )
    },
  },
  created() {
    this.tab = this.$route.params.tab
  },
}
</script>
