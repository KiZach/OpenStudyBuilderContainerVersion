<template>
  <NNTable
    :headers="headers"
    :items="criteria"
    item-value="study_criteria_uid"
    hide-fixed-headers-switch
    :export-data-url="exportDataUrl"
    :export-data-url-params="exportDataUrlParams"
    export-object-label="StudyCriteria"
    :history-data-fetcher="fetchAllCriteriaHistory"
    :history-title="$t('EligibilityCriteriaTable.global_history_title')"
    :history-html-fields="historyHtmlFields"
    :column-data-resource="`studies/${studiesGeneralStore.selectedStudy.uid}/study-criteria`"
    :items-length="total"
    :filters-modify-function="addTypeFilterToHeader"
    @filter="getStudyCriteria"
  >
    <template #actions>
      <v-btn
        data-cy="add-study-criteria"
        size="small"
        color="primary"
        :title="$t('EligibilityCriteriaTable.add_criteria')"
        :disabled="
          !accessGuard.checkPermission($roles.STUDY_WRITE) ||
          studiesGeneralStore.selectedStudyVersion !== null
        "
        icon="mdi-plus"
        @click.stop="addCriteria"
      />
    </template>
    <template #[`item.order`]="{ item }">
      {{ item.order }}
      <template  v-if="item.criteria">
        <v-tooltip
          v-if="item.criteria.name_plain.length > 200"
          location="bottom"
        >
          <template #activator="{ props }">
            <v-badge v-bind="props" color="warning" icon="mdi-exclamation" bordered inline />
          </template>
          <span>{{ $t('EligibilityCriteriaTable.criteria_length_warning') }}</span>
        </v-tooltip>
      </template>
    </template>
    <template #[`item.criteria.name`]="{ item }">
      <template v-if="item.criteria_template">
        <NNParameterHighlighter
          :name="item.criteria_template.name"
          default-color="orange"
        />
      </template>
      <template v-else>
        <NNParameterHighlighter
          :name="item.criteria.name"
          :show-prefix-and-postfix="false"
        />
      </template>
    </template>
    <template #[`item.criteria.criteria_template.guidance_text`]="{ item }">
      <template v-if="item.criteria_template">
        <span v-html="item.criteria_template.guidance_text" />
      </template>
      <template v-else>
        <span v-html="item.criteria.criteria_template.guidance_text" />
      </template>
    </template>
    <template #[`item.key_criteria`]="{ item }">
      <v-checkbox
        v-model="item.key_criteria"
        color="primary"
        @update:model-value="updateKeyCriteria($event, item.study_criteria_uid)"
      />
    </template>
    <template #[`item.start_date`]="{ item }">
      {{ $filters.date(item.start_date) }}
    </template>
    <template #[`item.actions`]="{ item }">
      <ActionsMenu
        :key="item.study_criteria_uid"
        :actions="filterEditAction(item)"
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
    <EligibilityCriteriaForm
      :criteria-type="criteriaType"
      class="fullscreen-dialog"
      @close="closeForm"
      @added="getStudyCriteria"
    />
  </v-dialog>
  <EligibilityCriteriaEditForm
    :open="showEditForm"
    :study-criteria="selectedStudyCriteria"
    @close="closeEditForm"
    @updated="getStudyCriteria"
  />
  <v-dialog
    v-model="showHistory"
    persistent
    :fullscreen="$globals.historyDialogFullscreen"
    @keydown.esc="closeHistory"
  >
    <HistoryTable
      :title="studyCriteriaHistoryTitle"
      :headers="headers"
      :items="criteriaHistoryItems"
      :html-fields="historyHtmlFields"
      @close="closeHistory"
    />
  </v-dialog>
  <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
  <SelectionOrderUpdateForm
    v-if="selectedStudyCriteria"
    ref="orderForm"
    :initial-value="selectedStudyCriteria.order"
    :open="showOrderForm"
    @close="closeOrderForm"
    @submit="submitOrder"
  />
</template>

<script setup>
import { computed, inject, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import EligibilityCriteriaEditForm from './EligibilityCriteriaEditForm.vue'
import EligibilityCriteriaForm from './EligibilityCriteriaForm.vue'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import NNParameterHighlighter from '@/components/tools/NNParameterHighlighter.vue'
import SelectionOrderUpdateForm from '@/components/studies/SelectionOrderUpdateForm.vue'
import NNTable from '@/components/tools/NNTable.vue'
import study from '@/api/study'
import filteringParameters from '@/utils/filteringParameters'
import statuses from '@/constants/statuses'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesGeneralStore } from '@/stores/studies-general'

