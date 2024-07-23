<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('StudyManageView.title') }}
      <HelpButton :help-text="$t('_help.SelectOrAddStudyTable.general')" />
    </div>
    <v-tabs v-model="tab" bg-color="white">
      <v-tab value="active">
        {{ $t('SelectOrAddStudyTable.tab1_title') }}
      </v-tab>
      <v-tab value="deleted">
        {{ $t('SelectOrAddStudyTable.tab2_title') }}
      </v-tab>
    </v-tabs>
    <v-window v-model="tab">
      <v-window-item value="active">
        <StudyTable
          key="activeStudies"
          :items="activeStudies"
          :items-length="totalActiveStudies"
          @filter="fetchActiveStudies"
          @refresh-studies="fetchActiveStudies"
        />
      </v-window-item>
      <v-window-item value="deleted">
        <StudyTable
          key="deletedStudies"
          :items="deletedStudies"
          :items-length="totalDeletedStudies"
          read-only
          @filter="fetchDeletedStudies"
        />
      </v-window-item>
    </v-window>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import api from '@/api/study'
import filteringParameters from '@/utils/filteringParameters'
import StudyTable from '@/components/studies/StudyTable.vue'
import HelpButton from '@/components/tools/HelpButton.vue'
import { useStudiesManageStore } from '@/stores/studies-manage'
import { useI18n } from 'vue-i18n'

const appStore = useAppStore()
const studiesManageStore = useStudiesManageStore()
const router = useRouter()
const route = useRoute()
const { t } = useI18n()

const activeStudies = ref([])
const activeOptions = ref({})
const deletedStudies = ref([])
const deletedOptions = ref({})
const tab = ref(null)
const totalActiveStudies = ref(0)
const totalDeletedStudies = ref(0)
const savedFilters = ref('')

watch(tab, (newValue) => {
  router.push({
    name: 'SelectOrAddStudy',
    params: { tab: newValue },
  })
  const name =
    newValue === 'active'
      ? t('SelectOrAddStudyTable.tab1_title')
      : t('SelectOrAddStudyTable.tab2_title')
  appStore.addBreadcrumbsLevel(name, undefined, 2, true)
})

watch(activeOptions, () => {
  fetchActiveStudies()
})
watch(deletedOptions, () => {
  fetchDeletedStudies()
})

function fetchActiveStudies(filters, options, filtersUpdated) {
  if (filters) {
    savedFilters.value = filters
  }
  const params = filteringParameters.prepareParameters(
    options,
    savedFilters.value,
    filtersUpdated
  )
  params.sort_by = { 'current_metadata.identification_metadata.study_id': true }
  api.get(params).then((resp) => {
    activeStudies.value = resp.data.items
    totalActiveStudies.value = resp.data.total
  })
}

function fetchDeletedStudies(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  params.deleted = true
  api.get(params).then((resp) => {
    deletedStudies.value = resp.data.items
    totalDeletedStudies.value = resp.data.total
  })
}
function initialSortByDate() {
  activeOptions.value.sortBy = [
    'current_metadata.version_metadata.version_timestamp',
  ]
  activeOptions.value.sortDesc = [true]
}

studiesManageStore.fetchProjects()
tab.value = route.params.tab || 'active'
initialSortByDate()
</script>
