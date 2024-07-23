<template>
  <NNTable
    key="objectiveTable"
    :headers="headers"
    :items="studiesObjectivesStore.studyObjectives"
    item-value="study_objective_uid"
    :column-data-resource="`studies/${studiesGeneralStore.selectedStudy.uid}/study-objectives`"
    export-object-label="StudyObjectives"
    :export-data-url="exportDataUrl"
    :items-length="studiesObjectivesStore.total"
    :history-data-fetcher="fetchObjectivesHistory"
    :history-title="$t('StudyObjectivesTable.global_history_title')"
    :history-html-fields="historyHtmlFields"
    @filter="fetchObjectives"
  >
    <template #actions>
      <v-btn
        data-cy="add-study-objective"
        size="small"
        color="primary"
        :title="$t('StudyObjectiveForm.add_title')"
        :disabled="
          !accessGuard.checkPermission($roles.STUDY_WRITE) ||
          studiesGeneralStore.selectedStudyVersion !== null
        "
        icon="mdi-plus"
        @click.stop="showForm = true"
      />
    </template>
    <template #[`item.name`]="{ item }">
      <NNParameterHighlighter
        v-if="item.objective_template"
        :name="item.objective_template.name"
        default-color="orange"
      />
      <NNParameterHighlighter
        v-else
        :name="item.objective.name"
        :show-prefix-and-postfix="false"
      />
    </template>
    <template #[`item.start_date`]="{ item }">
      {{ $filters.date(item.start_date) }}
    </template>
    <template #[`item.actions`]="{ item }">
      <ActionsMenu
        :actions="actions"
        :item="item"
        :badge="actionsMenuBadge(item)"
      />
    </template>
  </NNTable>
  <v-dialog
    v-model="showForm"
    persistent
    fullscreen
    content-class="fullscreen-dialog"
  >
    <ObjectiveForm
      :current-study-objectives="studiesObjectivesStore.studyObjectives"
      :study-objective="selectedObjective"
      class="fullscreen-dialog"
      @close="closeForm"
      @added="fetchObjectives"
    />
  </v-dialog>
  <ObjectiveEditForm
    :open="showEditForm"
    :study-objective="selectedObjective"
    @close="closeEditForm"
    @updated="fetchObjectives"
  />
  <v-dialog
    v-model="showHistory"
    persistent
    :fullscreen="$globals.historyDialogFullscreen"
    @keydown.esc="closeHistory"
  >
    <HistoryTable
      :title="studyObjectiveHistoryTitle"
      :headers="headers"
      :items="objectiveHistoryItems"
      :html-fields="historyHtmlFields"
      @close="closeHistory"
    />
  </v-dialog>
  <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
  <SelectionOrderUpdateForm
    v-if="selectedObjective"
    ref="orderForm"
    :initial-value="selectedObjective.order"
    :open="showOrderForm"
    @close="closeOrderForm"
    @submit="submitOrder"
  />
  <v-snackbar v-model="snackbar" color="error" location="top">
    <v-icon class="mr-2" icon="mdi-alert-outline" />
    {{ $t('StudyObjectivesTable.sort_help_msg') }}
  </v-snackbar>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import study from '@/api/study'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import NNParameterHighlighter from '@/components/tools/NNParameterHighlighter.vue'
import NNTable from '@/components/tools/NNTable.vue'
import ObjectiveEditForm from '@/components/studies/ObjectiveEditForm.vue'
import ObjectiveForm from '@/components/studies/ObjectiveForm.vue'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import SelectionOrderUpdateForm from '@/components/studies/SelectionOrderUpdateForm.vue'
import statuses from '@/constants/statuses'
import filteringParameters from '@/utils/filteringParameters'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useStudiesObjectivesStore } from '@/stores/studies-objectives'
import { computed, inject, onMounted, ref, watch } from 'vue'

const { t } = useI18n()
const eventBusEmit = inject('eventBusEmit')
const roles = inject('roles')
const emit = defineEmits(['updated'])
const studiesGeneralStore = useStudiesGeneralStore()
const studiesObjectivesStore = useStudiesObjectivesStore()
const accessGuard = useAccessGuard()