const eventBusEmit = inject('eventBusEmit')
const roles = inject('roles')
const props = defineProps({
  criteriaType: {
    type: Object,
    default: undefined,
  },
})
const accessGuard = useAccessGuard()
const studiesGeneralStore = useStudiesGeneralStore()
const { t } = useI18n()

const criteria = ref([])
const criteriaHistoryItems = ref([])
const headers = ref([
  { title: '', key: 'actions', width: '5%' },
  { title: '#', key: 'order', width: '5%' },
  {
    title: props.criteriaType.name.sponsor_preferred_name,
    key: 'criteria.name',
    width: '30%',
  },
  {
    title: t('EligibilityCriteriaTable.guidance_text'),
    key: 'criteria.criteria_template.guidance_text',
    width: '20%',
  },
  { title: t('EligibilityCriteriaTable.key_criteria'), key: 'key_criteria' },
  { title: t('_global.modified'), key: 'start_date' },
  { title: t('_global.modified_by'), key: 'user_initials' },
])
const selectedStudyCriteria = ref(null)
const showEditForm = ref(false)
const showForm = ref(false)
const showHistory = ref(false)
const showOrderForm = ref(false)
const total = ref(0)
const confirm = ref()

const historyHtmlFields = [
  'criteria.name',
  'criteria.criteria_template.guidance_text',
]

const exportDataUrl = computed(() => {
  return `studies/${studiesGeneralStore.selectedStudy.uid}/study-criteria`
})
const exportDataUrlParams = computed(() => {
  return {
    filters: JSON.stringify({
      'criteria_type.sponsor_preferred_name_sentence_case': {
        v: [props.criteriaType.name.sponsor_preferred_name_sentence_case],
      },
    }),
  }
})
const studyCriteriaHistoryTitle = computed(() => {
  if (selectedStudyCriteria.value) {
    return t('EligibilityCriteriaTable.study_criteria_history_title', {
      studyCriteriaUid: selectedStudyCriteria.value.study_criteria_uid,
    })
  }
  return ''
})

onMounted(() => {
  studiesGeneralStore.fetchTrialPhases()
})

async function fetchAllCriteriaHistory() {
  const resp = await study.getStudyCriteriaAllAuditTrail(
    studiesGeneralStore.selectedStudy.uid,
    props.criteriaType.term_uid
  )
  const auditTrailData = transformItems(resp.data)
  auditTrailData.forEach((item) => {
    if (!item.criteria) {
      item.criteria = item.criteria_template
    }
  })
  return auditTrailData
}

function actionsMenuBadge(item) {
  if (needUpdate(item)) {
    return {
      color: item.accepted_version ? 'lightgray' : 'error',
      icon: 'mdi-bell-outline',
    }
  }
  if (!item.criteria && item.criteria_template.parameters.length > 0) {
    return {
      color: 'error',
      icon: 'mdi-exclamation',
    }
  }
  return undefined
}

function filterEditAction(item) {
  if (
    (item.criteria && item.criteria.parameter_terms.length > 0) ||
    (item.criteria_template && item.criteria_template.parameters.length > 0)
  ) {
    return actions.value
  } else {
    return actions.value.slice(1)
  }
}

function addCriteria() {
  showForm.value = true
}

function closeEditForm() {
  showEditForm.value = false
}

function closeForm() {
  showForm.value = false
}

function closeHistory() {
  selectedStudyCriteria.value = null
  showHistory.value = false
}

async function openHistory(studyCriteria) {
  selectedStudyCriteria.value = studyCriteria
  const resp = await study.getStudyCriteriaAuditTrail(
    studiesGeneralStore.selectedStudy.uid,
    studyCriteria.study_criteria_uid
  )
  criteriaHistoryItems.value = transformItems(resp.data)
  criteriaHistoryItems.value.forEach((item) => {
    if (!item.criteria) {
      item.criteria = item.criteria_template
    }
  })
  showHistory.value = true
}

function editStudyCriteria(studyCriteria) {
  showEditForm.value = true
  selectedStudyCriteria.value = studyCriteria
}

async function deleteStudyCriteria(studyCriteria) {
  const options = { type: 'warning' }
  let criterion = studyCriteria.criteria_template
    ? studyCriteria.criteria_template.name
    : studyCriteria.criteria.name

  criterion = criterion.replaceAll(/\[|\]/g, '')
  if (
    await confirm.value.open(
      t('EligibilityCriteriaTable.confirm_delete', { criterion }),
      options
    )
  ) {
    await study.deleteStudyCriteria(
      studiesGeneralStore.selectedStudy.uid,
      studyCriteria.study_criteria_uid
    )
    getStudyCriteria()
    eventBusEmit('notification', {
      msg: t('EligibilityCriteriaTable.delete_success'),
    })
  }
}

