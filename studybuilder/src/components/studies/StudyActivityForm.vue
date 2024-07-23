<template>
  <HorizontalStepperForm
    ref="stepper"
    :title="$t('StudyActivityForm.add_title')"
    :steps="steps"
    :form-observer-getter="getObserver"
    :help-text="$t('_help.StudyActivityTable.general')"
    :reset-loading="resetLoading"
    @close="cancel"
    @save="submit"
  >
    <template #[`step.creationMode`]>
      <v-radio-group v-model="creationMode" color="primary">
        <v-radio
          :label="$t('StudyActivityForm.select_from_studies')"
          value="selectFromStudies"
          data-cy="select-from-studies"
        />
        <v-radio
          :label="$t('StudyActivityForm.select_from_library')"
          value="selectFromLibrary"
          data-cy="select-from-library"
        />
        <v-radio
          :label="$t('StudyActivityForm.create_placeholder_for_activity')"
          value="createPlaceholder"
          data-cy="create-placeholder"
        />
      </v-radio-group>
    </template>
    <template #[`step.selectStudies`]>
      <v-form ref="selectStudiesForm">
        <v-autocomplete
          v-model="selectedStudy"
          :label="$t('StudySelectionTable.studies')"
          data-cy="select-study-for-activity"
          :items="studies"
          :rules="[formRules.required]"
          item-title="current_metadata.identification_metadata.study_id"
          clearable
          return-object
        />
      </v-form>
    </template>
    <template #[`step.selectFlowchartGroup`]>
      <v-form ref="flowchartGroupForm">
        <v-row>
          <v-col cols="4">
            <v-autocomplete
              v-model="currentFlowchartGroup"
              :label="$t('StudyActivityForm.flowchart_group')"
              data-cy="flowchart-group"
              :items="flowchartGroups"
              item-title="name.sponsor_preferred_name"
              return-object
              :rules="[formRules.required]"
              :hint="$t('_help.StudyActivityForm.flowchart_group')"
              persistent-hint
              clearable
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
    <template #[`step.selectFromStudies`]>
      <v-data-table
        key="fromStudiesSelection"
        :headers="selectionFromStudiesHeaders"
        :items="selectedActivities"
      >
        <template #[`item.name`]="{ item }">
          {{ item.activity.name }}
        </template>
        <template #[`item.actions`]="{ item }">
          <v-btn
            icon="mdi-delete-outline"
            color="red"
            variant="text"
            @click="unselectActivity(item)"
          />
        </template>
      </v-data-table>
    </template>
    <template #[`step.selectFromStudies.after`]>
      <div class="mt-4 mx-4 text-subtitle-1 text-grey font-italic">
        {{ $t('StudyActivityForm.copy_activity_instructions') }}
      </div>
      <v-col cols="12">
        <NNTable
          v-if="selectedStudy"
          ref="selectionTable"
          :headers="studyActivityHeaders"
          :items="activities"
          hide-default-switches
          hide-actions-menu
          show-filter-bar-by-default
          :items-per-page="15"
          elevation="0"
          :items-length="activitiesTotal"
          :column-data-resource="`studies/${selectedStudy.uid}/study-activities`"
          :filters-modify-function="modifyFilters"
          @filter="getActivities"
        >
          <template #[`header.actions`]>
            <div class="row">
              <v-btn
                icon="mdi-content-copy"
                color="primary"
                :title="$t('StudyActivityForm.copy_all_activities')"
                variant="text"
                @click="selectAllStudyActivities()"
              />
            </div>
          </template>
          <template #[`item.actions`]="{ item }">
            <v-btn
              icon="mdi-content-copy"
              :color="getCopyButtonColor(item)"
              :disabled="
                isStudyActivitySelected(item) || isStudyActivityRequested(item)
              "
              data-cy="copy-activity"
              :title="$t('StudyActivityForm.copy_activity')"
              variant="text"
              @click="selectStudyActivity(item)"
            />
          </template>
          <template #[`item.activity.is_data_collected`]="{ item }">
            <div v-if="item.activity">
              {{ $filters.yesno(item.activity.is_data_collected) }}
            </div>
          </template>
        </NNTable>
      </v-col>
    </template>
    <template #[`step.selectFromLibrary`]>
      <v-data-table
        key="fromLibrarySelection"
        :headers="selectionFromLibraryHeaders"
        :items="selectedActivities"
      >
        <template #[`item.actions`]="{ item }">
          <v-btn
            icon="mdi-delete-outline"
            color="red"
            variant="text"
            @click="unselectActivity(item)"
          />
        </template>
      </v-data-table>
    </template>
    <template #[`step.selectFromLibrary.after`]>
      <div class="mt-4 mx-4 text-subtitle-1 text-grey font-italic">
        {{ $t('StudyActivityForm.copy_activity_instructions') }}
      </div>
      <v-col cols="12">
        <NNTable
          key="activityTable"
          :headers="activityHeaders"
          :items="activities"
          hide-default-switches
          hide-actions-menu
          show-filter-bar-by-default
          :items-per-page="15"
          elevation="0"
          :items-length="activitiesTotal"
          :initial-filters="initialFilters"
          column-data-resource="concepts/activities/activities"
          :filters-modify-function="modifyFilters"
          @filter="getActivities"
        >
          <template #[`item.actions`]="{ item }">
            <v-btn
              icon="mdi-content-copy"
              :color="getCopyButtonColor(item)"
              :disabled="
                isActivitySelected(item) ||
                isActivityNotFinal(item) ||
                isActivityRequested(item)
              "
              data-cy="copy-activity"
              :title="$t('StudyActivityForm.copy_activity')"
              variant="text"
              @click="selectActivity(item)"
            />
          </template>
          <template #[`header.actions`]>
            <div class="row">
              <v-btn
                icon="mdi-content-copy"
                color="primary"
                :title="$t('StudyActivityForm.copy_all_activities')"
                variant="text"
                @click="selectAllActivities()"
              />
            </div>
          </template>
          <template #[`item.is_data_collected`]="{ item }">
            {{ $filters.yesno(item.is_data_collected) }}
          </template>
        </NNTable>
      </v-col>
    </template>
    <template #[`step.createPlaceholder`]>
      <v-form ref="createPlaceholderForm">
        <v-row>
          <v-col cols="5">
            <v-autocomplete
              v-model="form.activity_groupings[0].activity_group_uid"
              :label="$t('ActivityForms.activity_group')"
              data-cy="activity-group"
              :items="groups"
              item-title="name"
              item-value="uid"
              density="compact"
              clearable
            />
            <v-autocomplete
              v-model="form.activity_groupings[0].activity_subgroup_uid"
              :label="$t('ActivityForms.activity_subgroup')"
              data-cy="activity-subgroup"
              :items="filteredSubGroups"
              item-title="name"
              item-value="uid"
              density="compact"
              clearable
              :disabled="
                form.activity_groupings[0].activity_group_uid ? false : true
              "
            />
            <v-text-field
              v-model="form.name"
              :label="$t('ActivityFormsRequested.name')"
              data-cy="instance-name"
              density="compact"
              clearable
              :rules="[formRules.required]"
              @input="getActivities"
            />
            <v-textarea
              v-model="form.request_rationale"
              :label="$t('ActivityFormsRequested.rationale_for_request')"
              data-cy="activity-rationale"
              density="compact"
              clearable
              auto-grow
              rows="1"
              :rules="[formRules.required]"
            />
            <v-row>
              <v-checkbox
                v-model="form.is_data_collected"
                class="mt-2"
                :label="$t('ActivityForms.is_data_collected')"
              />
              <v-spacer />
              <v-switch
                v-model="form.is_request_final"
                :label="$t('ActivityForms.submit_request')"
                hide-details
                color="primary"
              />
            </v-row>
          </v-col>
          <v-col cols="7">
            <v-data-table
              :headers="activityHeaders"
              :items="activities"
              :items-length="activitiesTotal"
              :items-per-page="5"
              @pagination="getActivities()"
            >
              <template #[`item.actions`]="{ item }">
                <v-btn
                  icon="mdi-content-copy"
                  :color="getCopyButtonColor(item)"
                  :disabled="
                    isActivitySelected(item) ||
                    isActivityNotFinal(item) ||
                    isActivityRequested(item)
                  "
                  data-cy="copy-activity"
                  :title="$t('StudyActivityForm.copy_activity')"
                  variant="text"
                  @click="selectActivityFromPlaceholder(item)"
                />
              </template>
            </v-data-table>
          </v-col>
        </v-row>
      </v-form>
    </template>
  </HorizontalStepperForm>
  <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
