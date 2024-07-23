<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('Sidebar.study.study_properties') }} ({{ studyId }})
      <HelpButtonWithPanels
        :help-text="$t('_help.StudyProperties.general')"
        :items="helpItems"
      />
    </div>
    <v-tabs v-model="tab" bg-color="white">
      <v-tab v-for="item of tabs" :key="item.tab" :value="item.tab">
        {{ item.name }}
      </v-tab>
    </v-tabs>
    <v-window v-model="tab">
      <v-window-item value="type">
        <StudyTypeSummary />
      </v-window-item>
      <v-window-item value="attributes">
        <InterventionTypeSummary />
      </v-window-item>
    </v-window>
  </div>
</template>

<script>
import { computed } from 'vue'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels.vue'
import InterventionTypeSummary from '@/components/studies/InterventionTypeSummary.vue'
import StudyTypeSummary from '@/components/studies/StudyTypeSummary.vue'
import { useAppStore } from '@/stores/app'
import { useStudiesGeneralStore } from '@/stores/studies-general'

export default {
  components: {
    InterventionTypeSummary,
    HelpButtonWithPanels,
    StudyTypeSummary,
  },
  setup() {
    const appStore = useAppStore()
    const studiesGeneralStore = useStudiesGeneralStore()
    return {
      addBreadcrumbsLevel: appStore.addBreadcrumbsLevel,
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
      studyId: computed(() => studiesGeneralStore.studyId),
    }
  },
  data() {
    return {
      helpItems: ['StudyProperties.study_type'],
      tab: null,
      tabs: [
        { tab: 'type', name: this.$t('Sidebar.study.study_type') },
        { tab: 'attributes', name: this.$t('Sidebar.study.study_attributes') },
      ],
    }
  },
  watch: {
    tab(newValue) {
      this.$router.push({
        name: 'StudyProperties',
        params: { tab: newValue },
      })
      const tabName = newValue
        ? this.tabs.find((el) => el.tab === newValue).name
        : this.tabs[0].name
      this.addBreadcrumbsLevel(
        tabName,
        {
          name: 'StudyProperties',
          params: { study_id: this.selectedStudy.uid, tab: tabName },
        },
        3,
        true
      )
    },
  },
  mounted() {
    this.tab = this.$route.params.tab || this.tabs[0].tab
    const tabName = this.tab
      ? this.tabs.find((el) => el.tab === this.tab).name
      : this.tabs[0].name
    setTimeout(() => {
      this.addBreadcrumbsLevel(
        tabName,
        {
          name: 'StudyProperties',
          params: { study_id: this.selectedStudy.uid, tab: tabName },
        },
        3,
        true
      )
    }, 100)
  },
}
</script>