function getStudyCriteria(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  study
    .getStudyCriteriaWithType(
      studiesGeneralStore.selectedStudy.uid,
      props.criteriaType,
      params
    )
    .then((resp) => {
      criteria.value = transformItems(resp.data.items)
      total.value = resp.data.total
    })
}

function submitOrder(value) {
  study
    .updateStudyCriteriaOrder(
      selectedStudyCriteria.value.study_uid,
      selectedStudyCriteria.value.study_criteria_uid,
      value
    )
    .then(() => {
      getStudyCriteria()
      closeOrderForm()
      eventBusEmit('notification', { msg: t('_global.order_updated') })
    })
}
function changeCriteriaOrder(criteria) {
  selectedStudyCriteria.value = criteria
  showOrderForm.value = true
}

function closeOrderForm() {
  showOrderForm.value = false
}

function updateKeyCriteria(value, studyCriteriaUid) {
  study
    .updateStudyCriteriaKeyCriteria(
      studiesGeneralStore.selectedStudy.uid,
      studyCriteriaUid,
      value
    )
    .then(() => {
      getStudyCriteria()
    })
}

function transformItems(items) {
  const result = []
  for (const item of items) {
    const newItem = { ...item }
    if (newItem.criteria_template) {
      newItem.name = item.criteria_template.name
      newItem.guidance_text = item.criteria_template.guidance_text
    } else {
      newItem.name = item.criteria.name
      newItem.guidance_text = item.criteria.guidance_text
    }
    result.push(newItem)
  }
  return result
}

function needUpdate(item) {
  if (item.latest_criteria) {
    if (!isLatestRetired(item)) {
      return item.criteria.version !== item.latest_criteria.version
    }
  }
  return false
}

function criteriaUpdateAborted(item) {
  return item.accepted_version ? '' : 'error'
}

function isLatestRetired(item) {
  if (item.latest_criteria) {
    return item.latest_criteria.status === statuses.RETIRED
  }
  return false
}

async function updateVersion(item) {
  const options = {
    type: 'warning',
    width: 1000,
    cancelLabel: t('EligibilityCriteriaTable.keep_old_version'),
    agreeLabel: t('EligibilityCriteriaTable.use_new_version'),
  }
  const message =
    t('EligibilityCriteriaTable.update_version_alert') +
    '<br>' +
    t('EligibilityCriteriaTable.previous_version') +
    ' ' +
    item.criteria.name_plain +
    '<br>' +
    t('EligibilityCriteriaTable.new_version') +
    ' ' +
    item.latest_criteria.name_plain

  if (await confirm.value.open(message, options)) {
    study
      .updateStudyCriteriaLatestVersion(item.study_uid, item.study_criteria_uid)
      .then(() => {
        eventBusEmit('notification', {
          msg: t('EligibilityCriteriaTable.update_version_successful'),
        })
        getStudyCriteria()
      })
      .catch((error) => {
        eventBusEmit('notification', {
          type: 'error',
          msg: error.response.data.message,
        })
      })
  } else {
    study
      .updateStudyCriteriaAcceptVersion(item.study_uid, item.study_criteria_uid)
      .then(() => {
        getStudyCriteria()
      })
      .catch((error) => {
        eventBusEmit('notification', {
          type: 'error',
          msg: error.response.data.message,
        })
      })
  }
}

function addTypeFilterToHeader(jsonFilter, params) {
  if (params.field_name === 'criteria.name') {
    jsonFilter['criteria_type.sponsor_preferred_name_sentence_case'] = {
      v: [props.criteriaType.name.sponsor_preferred_name_sentence_case],
    }
  }
  return {
    jsonFilter,
    params,
  }
}

const actions = ref([
  {
    label: t('EligibilityCriteriaTable.update_version_retired_tooltip'),
    icon: 'mdi-alert-outline',
    iconColor: 'orange',
    condition: (item) => isLatestRetired(item),
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('EligibilityCriteriaTable.update_version_tooltip'),
    icon: 'mdi-bell-ring-outline',
    iconColorFunc: criteriaUpdateAborted,
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
    click: editStudyCriteria,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('_global.change_order'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    condition: () => !studiesGeneralStore.selectedStudyVersion,
    click: changeCriteriaOrder,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('_global.delete'),
    icon: 'mdi-delete-outline',
    iconColor: 'error',
    condition: () => !studiesGeneralStore.selectedStudyVersion,
    click: deleteStudyCriteria,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('_global.history'),
    icon: 'mdi-history',
    click: openHistory,
  },
])
</script>
