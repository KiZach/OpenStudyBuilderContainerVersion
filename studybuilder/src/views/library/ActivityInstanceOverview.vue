<template>
  <div v-if="activityInstanceOverview" class="px-4">
    <div class="d-flex page-title">
      {{ activityInstanceOverview.activity_instance.name }}
      <HelpButtonWithPanels
        :help-text="$t('_help.ActivityInstanceOverview.general')"
        :items="helpItems"
      />
    </div>
    <ActivityInstanceOverview
      v-if="activityInstanceOverview"
      source="activity-instances"
      :item-uid="$route.params.id"
      :item-overview="activityInstanceOverview"
      :yaml-version="activityInstanceYAML"
      :cosmos-version="activityInstanceCOSMoS"
      @refresh="fetchOverview"
      @close-page="closePage"
    />
  </div>
</template>

<script>
import ActivityInstanceOverview from '@/components/library/ActivityInstanceOverview.vue'
import activities from '@/api/activities'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels.vue'
import { useAppStore } from '@/stores/app'

export default {
  components: {
    ActivityInstanceOverview,
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
      activityInstanceOverview: null,
      activityInstanceYAML: null,
      activityInstanceCOSMoS: null,
      helpItems: [
        'ActivityInstanceOverview.cosmos_yaml',
        'ActivityInstanceOverview.class',
        'ActivityInstanceOverview.adam_code',
        'ActivityInstanceOverview.topic_code',
        'ActivityInstanceOverview.activity_group',
        'ActivityInstanceOverview.activity_subgroup',
        'ActivityInstanceOverview.activity',
        'ActivityInstanceOverview.activity_groupings',
        'ActivityInstanceOverview.is_required_for_activity',
        'ActivityInstanceOverview.is_default_selected_for_activity',
        'ActivityInstanceOverview.is_data_sharing',
        'ActivityInstanceOverview.is_legacy_usage',
        'ActivityInstanceOverview.item_type',
        'ActivityInstanceOverview.items',
        'ActivityInstanceOverview.item_class',
      ],
    }
  },
  created() {
    this.fetchOverview()
  },
  methods: {
    fetchOverview() {
      activities
        .getObjectOverview(
          'activity-instances',
          this.$route.params.id,
          this.$route.params.version
        )
        .then((resp) => {
          this.activityInstanceOverview = resp.data
          this.addBreadcrumbsLevel(
            this.activityInstanceOverview.activity_instance.name,
            { name: 'ActivityInstanceOverview', params: this.$route.params },
            4
          )
        })
      activities
        .getObjectOverview(
          'activity-instances',
          this.$route.params.id,
          this.$route.params.version,
          'yaml'
        )
        .then((resp) => {
          this.activityInstanceYAML = resp.data
        })
      activities
        .getCOSMoSOverview('activity-instances', this.$route.params.id)
        .then((resp) => {
          this.activityInstanceCOSMoS = resp.data
        })
    },
    closePage() {
      this.$router.push({
        name: 'Activities',
        params: { tab: 'activity-instances' },
      })
    },
  },
}
</script>
