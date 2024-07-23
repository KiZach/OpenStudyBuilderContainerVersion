<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('StudyRegistryIdentifiersView.title') }} ({{ studyId }})
      <HelpButton :help-text="$t('_help.RegistryIdentifiersTable.general')" />
    </div>
    <RegistryIdentifiersSummary />
    <CommentThreadList
      :topic-path="'/studies/' + selectedStudy.uid + '/registry_identifiers'"
      :is-transparent="false"
    />
  </div>
</template>

<script>
import { computed } from 'vue'
import RegistryIdentifiersSummary from '@/components/studies/RegistryIdentifiersSummary.vue'
import HelpButton from '@/components/tools/HelpButton.vue'
import CommentThreadList from '@/components/tools/CommentThreadList.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'

export default {
  components: {
    RegistryIdentifiersSummary,
    CommentThreadList,
    HelpButton,
  },
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    return {
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
      studyId: studiesGeneralStore.studyId,
    }
  },
}
</script>
