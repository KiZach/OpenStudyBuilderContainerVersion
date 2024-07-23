<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('StudyProtocolElementsView.title') }} ({{ studyId }})
      <HelpButton :help-text="$t('_help.ProtocolElementsTable.general')" />
      <v-spacer/>
      <v-btn
        color="primary"
        size="small"
        icon="mdi-cog-outline"
        :disabled="lockSettings"
        :loading="soaContentLoadingStore.loading"
        @click="openSoaSettings"
      />
    </div>
    <v-tabs v-model="tab" bg-color="white">
      <v-tab v-for="item of tabs" :key="item.tab" :value="item.tab">
        {{ item.name }}
      </v-tab>
    </v-tabs>
    <v-window v-model="tab" class="bg-white">
      <v-window-item value="tab-0">
        <ProtocolTitlePage />
      </v-window-item>
      <v-window-item value="tab-1">
        <ProtocolFlowchart
          :study-uid="selectedStudy.uid"
          :update="updateFlowchart"
        />
      </v-window-item>
      <v-window-item value="tab-2">
        <ProtocolElementsObjectiveTable
          :study-uid="selectedStudy.uid"
          :update="updateObjectives"
        />
      </v-window-item>
      <v-window-item value="tab-3">
        <ProtocolElementsStudyDesign
          :study-uid="selectedStudy.uid"
          :update="updateDesign"
        />
      </v-window-item>
      <v-window-item value="tab-4">
        <ProtocolElementsStudyPopulationSummary />
      </v-window-item>
      <v-window-item value="tab-5">
        <ProtocolElementsStudyInterventions
          :study-uid="selectedStudy.uid"
          :update="updateInterventions"
        />
      </v-window-item>
      <v-window-item value="tab-6">
        <ProtocolElementsProceduresAndActivities />
      </v-window-item>
    </v-window>
    <v-dialog v-model="showSoaSettings" max-width="800px">
      <SoaSettingsForm
        @close="closeSoaSettings"
      />
    </v-dialog>
  </div>
</template>

<script>
import { computed } from 'vue'
import ProtocolElementsObjectiveTable from '@/components/studies/ProtocolElementsObjectiveTable.vue'
import ProtocolElementsStudyPopulationSummary from '@/components/studies/ProtocolElementsStudyPopulationSummary.vue'
import ProtocolElementsStudyDesign from '@/components/studies/ProtocolElementsStudyDesign.vue'
import ProtocolElementsStudyInterventions from '@/components/studies/ProtocolElementsStudyIntervention.vue'
import ProtocolElementsProceduresAndActivities from '@/components/studies/ProtocolElementsProceduresAndActivities.vue'
import ProtocolFlowchart from '@/components/studies/ProtocolFlowchart.vue'
import ProtocolTitlePage from '@/components/studies/ProtocolTitlePage.vue'
import HelpButton from '@/components/tools/HelpButton.vue'
import SoaSettingsForm from '@/components/studies/SoaSettingsForm.vue'
import { useAppStore } from '@/stores/app'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useSoaContentLoadingStore } from '@/stores/soa-content-loading'
import { useAccessGuard } from '@/composables/accessGuard'

export default {
  components: {
    ProtocolElementsObjectiveTable,
    ProtocolFlowchart,
    ProtocolTitlePage,
    ProtocolElementsStudyPopulationSummary,
    ProtocolElementsStudyDesign,
    ProtocolElementsStudyInterventions,
    ProtocolElementsProceduresAndActivities,
    HelpButton,
    SoaSettingsForm,
  },
  setup() {
    const appStore = useAppStore()
    const studiesGeneralStore = useStudiesGeneralStore()
    const soaContentLoadingStore = useSoaContentLoadingStore()
    const accessGuard = useAccessGuard()
    return {
      addBreadcrumbsLevel: appStore.addBreadcrumbsLevel,
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
      selectedStudyVersion: computed(
        () => studiesGeneralStore.selectedStudyVersion
      ),
      studyId: computed(() => studiesGeneralStore.studyId),
      soaContentLoadingStore,
      ...accessGuard,
    }
  },
  data() {
    return {
      tab: null,
      updateFlowchart: 0,
      updateObjectives: 0,
      updateDesign: 0,
      updateInterventions: 0,
      showSoaSettings: false,
      tabs: [
        { tab: 'tab-0', name: this.$t('Sidebar.study.protocol_title') },
        {
          tab: 'tab-1',
          name: this.$t('StudyProtocolElementsView.protocol_soa'),
        },
        {
          tab: 'tab-2',
          name: this.$t('Sidebar.study.objective_endpoints_estimands'),
        },
        { tab: 'tab-3', name: this.$t('Sidebar.study.study_design') },
        { tab: 'tab-4', name: this.$t('Sidebar.study.study_population') },
        {
          tab: 'tab-5',
          name: this.$t('Sidebar.study.study_interventions_and_therapy'),
        },
        { tab: 'tab-6', name: this.$t('Sidebar.study.study_activities') },
      ],
    }
  },
  computed: {
    lockSettings() {
      if(!this.checkPermission(this.$roles.STUDY_WRITE) || this.selectedStudyVersion !== null) {
        return true
      }
      return false
    },
  },
  watch: {
    tab(value) {
      const tabName = value
        ? this.tabs.find((el) => el.tab === value).name
        : this.tabs[0].name
      this.$router.push({
        name: 'ProtocolElements',
        params: { study_id: this.selectedStudy.uid, tab: tabName },
      })
      this.addBreadcrumbsLevel(
        tabName,
        {
          name: 'ProtocolElements',
          params: { study_id: this.selectedStudy.uid, tab: tabName },
        },
        3,
        true
      )
      localStorage.setItem('templatesTab', value)
      switch (value) {
        case 'tab-1':
          this.updateFlowchart++
          break
        case 'tab-2':
          this.updateObjectives++
          break
        case 'tab-3':
          this.updateDesign++
          break
        case 'tab-5':
          this.updateInterventions++
          break
      }
    },
  },
  mounted() {
    this.tab = localStorage.getItem('templatesTab') || 'tab-0'
    const tabName = this.tab
      ? this.tabs.find((el) => el.tab === this.tab).name
      : this.tabs[0].name
    setTimeout(() => {
      this.addBreadcrumbsLevel(
        tabName,
        {
          name: 'ProtocolElements',
          params: { study_id: this.selectedStudy.uid, tab: tabName },
        },
        3,
        true
      )
    }, 100)
  },
  methods: {
    openSoaSettings() {
      this.showSoaSettings = true
    },
    closeSoaSettings() {
      this.updateFlowchart++
      this.showSoaSettings = false
    }
  }
}
</script>