const actions = [
  {
    label: t('StudyObjectivesTable.update_version_retired_tooltip'),
    icon: 'mdi-alert-outline',
    iconColor: 'orange',
    condition: (item) =>
      isLatestRetired(item) && !studiesGeneralStore.selectedStudyVersion,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('StudyObjectivesTable.update_version_tooltip'),
    icon: 'mdi-bell-ring-outline',
    iconColorFunc: objectiveUpdateAborted,
    condition: (item) =>
      needUpdate(item) && !studiesGeneralStore.selectedStudyVersion,
    click: updateVersion,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('_global.edit'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    condition: () => !studiesGeneralStore.selectedStudyVersion,
    click: editObjective,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('_global.change_order'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    condition: () => !studiesGeneralStore.selectedStudyVersion,
    click: changeObjectiveOrder,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('_global.delete'),
    icon: 'mdi-delete-outline',
    iconColor: 'error',
    condition: () => !studiesGeneralStore.selectedStudyVersion,
    click: deleteObjective,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('_global.history'),
    icon: 'mdi-history',
    click: openHistory,
  },
]
const headers = [
  { title: '', key: 'actions', width: '5%' },
  { title: t('StudyObjectivesTable.order'), key: 'order', width: '3%' },
  {
    title: t('StudyObjectivesTable.objective_level'),
    key: 'objective_level.sponsor_preferred_name',
  },
  { title: t('_global.objective'), key: 'name', width: '30%' },
  { title: t('StudyObjectivesTable.endpoint_count'), key: 'endpoint_count' },
  { title: t('_global.modified'), key: 'start_date' },
  { title: t('_global.modified_by'), key: 'user_initials' },
]
const historyHtmlFields = ['objective.name']

const objectiveHistoryItems = ref([])
const selectedObjective = ref(null)
const selectedStudyObjective = ref(null)
const showEditForm = ref(false)
const showForm = ref(false)
const showOrderForm = ref(false)
const snackbar = ref(false)
const showHistory = ref(false)
const abortConfirm = ref(false)
const confirm = ref()

const exportDataUrl = computed(() => {
  return `studies/${studiesGeneralStore.selectedStudy.uid}/study-objectives`
})
const studyObjectiveHistoryTitle = computed(() => {
  if (selectedStudyObjective.value) {
    return t('StudyObjectivesTable.study_objective_history_title', {
      studyObjectiveUid: selectedStudyObjective.value.study_objective_uid,
    })
  }
  return ''
})

watch(
  () => studiesObjectivesStore.studyObjectives,
  (value) => {
    if (value) {
      emit('updated')
    }
  }
)

onMounted(() => {
  studiesGeneralStore.fetchObjectiveLevels()
})

function fetchObjectives(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  params.studyUid = studiesGeneralStore.selectedStudy.uid
  studiesObjectivesStore.fetchStudyObjectives(params)
}

async function fetchObjectivesHistory() {
  const resp = await study.getStudyObjectivesAuditTrail(
    studiesGeneralStore.selectedStudy.uid
  )
  return resp.data
}

function needUpdate(item) {
  if (item.latest_objective) {
    if (!isLatestRetired(item)) {
      return item.objective.version !== item.latest_objective.version
    }
  }
  return false
}

function actionsMenuBadge(item) {
  if (needUpdate(item) && !studiesGeneralStore.selectedStudyVersion) {
    return {
      color: item.accepted_version ? 'lightgray' : 'error',
      icon: 'mdi-bell-outline',
    }
  }
  if (
    !item.objective &&
    item.objective_template.parameters.length > 0 &&
    !studiesGeneralStore.selectedStudyVersion
  ) {
    return {
      color: 'error',
      icon: 'mdi-exclamation',
    }
  }
  return null
}

function objectiveUpdateAborted(item) {
  return item.accepted_version ? '' : 'error'
}

function isLatestRetired(item) {
  if (item.latest_objective) {
    return item.latest_objective.status === statuses.RETIRED
  }
  return false
}

async function updateVersion(item) {
  const options = {
    type: 'warning',
    width: 1000,
    cancelLabel: t('StudyObjectivesTable.keep_old_version'),
    agreeLabel: t('StudyObjectivesTable.use_new_version'),
  }
  const message =
    t('StudyObjectivesTable.update_version_alert') +
    '</br>' +
    t('StudyObjectivesTable.previous_version') +
    item.objective.name +
    ' ' +
    t('StudyObjectivesTable.new_version') +
    ' ' +
    item.latest_objective.name

  if (await confirm.value.open(message, options)) {
    const args = {
      studyUid: item.study_uid,
      studyObjectiveUid: item.study_objective_uid,
    }
    studiesObjectivesStore
      .updateStudyObjectiveLatestVersion(args)
      .then(() => {
        eventBusEmit('notification', {
          msg: t('StudyObjectivesTable.update_version_successful'),
        })
      })
      .catch((error) => {
        eventBusEmit('notification', {
          type: 'error',
          msg: error.response.data.message,
        })
      })
  } else {
    abortConfirm.value = true
    const args = {
      studyUid: item.study_uid,
      studyObjectiveUid: item.study_objective_uid,
    }
    studiesObjectivesStore
      .updateStudyObjectiveAcceptVersion(args)
      .then(() => {})
      .catch((error) => {
        eventBusEmit('notification', {
          type: 'error',
          msg: error.response.data.message,
        })
      })
  }
}

function closeForm() {
  showForm.value = false
  selectedObjective.value = null
}

function closeEditForm() {
  showEditForm.value = false
  selectedObjective.value = null
}

async function deleteObjective(studyObjective) {
  const options = { type: 'warning' }
  const objective = studyObjective.objective
    ? studyObjective.objective.name_plain
    : '(unnamed)'

  if (
    await confirm.value.open(
      t('StudyObjectivesTable.confirm_delete', { objective }),
      options
    )
  ) {
    studiesObjectivesStore
      .deleteStudyObjective({
        studyUid: studiesGeneralStore.selectedStudy.uid,
        studyObjectiveUid: studyObjective.study_objective_uid,
      })
      .then(() => {
        fetchObjectives()
        eventBusEmit('notification', {
          msg: t('StudyObjectivesTable.delete_objective_success'),
        })
      })
  }
}

function editObjective(objective) {
  selectedObjective.value = objective
  showEditForm.value = true
}

function closeHistory() {
  selectedStudyObjective.value = null
  showHistory.value = false
}

async function openHistory(studyObjective) {
  selectedStudyObjective.value = studyObjective
  const resp = await study.getStudyObjectiveAuditTrail(
    studiesGeneralStore.selectedStudy.uid,
    studyObjective.study_objective_uid
  )
  objectiveHistoryItems.value = resp.data
  showHistory.value = true
}

function submitOrder(value) {
  study
    .updateStudyObjectiveOrder(
      selectedObjective.value.study_uid,
      selectedObjective.value.study_objective_uid,
      value
    )
    .then(() => {
      fetchObjectives()
      closeOrderForm()
      eventBusEmit('notification', { msg: t('_global.order_updated') })
    })
}

function changeObjectiveOrder(objective) {
  selectedObjective.value = objective
  showOrderForm.value = true
}

function closeOrderForm() {
  showOrderForm.value = false
}
</script>