</template>

<script setup>
import { computed, inject, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import activitiesApi from '@/api/activities'
import statuses from '@/constants/statuses'
import study from '@/api/study'
import terms from '@/api/controlledTerminology/terms'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm.vue'
import NNTable from '@/components/tools/NNTable.vue'
import _isEmpty from 'lodash/isEmpty'
import _isEqual from 'lodash/isEqual'
import libConstants from '@/constants/libraries'
import { useStudiesGeneralStore } from '@/stores/studies-general'

const eventBusEmit = inject('eventBusEmit')
const formRules = inject('formRules')
const { t } = useI18n()
const emit = defineEmits(['close', 'added'])
const studiesGeneralStore = useStudiesGeneralStore()

const creationMode = ref('selectFromLibrary')
const activities = ref([])
const activitiesTotal = ref(0)
const currentFlowchartGroup = ref(null)
const flowchartGroups = ref([])
const selectedStudy = ref(null)
const steps = ref([])
const studies = ref([])
const selectedActivities = ref([])
const studyActivities = ref([])
const savedFilters = ref('')
const form = ref({
  name: '',
  activity_groupings: [{}],
  is_data_collected: true,
})
const groups = ref([])
const subgroups = ref([])
const resetLoading = ref(0)
const confirm = ref()
const stepper = ref()
const flowchartGroupForm = ref()
const selectStudiesForm = ref()
const createPlaceholderForm = ref()
const selectionTable = ref()

const activityHeaders = [
  { title: '', key: 'actions', width: '5%' },
  { title: t('_global.library'), key: 'library_name', noFilter: true },
  {
    title: t('StudyActivity.activity_group'),
    key: 'activity_group.name',
    externalFilterSource: 'concepts/activities/activity-groups$name',
    exludeFromHeader: ['is_data_collected'],
  },
  {
    title: t('StudyActivity.activity_sub_group'),
    key: 'activity_subgroup.name',
    externalFilterSource: 'concepts/activities/activity-sub-groups$name',
    exludeFromHeader: ['is_data_collected'],
  },
  { title: t('StudyActivity.activity'), key: 'name' },
  { title: t('StudyActivity.data_collection'), key: 'is_data_collected' },
  { title: t('_global.status'), key: 'status' },
]
const selectFromStudiesSteps = [
  { name: 'creationMode', title: t('StudyActivityForm.creation_mode_title') },
  { name: 'selectStudies', title: t('StudyActivityForm.select_studies') },
  {
    name: 'selectFromStudies',
    title: t('StudyActivityForm.select_from_studies_title'),
  },
]
const selectFromLibrarySteps = [
  { name: 'creationMode', title: t('StudyActivityForm.creation_mode_title') },
  {
    name: 'selectFlowchartGroup',
    title: t('StudyActivityForm.flowchart_group_title'),
  },
  {
    name: 'selectFromLibrary',
    title: t('StudyActivityForm.select_from_library_title'),
  },
]
const createPlaceholderSteps = [
  { name: 'creationMode', title: t('StudyActivityForm.creation_mode_title') },
  {
    name: 'selectFlowchartGroup',
    title: t('StudyActivityForm.flowchart_group_title'),
  },
  {
    name: 'createPlaceholder',
    title: t('StudyActivityForm.create_placeholder'),
    belowDisplay: true,
  },
]
const selectionFromLibraryHeaders = [
  { title: '', key: 'actions', width: '5%' },
  { title: t('_global.library'), key: 'library_name' },
  { title: t('StudyActivity.activity_group'), key: 'activity_group.name' },
  {
    title: t('StudyActivity.activity_sub_group'),
    key: 'activity_subgroup.name',
  },
  { title: t('StudyActivity.activity'), key: 'name' },
]
const selectionFromStudiesHeaders = [
  { title: '', key: 'actions', width: '5%' },
  { title: t('_global.library'), key: 'activity.library_name' },
  {
    title: t('StudyActivityForm.flowchart_group'),
    key: 'study_soa_group.soa_group_name',
  },
  {
    title: t('StudyActivity.activity_group'),
    key: 'study_activity_group.activity_group_name',
  },
  {
    title: t('StudyActivity.activity_sub_group'),
    key: 'study_activity_subgroup.activity_subgroup_name',
  },
  { title: t('StudyActivity.activity'), key: 'name' },
]
const studyActivityHeaders = [
  { title: '', key: 'actions', width: '5%' },
  { title: t('StudyActivityForm.study_id'), key: 'study_id', noFilter: true },
  { title: t('_global.library'), key: 'activity.library_name', noFilter: true },
  {
    title: t('StudyActivityForm.flowchart_group'),
    key: 'study_soa_group.soa_group_name',
  },
  {
    title: t('StudyActivity.activity_group'),
    key: 'study_activity_group.activity_group_name',
    disableColumnFilters: true,
  },
  {
    title: t('StudyActivity.activity_sub_group'),
    key: 'study_activity_subgroup.activity_subgroup_name',
    disableColumnFilters: true,
  },
  { title: t('StudyActivity.activity'), key: 'activity.name' },
  {
    title: t('StudyActivity.data_collection'),
    key: 'activity.is_data_collected',
  },
]
const initialFilters = { status: [statuses.FINAL] }

const filteredSubGroups = computed(() => {
  if (!form.value.activity_groupings[0].activity_group_uid) {
    return []
  }
  return subgroups.value.filter(
    (el) =>
      el.activity_groups.find(
        (o) => o.uid === form.value.activity_groupings[0].activity_group_uid
      ) !== undefined
  )
})

watch(filteredSubGroups, (value) => {
  if (value.length === 1) {
    form.value.activity_groupings[0].activity_subgroup_uid = value[0].uid
  } else {
    form.value.activity_groupings[0].activity_subgroup_uid = null
  }
})
watch(creationMode, (value) => {
  if (value === 'selectFromStudies') {
    steps.value = selectFromStudiesSteps
  } else if (value === 'selectFromLibrary') {
    steps.value = selectFromLibrarySteps
  } else {
    steps.value = createPlaceholderSteps
  }
  selectedActivities.value = []
})
watch(selectedStudy, () => {
  if (selectionTable.value) {
    selectionTable.value.filterTable()
  }
})

steps.value = selectFromLibrarySteps

onMounted(() => {
  terms.getByCodelist('flowchartGroups').then((resp) => {
    flowchartGroups.value = resp.data.items
  })
  study.get({ has_study_activity: true, page_size: 0 }).then((resp) => {
    studies.value = resp.data.items.filter(
      (study) => study.uid !== studiesGeneralStore.selectedStudy.uid
    )
  })
  getGroups()
  study
    .getStudyActivities(studiesGeneralStore.selectedStudy.uid, { page_size: 0 })
    .then((resp) => {
      studyActivities.value = resp.data.items
    })
})

async function cancel() {
  if (!_isEmpty(selectedActivities.value)) {
    const options = {
      type: 'warning',
      cancelLabel: t('_global.cancel'),
      agreeLabel: t('_global.continue'),
    }
    if (await confirm.value.open(t('_global.cancel_changes'), options)) {
      close()
    }
  } else {
    close()
  }
}

function close() {
  emit('close')
  selectedActivities.value = []
  currentFlowchartGroup.value = null
  creationMode.value = 'selectFromLibrary'
  steps.value = selectFromLibrarySteps
  selectedStudy.value = null
  form.value = {
    name: '',
    activity_groupings: [{}],
  }
  stepper.value.reset()
}

function getObserver(step) {
  if (step === 2) {
    if (creationMode.value === 'selectFromStudies') {
      return selectStudiesForm.value
    } else {
      return flowchartGroupForm.value
    }
  } else if (step === 3) {
    return createPlaceholderForm.value
  }
}

function selectActivityFromPlaceholder(activity) {
  creationMode.value = 'selectFromLibrary'
  if (!currentFlowchartGroup.value) {
    return
  }
  const activityCopy = { ...activity }
  activityCopy.flowchart_group = { ...currentFlowchartGroup.value }
  selectedActivities.value.push(activityCopy)
}

function getActivities(filters, options) {
  if (creationMode.value === 'createPlaceholder') {
    const params = {
      page_number: options && options.page ? options.page : 1,
      page_size: options && options.itemsPerPage ? options.itemsPerPage : 50,
      total_count: true,
      library: libConstants.LIBRARY_SPONSOR,
      filters: `{"*":{"v":["${form.value.name}"]}}`,
    }
    activitiesApi.get(params, 'activities').then((resp) => {
      const items = []
      for (const item of resp.data.items) {
        if (item.activity_groupings.length > 0) {
          for (const grouping of item.activity_groupings) {
            items.push({
              activity_group: {
                name: grouping.activity_group_name,
                uid: grouping.activity_group_uid,
              },
              activity_subgroup: {
                name: grouping.activity_subgroup_name,
                uid: grouping.activity_subgroup_uid,
              },
              item_key:
                item.uid +
                grouping.activity_group_uid +
                grouping.activity_subgroup_uid,
              ...item,
            })
          }
        } else {
          items.push({
            activity_group: { name: '', uid: '' },
            activity_subgroup: { name: '', uid: '' },
            item_key: item.uid,
            ...item,
          })
        }
      }
      activities.value = items
      activitiesTotal.value = resp.data.total
    })
    return
  } else if (creationMode.value === 'selectFromStudies') {
    const params = {
      page_number: options ? options.page : 1,
      page_size: options ? options.itemsPerPage : 15,
      total_count: true,
    }
    if (filters) {
      params.filters = JSON.parse(filters)
    } else {
      params.filters = {}
    }
    params.filters.study_uid = { v: [selectedStudy.value.uid] }
    params.filters['activity.library_name'] = {
      v: [libConstants.LIBRARY_SPONSOR],
    }
    study.getAllStudyActivities(params).then((resp) => {
      const items = resp.data.items
      items.forEach((el) => {
        el.study_id =
          studies.value[
            studies.value.findIndex((study) => study.uid === el.study_uid)
          ].current_metadata.identification_metadata.study_id
      })
      const result = []
      for (const item of items) {
        let grouping = null
        if (item.activity.activity_groupings.length > 0) {
          if (item.study_activity_group && item.study_activity_subgroup) {
            grouping = item.activity.activity_groupings.find(
              (o) =>
                o.activity_group_uid ===
                  item.study_activity_group.activity_group_uid &&
                o.activity_subgroup_uid ===
                  item.study_activity_subgroup.activity_subgroup_uid
            )
          }
        }
        if (grouping) {
          result.push({
            ...item,
            activity: {
              activity_group: {
                name: grouping.activity_group_name,
                uid: grouping.activity_group_uid,
              },
              activity_subgroup: {
                name: grouping.activity_subgroup_name,
                uid: grouping.activity_subgroup_uid,
              },
              ...item.activity,
            },
            item_key:
              item.activity.uid +
              grouping.activity_group_uid +
              grouping.activity_subgroup_uid,
          })
        } else {
          result.push({
            ...item,
            activity: {
              ...item.activity,
              activity_group: { name: '', uid: '' },
              activity_subgroup: { name: '', uid: '' },
            },
            item_key: item.activity.uid,
          })
        }
      }
      activities.value = result
      activitiesTotal.value = resp.data.total
    })
    return
  }
  if (filters !== undefined && !_isEqual(filters, savedFilters.value)) {
    // New filters, also reset current page
    savedFilters.value = filters
  }
  const params = {
    page_number: options ? options.page : 1,
    page_size: options ? options.itemsPerPage : 15,
    library: libConstants.LIBRARY_SPONSOR,
    total_count: true,
  }
  if (savedFilters.value && savedFilters.value !== undefined) {
    const filtersObj = JSON.parse(savedFilters.value)
    filtersObj['is_used_by_legacy_instances'] = {
      v: [false],
      op: 'eq',
    }
    if (filtersObj['activity_group.name']) {
      params.activity_group_names = []
      filtersObj['activity_group.name'].v.forEach((value) => {
        params.activity_group_names.push(value)
      })
      delete filtersObj['activity_group.name']
    }
    if (filtersObj['activity_subgroup.name']) {
      params.activity_subgroup_names = []
      filtersObj['activity_subgroup.name'].v.forEach((value) => {
        params.activity_subgroup_names.push(value)
      })
      delete filtersObj['activity_subgroup.name']
    }
    if (filtersObj.name) {
      params.activity_names = []
      filtersObj.name.v.forEach((value) => {
        params.activity_names.push(value)
      })
      delete filtersObj.name
    }
    if (
      Object.keys(filtersObj).length !== 0 &&
      filtersObj.constructor === Object
    ) {
      params.filters = JSON.stringify(filtersObj)
    }
  }
  activitiesApi.get(params, 'activities').then((resp) => {
    const items = []
    for (const item of resp.data.items) {
      if (item.activity_groupings.length > 0) {
        for (const grouping of item.activity_groupings) {
          items.push({
            activity_group: {
              name: grouping.activity_group_name,
              uid: grouping.activity_group_uid,
            },
            activity_subgroup: {
              name: grouping.activity_subgroup_name,
              uid: grouping.activity_subgroup_uid,
            },
            item_key:
              item.uid +
              grouping.activity_group_uid +
              grouping.activity_subgroup_uid,
            ...item,
          })
        }
      } else {
        items.push({
          activity_group: { name: '', uid: '' },
          activity_subgroup: { name: '', uid: '' },
          item_key: item.uid,
          ...item,
        })
      }
    }
    activities.value = items
    activitiesTotal.value = resp.data.total
  })
}

function modifyFilters(jsonFilter, params) {
  if (jsonFilter['activity_group.name']) {
    params.activity_group_names = []
    jsonFilter['activity_group.name'].v.forEach((value) => {
      params.activity_group_names.push(value)
    })
    delete jsonFilter['activity_group.name']
  }
  if (jsonFilter['activity_subgroup.name']) {
    params.activity_subgroup_names = []
    jsonFilter['activity_subgroup.name'].v.forEach((value) => {
      params.activity_subgroup_names.push(value)
    })
    delete jsonFilter['activity_subgroup.name']
  }
  if (jsonFilter.name) {
    params.activity_names = []
    jsonFilter.name.v.forEach((value) => {
      params.activity_names.push(value)
    })
    delete jsonFilter.name
  }
  if (creationMode.value === 'selectFromLibrary') {
    jsonFilter.library_name = { v: [libConstants.LIBRARY_SPONSOR] }
  } else {
    jsonFilter['activity.library_name'] = { v: [libConstants.LIBRARY_SPONSOR] }
  }
  const filters = {
    jsonFilter: jsonFilter,
    params: params,
  }
  return filters
}

function selectActivity(activity) {
  if (!currentFlowchartGroup.value) {
    return
  }
  const activityCopy = { ...activity }
  activityCopy.flowchart_group = { ...currentFlowchartGroup.value }
  selectedActivities.value.push(activityCopy)
}

function selectAllActivities() {
  if (!currentFlowchartGroup.value) {
    return
  }
  for (const activity of activities.value) {
    if (
      !isActivitySelected(activity) &&
      !isActivityNotFinal(activity) &&
      !isActivityRequested(activity)
    ) {
      const activityCopy = { ...activity }
      activityCopy.flowchart_group = { ...currentFlowchartGroup.value }
      selectedActivities.value.push(activityCopy)
    }
  }
}

function selectStudyActivity(studyActivity) {
  const copy = { ...studyActivity }
  selectedActivities.value.push(copy)
}

function selectAllStudyActivities() {
  for (const studyActivity of activities.value) {
    if (!isStudyActivitySelected(studyActivity)) {
      const copy = { ...studyActivity }
      selectedActivities.value.push(copy)
    }
  }
}

function unselectActivity(activity) {
  if (creationMode.value === 'selectFromLibrary') {
    selectedActivities.value = selectedActivities.value.filter(
      (item) =>
        !(
          item.uid === activity.uid &&
          item.activity_group.uid === activity.activity_group.uid &&
          item.activity_subgroup.uid === activity.activity_subgroup.uid
        )
    )
  } else {
    selectedActivities.value = selectedActivities.value.filter(
      (item) =>
        !(
          item.activity.uid === activity.activity.uid &&
          item.study_activity_group.activity_group_uid ===
            activity.study_activity_group.activity_group_uid &&
          item.study_activity_subgroup.activity_subgroup_uid ===
            activity.study_activity_subgroup.activity_subgroup_uid
        )
    )
  }
}

function getCopyButtonColor(activity) {
  let selected = false
  if (creationMode.value === 'selectFromLibrary') {
    selected = selectedActivities.value.find(
      (item) =>
        item.uid === activity.uid &&
        item.activity_group.uid === activity.activity_group.uid &&
        item.activity_subgroup.uid === activity.activity_subgroup.uid
    )
  } else {
    selected = selectedActivities.value.find(
      (item) =>
        item.study_activity_uid === activity.study_activity_uid &&
        item.study_activity_group.activity_group_uid ===
          activity.study_activity_group.activity_group_uid &&
        item.study_activity_subgroup.activity_subgroup_uid ===
          activity.study_activity_subgroup.activity_subgroup_uid
    )
  }
  return !selected ? 'primary' : ''
}

function isActivitySelected(activity) {
  if (studyActivities.value) {
    let selected = selectedActivities.value.find(
      (item) =>
        item.uid === activity.uid &&
        item.activity_group.uid === activity.activity_group.uid &&
        item.activity_subgroup.uid === activity.activity_subgroup.uid
    )
    if (!selected && studyActivities.value.length) {
      selected = studyActivities.value.find(
        (item) =>
          item.activity.uid === activity.uid &&
          item.study_activity_group.activity_group_uid ===
            activity.activity_group.uid &&
          item.study_activity_subgroup.activity_subgroup_uid ===
            activity.activity_subgroup.uid
      )
    }
    return !currentFlowchartGroup.value || selected !== undefined
  }
  return false
}

function isActivityNotFinal(activity) {
  return activity.status !== statuses.FINAL
}

function isActivityRequested(activity) {
  return activity.library_name === libConstants.LIBRARY_REQUESTED
}

function isStudyActivityRequested(activity) {
  return activity.activity.library_name === libConstants.LIBRARY_REQUESTED
}

function isStudyActivitySelected(studyActivity) {
  let selected = selectedActivities.value.find(
    (item) => item.activity.uid === studyActivity.activity.uid
  )
  if (!selected && studyActivities.value.length) {
    selected = studyActivities.value.find(
      (item) => item.activity.uid === studyActivity.activity.uid
    )
  }
  return selected !== undefined
}

async function submit() {
  if (
    creationMode.value !== 'selectFromLibrary' &&
    creationMode.value !== 'selectFromStudies'
  ) {
    form.value.library_name = libConstants.LIBRARY_REQUESTED
    form.value.name_sentence_case = form.value.name.toLowerCase()
    const { valid } = await createPlaceholderForm.value.validate()
    if (!valid) {
      resetLoading.value += 1
      return
    }
    if (_isEmpty(form.value.activity_groupings[0])) {
      delete form.value.activity_groupings
    }
    const createdActivity = await activitiesApi.create(form.value, 'activities')
    await activitiesApi
      .approve(createdActivity.data.uid, 'activities')
      .then((resp) => {
        const activity = {
          ...resp.data,
          item_key: resp.data.uid,
        }
        if (resp.data.activity_groupings.length > 0) {
          activity.activity_group = {
            uid: resp.data.activity_groupings[0].activity_group_uid,
          }
          activity.activity_subgroup = {
            uid: resp.data.activity_groupings[0].activity_subgroup_uid,
          }
          activity.item_key =
            resp.data.uid +
            resp.data.activity_groupings[0].activity_group_uid +
            resp.data.activity_groupings[0].activity_subgroup_uid
        }
        selectActivity(activity)
      })
  }
  if (!selectedActivities.value.length) {
    eventBusEmit('notification', {
      type: 'info',
      msg: t('StudyActivityForm.select_activities_info'),
    })
    resetLoading.value += 1
    return
  }
  try {
    for (const item of selectedActivities.value) {
      let payload
      if (
        creationMode.value === 'selectFromLibrary' ||
        creationMode.value === 'createPlaceholder'
      ) {
        payload = {
          soa_group_term_uid: item.flowchart_group.term_uid,
          activity_uid: item.uid,
        }
        if (form.value.activity_groupings) {
          payload.activity_group_uid = item.activity_group.uid
          payload.activity_subgroup_uid = item.activity_subgroup.uid
        }
      } else {
        payload = {
          soa_group_term_uid: item.study_soa_group.soa_group_term_uid,
          activity_uid: item.activity.uid,
          activity_group_uid: item.study_activity_group.activity_group_uid,
          activity_subgroup_uid:
            item.study_activity_subgroup.activity_subgroup_uid,
        }
      }
      await study.createStudyActivity(
        studiesGeneralStore.selectedStudy.uid,
        payload
      )
    }
  } catch (error) {
    stepper.value.loading = false
    return
  }
  eventBusEmit('notification', {
    type: 'success',
    msg: t('StudyActivityForm.add_success'),
  })
  emit('added')
  close()
}

function getGroups() {
  const params = {
    page_size: 0,
    filters: { status: { v: [statuses.FINAL], op: 'co' } },
    sort_by: JSON.stringify({ name: true }),
  }
  activitiesApi.get(params, 'activity-groups').then((resp) => {
    groups.value = resp.data.items
  })
  activitiesApi.get(params, 'activity-sub-groups').then((resp) => {
    subgroups.value = resp.data.items
  })
}
</script>

<style scoped lang="scss">
.v-stepper {
  background-color: rgb(var(--v-theme-dfltBackground)) !important;
  box-shadow: none;
}

.step-title {
  color: rgb(var(--v-theme-secondary)) !important;
}
</style>
