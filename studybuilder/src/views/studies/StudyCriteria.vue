<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('Sidebar.study.study_criteria') }} ({{ studyId }})
      <HelpButtonWithPanels :items="helpItems" />
    </div>
    <v-tabs v-model="tab" bg-color="white">
      <v-tab
        v-for="type in criteriaTypes"
        :key="type.term_uid"
        :value="type.name.sponsor_preferred_name"
      >
        {{ type.name.sponsor_preferred_name }}
      </v-tab>
    </v-tabs>
    <v-window v-model="tab">
      <v-window-item
        v-for="type in criteriaTypes"
        :key="type.term_uid"
        :value="type.name.sponsor_preferred_name"
      >
        <EligibilityCriteriaTable :criteria-type="type" />
      </v-window-item>
    </v-window>
  </div>
</template>

<script>
import { computed } from 'vue'
import EligibilityCriteriaTable from '@/components/studies/EligibilityCriteriaTable.vue'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels.vue'
import terms from '@/api/controlledTerminology/terms'
import { useAppStore } from '@/stores/app'
import { useStudiesGeneralStore } from '@/stores/studies-general'

export default {
  components: {
    EligibilityCriteriaTable,
    HelpButtonWithPanels,
  },
  setup() {
    const appStore = useAppStore()
    const studiesGeneralStore = useStudiesGeneralStore()
    return {
      addBreadcrumbsLevel: appStore.addBreadcrumbsLevel,
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
      studyId: studiesGeneralStore.studyId,
    }
  },
  data() {
    return {
      criteriaTypes: [],
      tab: null,
      helpItems: [
        'StudyCriteriaTable.general',
        'StudyCriteriaTable.study_criteria',
      ],
    }
  },
  watch: {
    tab(newValue) {
      this.$router.push({
        name: 'StudySelectionCriteria',
        params: { study_id: this.selectedStudy.uid, tab: newValue },
      })
      this.addBreadcrumbsLevel(
        newValue,
        {
          name: 'StudySelectionCriteria',
          params: { study_id: this.selectedStudy.uid, tab: newValue },
        },
        3,
        true
      )
    },
  },
  mounted() {
    terms.getByCodelist('criteriaTypes').then((resp) => {
      this.criteriaTypes = resp.data.items
      this.tab =
        this.$route.params.tab ||
        this.criteriaTypes[0].name.sponsor_preferred_name
    })
  },
}
</script>

<style scoped>
.v-window {
  min-height: 50vh;
}
</style>
