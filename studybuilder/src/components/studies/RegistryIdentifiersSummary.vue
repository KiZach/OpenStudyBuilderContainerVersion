<template>
  <StudyMetadataSummary
    :metadata="identifiers"
    :params="params"
    :first-col-label="
      $t('StudyRegistryIdentifiersSummary.registry_identifiers')
    "
    :fullscreen-form="false"
    form-max-width="1000px"
    component="registry_identifiers"
    :disable-edit="studiesGeneralStore.selectedStudy.study_parent_part"
  >
    <template #form="{ closeHandler, openHandler }">
      <RegistryIdentifiersForm
        :open="openHandler"
        :identifiers="identifiers"
        @close="closeHandler"
        @updated="onIdentifiersUpdated"
      />
    </template>
  </StudyMetadataSummary>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import study from '@/api/study'
import RegistryIdentifiersForm from './RegistryIdentifiersForm.vue'
import StudyMetadataSummary from './StudyMetadataSummary.vue'
import studyConstants from '@/constants/study'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { i18n } from '@/plugins/i18n'

const studiesGeneralStore = useStudiesGeneralStore()

const identifiers = ref({})

const params = computed(() => {
  const result = []
  for (const key of studyConstants.REGISTRY_IDENTIFIERS) {
    result.push({
      label: i18n.t(`RegistryIdentifiersForm.${key}`),
      name: key,
      nullValueName: `${key}_null_value_code`,
    })
  }
  return result
})

function onIdentifiersUpdated(value) {
  identifiers.value = value
}

onMounted(() => {
  studiesGeneralStore.fetchNullValues()
  const studyUid = studiesGeneralStore.selectedStudy.study_parent_part
    ? studiesGeneralStore.selectedStudy.study_parent_part.uid
    : studiesGeneralStore.selectedStudy.uid
  study
    .getStudy(studyUid, false)
    .then((resp) => {
      identifiers.value =
        resp.data.current_metadata.identification_metadata.registry_identifiers
    })
})
</script>
