<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('StudyPopulationView.title') }} ({{ studyId }})
      <HelpButton :help-text="$t('_help.StudyPopulationTable.general')" />
    </div>
    <StudyPopulationSummary />
  </div>
</template>

<script>
import StudyPopulationSummary from '@/components/studies/StudyPopulationSummary.vue'
import HelpButton from '@/components/tools/HelpButton.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'

export default {
  components: {
    StudyPopulationSummary,
    HelpButton,
  },
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    return {
      studyId: studiesGeneralStore.studyId,
    }
  },
}
</script>
