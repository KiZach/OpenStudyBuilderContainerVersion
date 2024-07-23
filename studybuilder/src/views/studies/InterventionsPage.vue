<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('Sidebar.study.study_interventions') }} ({{
        studiesGeneralStore.studyId
      }})
      <HelpButton :help-text="$t('_help.StudyInterventionsTable.general')" />
    </div>
    <v-tabs v-model="tab" bg-color="white">
      <v-tab v-for="item of tabs" :key="item.tab" :value="item.tab">
        {{ item.name }}
      </v-tab>
    </v-tabs>
    <v-window v-model="tab" class="bg-white">
      <v-window-item value="overview">
        <InterventionOverview />
      </v-window-item>
      <v-window-item value="study_compounds">
        <CompoundTable />
      </v-window-item>
      <v-window-item value="study_compound_dosings">
        <CompoundDosingTable />
      </v-window-item>
      <v-window-item value="other_interventions">
        <UnderConstruction />
      </v-window-item>
    </v-window>
  </div>
</template>

<script>
import CompoundDosingTable from '@/components/studies/CompoundDosingTable.vue'
import CompoundTable from '@/components/studies/CompoundTable.vue'
import InterventionOverview from '@/components/studies/InterventionOverview.vue'
import UnderConstruction from '@/components/layout/UnderConstruction.vue'
import HelpButton from '@/components/tools/HelpButton.vue'
import { useAppStore } from '@/stores/app'
import { useStudiesGeneralStore } from '@/stores/studies-general'

export default {
  components: {
    CompoundDosingTable,
    CompoundTable,
    InterventionOverview,
    UnderConstruction,
    HelpButton,
  },
  setup() {
    const appStore = useAppStore()
    const studiesGeneralStore = useStudiesGeneralStore()
    return {
      addBreadcrumbsLevel: appStore.addBreadcrumbsLevel,
      studiesGeneralStore,
    }
  },
  data() {
    return {
      tab: null,
      tabs: [
        {
          tab: 'overview',
          name: this.$t('Sidebar.study.study_intervention_overview'),
        },
        { tab: 'study_compounds', name: this.$t('Sidebar.study.compounds') },
        {
          tab: 'study_compound_dosings',
          name: this.$t('Sidebar.study.compound_dosings'),
        },
        {
          tab: 'other_interventions',
          name: this.$t('Sidebar.study.other_interventions'),
        },
      ],
    }
  },
  watch: {
    tab(newValue) {
      const tabName = newValue
        ? this.tabs.find((el) => el.tab === newValue).name
        : this.tabs[0].name
      this.$router.push({
        name: 'StudyInterventions',
        params: { tab: newValue },
      })
      this.addBreadcrumbsLevel(
        tabName,
        {
          name: 'StudyInterventions',
          params: {
            study_id: this.studiesGeneralStore.selectedStudy.uid,
            tab: tabName,
          },
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
          name: 'StudyInterventions',
          params: {
            study_id: this.studiesGeneralStore.selectedStudy.uid,
            tab: tabName,
          },
        },
        3,
        true
      )
    }, 100)
  },
}
</script>
