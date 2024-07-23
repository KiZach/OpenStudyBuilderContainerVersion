<template>
  <div>
    <NNTable
      ref="tableRef"
      v-model:expanded="expandedGroup"
      :headers="currentHeaders"
      :items="activities"
      export-object-label="Activities"
      :hide-export-button="source === 'activities-by-grouping'"
      :hide-default-switches="source === 'activities-by-grouping'"
      :export-data-url="`concepts/activities/${source}`"
      item-value="item_key"
      :items-length="total"
      :show-filter-bar-by-default="
        ['activities'].includes(source) && !requested
      "
      :column-data-resource="`concepts/activities/${source}`"
      :sub-tables="isExpand()"
      :filters-modify-function="modifyFilters"
      :modifiable-table="!isExpand()"
      :disable-filtering="source === 'activities-by-grouping'"
      :history-title="$t('_global.audit_trail')"
      :history-data-fetcher="
        source !== 'activities-by-grouping' ? fetchGlobalAuditTrail : null
      "
      history-change-field="change_description"
      :history-excluded-headers="historyExcludedHeaders"
      :default-filters="setDefaultFilters()"
      @filter="fetchActivities"
      @update:expanded="getSubGroups"
    >
      <template
        v-if="isExpand()"
        #item="{ item, internalItem, toggleExpand, isExpanded }"
      >
        <tr style="background-color: rgb(var(--v-theme-dfltBackgroundLight1))">
          <td width="40%" :class="'font-weight-bold'">
            <v-row class="align-center">
              <v-btn
                v-if="isExpanded(internalItem)"
                icon="mdi-chevron-down"
                variant="text"
                @click="toggleExpand(internalItem)"
              />
              <v-btn
                v-else
                icon="mdi-chevron-right"
                variant="text"
                @click="toggleExpand(internalItem)"
              />
              <span class="ml-2">
                {{ item.name }}
              </span>
            </v-row>
          </td>
          <td width="25%">
            {{ $filters.date(item.start_date) }}
          </td>
          <td width="15%">
            <StatusChip :status="item.status" />
          </td>
          <td width="20%">
            {{ item.version }}
          </td>
        </tr>
      </template>
      <template #[`item.possible_actions`]="{ item }">
        <div class="pr-0 mr-0">
          <ActionsMenu :actions="actions" :item="item" :source="source" />
        </div>
      </template>
      <template #[`item.name`]="{ item }">
        <template v-if="source === 'activity-instances'">
          <router-link
            :to="{ name: 'ActivityInstanceOverview', params: { id: item.uid } }"
          >
            {{ item.name }}
          </router-link>
        </template>
        <template v-else-if="source === 'activities'">
          <router-link
            :to="{ name: 'ActivityOverview', params: { id: item.uid } }"
          >
            {{ item.name }}
          </router-link>
        </template>
        <div v-else :class="isExpand() ? 'font-weight-bold' : ''">
          {{ item.name }}
        </div>
      </template>
      <template #[`item.nci_concept_id`]="{ item }">
        <NCIConceptLink :concept-id="item.nci_concept_id" />
      </template>
      <template #[`item.status`]="{ item }">
        <StatusChip :status="item.status" />
      </template>
      <template #[`item.start_date`]="{ item }">
        {{ $filters.date(item.start_date) }}
      </template>
      <template #[`item.activity_groups`]="{ item }">
        {{ $filters.names(item.activity_groups) }}
      </template>
      <template #[`item.activity_group.name`]="{ item }">
        <div v-html="groupsDisplay(item)" />
      </template>
      <template #[`item.activity_subgroup.name`]="{ item }">
        <div v-html="subGroupsDisplay(item)" />
      </template>
      <template #[`item.activities.name`]="{ item }">
        {{ activitiesDisplay(item) }}
      </template>
      <template #[`item.is_data_collected`]="{ item }">
        {{ $filters.yesno(item.is_data_collected) }}
      </template>
      <template #[`item.is_required_for_activity`]="{ item }">
        {{ $filters.yesno(item.is_required_for_activity) }}
      </template>
      <template #[`item.is_default_selected_for_activity`]="{ item }">
        {{ $filters.yesno(item.is_default_selected_for_activity) }}
      </template>
      <template #[`item.is_data_sharing`]="{ item }">
        {{ $filters.yesno(item.is_data_sharing) }}
      </template>
      <template #[`item.is_legacy_usage`]="{ item }">
        {{ $filters.yesno(item.is_legacy_usage) }}
      </template>
      <template #expanded-row="{ columns }">
        <tr>
          <td :colspan="columns.length" class="pa-0">
            <v-data-table
              v-model:expanded="expandedSubGroup"
              class="elevation-0"
              :items="subgroups"
              item-value="uid"
              :items-per-page="-1"
              :loading="loading"
              :show-expand="true"
              @update:expanded="getSubgroupActivities"
            >
              <template #headers />
              <template #bottom />
              <template
                #item="{ item, internalItem, toggleExpand, isExpanded }"
              >
                <tr
                  style="
                    background-color: rgb(var(--v-theme-dfltBackgroundLight2));
                  "
                >
                  <td width="40%" class="font-weight-bold">
                    <div class="ml-6">
                      <v-row class="align-center">
                        <v-btn
                          v-if="isExpanded(internalItem)"
                          icon="mdi-chevron-down"
                          variant="text"
                          @click="toggleExpand(internalItem)"
                        />
                        <v-btn
                          v-else
                          icon="mdi-chevron-right"
                          variant="text"
                          @click="toggleExpand(internalItem)"
                        />
                        {{ item.name }}
                      </v-row>
                    </div>
                  </td>
                  <td width="25%">
                    {{ $filters.date(item.start_date) }}
                  </td>
                  <td width="15%">
                    <StatusChip :status="item.status" />
                  </td>
                  <td width="20%">
                    {{ item.version }}
                  </td>
                </tr>
              </template>
              <template #expanded-row="{ columns }">
                <tr>
                  <td :colspan="columns.length" class="pa-0">
                    <v-data-table
                      class="elevation-0"
                      :items="subgroupActivities"
                      item-value="uid"
                      :items-per-page="-1"
                      :loading="subLoading"
                      :show-expand="true"
                    >
                      <template #headers />
                      <template #bottom />
                      <template #item="{ item }">
                        <tr>
                          <td width="40%">
                            <div class="ml-12">
                              {{ item.name }}
                            </div>
                          </td>
                          <td width="25%">
                            {{ $filters.date(item.start_date) }}
                          </td>
                          <td width="15%">
                            <StatusChip :status="item.status" />
                          </td>
                          <td width="20%">
                            {{ item.version }}
                          </td>
                        </tr>
                      </template>
                    </v-data-table>
                  </td>
                </tr>
              </template>
            </v-data-table>
          </td>
        </tr>
      </template>
      <template #afterSwitches>
        <v-switch
          v-if="requested"
          v-model="showFinalised"
          :label="$t('ActivityTable.show_only_handled')"
          hide-details
          color="primary"
          @update:model-value="tableRef.filterTable()"
        />
      </template>
      <template #actions="">
        <slot name="extraActions" />
        <v-btn
          v-if="source !== 'activities-by-grouping'"
          size="small"
          color="primary"
          data-cy="add-activity"
          :title="itemCreationTitle"
          :disabled="!accessGuard.checkPermission($roles.LIBRARY_WRITE)"
          icon="mdi-plus"
          @click.stop="showForm"
        />
      </template>
    </NNTable>
    <ActivitiesForm
      :open="showActivityForm"
      :edited-activity="activeItem"
      @close="closeForm"
    />
    <RequestedActivitiesForm
      :open="showRequestedActivityForm"
      :edited-activity="activeItem"
      @close="closeForm"
    />
    <v-dialog
      :model-value="showGroupsForm"
      persistent
      max-width="800px"
      content-class="top-dialog"
    >
      <ActivitiesGroupsForm
        ref="groupFormRef"
        :open="showGroupsForm"
        :subgroup="!groupMode"
        :edited-group-or-subgroup="activeItem"
        @close="closeForm"
      />
    </v-dialog>
    <v-dialog
      v-model="showInstantiationsForm"
      persistent
      fullscreen
      content-class="fullscreen-dialog"
    >
      <ActivitiesInstantiationsForm
        class="fullscreen-dialog"
        :edited-activity="activeItem"
        @close="closeForm"
      />
    </v-dialog>
    <v-dialog
      v-model="showSponsorFromRequestedForm"
      persistent
      max-width="1200px"
      content-class="top-dialog"
    >
      <ActivitiesCreateSponsorFromRequestedForm
        :edited-activity="activeItem"
        @close="closeForm"
      />
    </v-dialog>
    <v-dialog
      v-model="showHistory"
      persistent
      :max-width="$globals.historyDialogMaxWidth"
      :fullscreen="$globals.historyDialogFullscreen"
      @keydown.esc="closeHistory"
    >
      <HistoryTable
        :title="itemHistoryTitle"
        :headers="currentHeaders"
        :items="historyItems"
        :excluded-headers="historyExcludedHeaders"
        @close="closeHistory"
      />
    </v-dialog>
  </div>
</template>

<script setup>
import activitiesApi from '@/api/activities'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import NNTable from '@/components/tools/NNTable.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import ActivitiesForm from '@/components/library/ActivitiesForm.vue'
import RequestedActivitiesForm from '@/components/library/RequestedActivitiesForm.vue'
import ActivitiesGroupsForm from '@/components/library/ActivitiesGroupsForm.vue'
import ActivitiesInstantiationsForm from '@/components/library/ActivitiesInstantiationsForm.vue'
import ActivitiesCreateSponsorFromRequestedForm from '@/components/library/ActivitiesCreateSponsorFromRequestedForm.vue'
import libConstants from '@/constants/libraries'
import { useAccessGuard } from '@/composables/accessGuard'
import NCIConceptLink from '@/components/tools/NCIConceptLink.vue'
import filteringParameters from '@/utils/filteringParameters'
import statuses from '@/constants/statuses'
import _isEmpty from 'lodash/isEmpty'
import { useLibraryActivitiesStore } from '@/stores/library-activities'
import { computed, inject, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  source: {
    type: String,
    default: null,
  },
  requested: {
    type: Boolean,
    default: false,
  },
})

const { t } = useI18n()
const accessGuard = useAccessGuard()
const activitiesStore = useLibraryActivitiesStore()
const eventBusEmit = inject('eventBusEmit')
const roles = inject('roles')
const tableRef = ref()
const groupFormRef = ref()
  
const actions = [
  {
    label: t('ActivityTable.handle_placeholder_request'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    condition: (item) => item.status === statuses.FINAL && props.requested,
    accessRole: roles.LIBRARY_WRITE,
    click: createSponsorFromRequested,
  },
  {
    label: t('_global.approve'),
    icon: 'mdi-check-decagram',
    iconColor: 'success',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'approve'),
    accessRole: roles.LIBRARY_WRITE,
    click: approveItem,
  },
  {
    label: t('_global.edit'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'edit'),
    accessRole: roles.LIBRARY_WRITE,
    click: editItem,
  },
  {
    label: t('_global.new_version'),
    icon: 'mdi-plus-circle-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'new_version'),
    accessRole: roles.LIBRARY_WRITE,
    click: newItemVersion,
  },
  {
    label: t('_global.inactivate'),
    icon: 'mdi-close-octagon-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'inactivate'),
    accessRole: roles.LIBRARY_WRITE,
    click: inactivateItem,
  },
  {
    label: t('_global.reactivate'),
    icon: 'mdi-undo-variant',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'reactivate'),
    accessRole: roles.LIBRARY_WRITE,
    click: reactivateItem,
  },
  {
    label: t('_global.delete'),
    icon: 'mdi-delete-outline',
    iconColor: 'error',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'delete'),
    accessRole: roles.LIBRARY_WRITE,
    click: deleteItem,
  },
  {
    label: t('_global.history'),
    icon: 'mdi-history',
    accessRole: roles.LIBRARY_READ,
    click: openItemHistory,
  },
]
const activities = ref([])
const activitiesHeaders = [
  { title: '', key: 'possible_actions', width: '5%', noFilter: true },
  { title: t('_global.library'), key: 'library_name' },
  {
    title: t('ActivityTable.activity_group'),
    key: 'activity_group.name',
    externalFilterSource: 'concepts/activities/activity-groups$name',
    width: '15%',
    exludeFromHeader: ['is_data_collected'],
  },
  {
    title: t('ActivityTable.activity_subgroup'),
    key: 'activity_subgroup.name',
    externalFilterSource: 'concepts/activities/activity-sub-groups$name',
    width: '15%',
    exludeFromHeader: ['is_data_collected'],
  },
  {
    title: t('ActivityTable.activity_name'),
    key: 'name',
    externalFilterSource: 'concepts/activities/activities$name',
  },
  {
    title: t('ActivityTable.sentence_case_name'),
    key: 'name_sentence_case',
  },
  {
    title: t('ActivityTable.nci_concept_id'),
    key: 'nci_concept_id',
  },
  { title: t('ActivityTable.abbreviation'), key: 'abbreviation' },
  {
    title: t('ActivityTable.is_data_collected'),
    key: 'is_data_collected',
  },
  { title: t('_global.modified'), key: 'start_date' },
  { title: t('_global.status'), key: 'status' },
  { title: t('_global.version'), key: 'version' },
]
const instantiationsHeaders = [
  { title: '', key: 'possible_actions', width: '5%', noFilter: true },
  { title: t('_global.library'), key: 'library_name' },
  {
    title: t('ActivityTable.type'),
    key: 'activity_instance_class.name',
  },
  {
    title: t('ActivityTable.activity'),
    key: 'activity_name',
    disableColumnFilters: true,
  },
  { title: t('ActivityTable.instance'), key: 'name' },
  { title: t('_global.definition'), key: 'definition' },
  {
    title: t('ActivityTable.nci_concept_id'),
    key: 'nci_concept_id',
  },
  { title: t('ActivityTable.topic_code'), key: 'topic_code' },
  { title: t('ActivityTable.adam_code'), key: 'adam_param_code' },
  {
    title: t('ActivityTable.is_required_for_activity'),
    key: 'is_required_for_activity',
  },
  {
    title: t('ActivityTable.is_default_selected_for_activity'),
    key: 'is_default_selected_for_activity',
  },
  {
    title: t('ActivityTable.is_data_sharing'),
    key: 'is_data_sharing',
  },
  {
    title: t('ActivityTable.is_legacy_usage'),
    key: 'is_legacy_usage',
  },
  { title: t('_global.modified'), key: 'start_date' },
  { title: t('_global.modified_by'), key: 'user_initials' },
  { title: t('_global.status'), key: 'status' },
  { title: t('_global.version'), key: 'version' },
]
const groupsHeaders = [
  { title: t('ActivityTable.group_or_subgroup'), key: 'name' },
  { title: t('_global.modified'), key: 'start_date' },
  { title: t('_global.status'), key: 'status' },
  { title: t('_global.version'), key: 'version' },
]
const requestedHeaders = [
  { title: '', key: 'possible_actions', width: '5%' },
  {
    title: t('ActivityTable.activity_group'),
    key: 'activity_group.name',
    externalFilterSource: 'concepts/activities/activity-groups$name',
  },
  {
    title: t('ActivityTable.activity_subgroup'),
    key: 'activity_subgroup.name',
    externalFilterSource: 'concepts/activities/activity-sub-groups$name',
  },
  {
    title: t('ActivityTable.activity'),
    key: 'name',
    externalFilterSource: 'concepts/activities/activities$name',
  },
  {
    title: t('ActivityTable.sentence_case_name'),
    key: 'name_sentence_case',
  },
  { title: t('ActivityTable.abbreviation'), key: 'abbreviation' },
  { title: t('ActivityTable.definition'), key: 'definition' },
  {
    title: t('ActivityTable.rationale_for_request'),
    key: 'request_rationale',
  },
  { title: t('ActivityTable.study_id'), key: 'requester_study_id' },
  { title: t('_global.modified'), key: 'start_date' },
  { title: t('_global.modified_by'), key: 'user_initials' },
  { title: t('_global.status'), key: 'status' },
  { title: t('_global.version'), key: 'version' },
]
const activityGroupHeaders = [
  { title: '', key: 'possible_actions', width: '5%' },
  { title: t('ActivityTable.activity_group'), key: 'name' },
  {
    title: t('ActivityTable.sentence_case_name'),
    key: 'name_sentence_case',
  },
  { title: t('ActivityTable.abbreviation'), key: 'abbreviation' },
  { title: t('_global.definition'), key: 'definition' },
  { title: t('_global.modified'), key: 'start_date' },
  { title: t('_global.status'), key: 'status' },
  { title: t('_global.version'), key: 'version' },
]
const activitySubgroupHeaders = [
  { title: '', key: 'possible_actions', width: '5%' },
  {
    title: t('ActivityTable.activity_group'),
    key: 'activity_groups',
    externalFilterSource: 'concepts/activities/activity-groups$name',
  },
  { title: t('ActivityTable.activity_subgroup'), key: 'name' },
  {
    title: t('ActivityTable.sentence_case_name'),
    key: 'name_sentence_case',
  },
  { title: t('ActivityTable.abbreviation'), key: 'abbreviation' },
  { title: t('_global.definition'), key: 'definition' },
  { title: t('_global.modified'), key: 'start_date' },
  { title: t('_global.status'), key: 'status' },
  { title: t('_global.version'), key: 'version' },
]
const groupMode = ref(false)
const historyItems = ref([])
const historyExcludedHeaders = ['possible_actions']
const total = ref(0)
const savedFilters = ref('')
const subgroups = ref([])
const currentGroup = ref('')
const currentSubGroup = ref('')
const showActivityForm = ref(false)
const showRequestedActivityForm = ref(false)
const showGroupsForm = ref(false)
const showHistory = ref(false)
const showInstantiationsForm = ref(false)
const showSponsorFromRequestedForm = ref(false)
const activeItem = ref(null)
const loading = ref(false)
const subLoading = ref(false)
const subgroupActivities = ref([])
const showFinalised = ref(false)
const expandedGroup = ref([])
const expandedSubGroup = ref([])
      
watch(expandedGroup, () => {
  if (expandedGroup.value.length > 1) {
    expandedGroup.value.splice(0, 1)
  }
})

watch(expandedSubGroup, () => {
  if (expandedSubGroup.value.length > 1) {
    expandedSubGroup.value.splice(0, 1)
  }
})

const itemCreationTitle = computed(() => {
  if (props.source === 'activities') {
    return t('ActivityForms.add_activity')
  } else if (props.source === 'activity-instances') {
    return t('ActivityForms.addInstance')
  } else if (props.source === 'activity-groups') {
    return t('ActivityForms.add_group')
  } else if (props.source === 'activity-sub-groups') {
    return t('ActivityForms.add_subgroup')
  }
  return ''
})

const itemHistoryTitle = computed(() => {
  if (activeItem.value) {
    let type
    switch (props.source) {
      case 'activities':
        type = t('ActivitiesTable.activity')
        break
      case 'activity-groups':
        type = t('ActivitiesTable.activity_group')
        break
      case 'activity-sub-groups':
        type = t('ActivitiesTable.activity_subgroup')
        break
      case 'activity-instances':
        type = t('ActivitiesTable.activity_instance')
        break
    }
    return t('ActivitiesTable.item_history_title', {
      uid: activeItem.value.uid,
      type,
    })
  }
  return ''
})

const currentHeaders = computed(() => {
  switch (props.source) {
    case 'activities':
      return props.requested ? requestedHeaders : activitiesHeaders
    case 'activity-groups':
      return activityGroupHeaders
    case 'activity-sub-groups':
      return activitySubgroupHeaders
    case 'activities-by-grouping':
      return groupsHeaders
    case 'activity-instances':
      return instantiationsHeaders
  }
  return []
})

onMounted(() => {
  activitiesStore.getGroupsAndSubgroups()
})
  
  
function transformItems(items) {
  const activities = []
  if (props.source === 'activities') {
    for (const item of items) {
      if (item.activity_groupings.length > 0) {
        const groups = []
        const subgroups = []
        for (const grouping of item.activity_groupings) {
          groups.push(grouping.activity_group_name)
          subgroups.push(grouping.activity_subgroup_name)
        }
        activities.push({
          activity_group: { name: groups },
          activity_subgroup: { name: subgroups },
          item_key: item.uid,
          ...item,
        })
      } else {
        activities.push({
          activity_group: { name: '' },
          activity_subgroup: { name: '' },
          item_key: item.uid,
          ...item,
        })
      }
    }
  } else if (props.source === 'activity-instances') {
    for (const item of items) {
      if (item.activity_groupings.length > 0) {
        item.activities = [item.activity_groupings[0].activity]
        item.activity_group = item.activity_groupings[0].activity_group
        item.activity_subgroup =
          item.activity_groupings[0].activity_subgroup
      } else {
        item.activities = []
      }
      item.item_key = item.uid
      activities.push(item)
    }
  } else {
    for (const item of items) {
      item.item_key = item.uid
      activities.push(item)
    }
  }
  return activities
}

function fetchActivities(filters, options, filtersUpdated) {
  if (filters !== undefined) {
    savedFilters.value = filters
  }
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  if (
    options.sortBy[0] &&
    options.sortBy[0].key === 'activity_group.name'
  ) {
    params.sort_by = JSON.stringify({
      'activity_groupings[0].activity_group_name':
        options.sortBy[0].order === 'desc' ? false : true,
    })
  } else if (
    options.sortBy[0] &&
    options.sortBy[0].key === 'activity_subgroup.name'
  ) {
    params.sort_by = JSON.stringify({
      'activity_groupings[0].activity_subgroup_name':
        options.sortBy[0].order === 'desc' ? false : true,
    })
  }
  params.filters = {}
  if (props.requested) {
    params.library = libConstants.LIBRARY_REQUESTED
  }
  if (
    savedFilters.value &&
    savedFilters.value !== undefined &&
    savedFilters.value !== '{}' &&
    props.source === 'activities'
  ) {
    const filtersObj = JSON.parse(savedFilters.value)
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
  } else if (
    savedFilters.value &&
    savedFilters.value !== undefined &&
    savedFilters.value !== '{}' &&
    props.source === 'activity-instances'
  ) {
    const filtersObj = JSON.parse(savedFilters.value)
    if (filtersObj['activities.name']) {
      params.activity_names = []
      filtersObj['activities.name'].v.forEach((value) => {
        params.activity_names.push(value)
      })
      delete filtersObj['activities.name']
    }
    if (filtersObj.specimen) {
      params.specimen_names = []
      filtersObj.specimen.v.forEach((value) => {
        params.specimen_names.push(value)
      })
      delete filtersObj.specimen
    }
    if (
      Object.keys(filtersObj).length !== 0 &&
      filtersObj.constructor === Object
    ) {
      params.filters = JSON.stringify(filtersObj)
    }
  } else if (
    savedFilters.value !== undefined &&
    savedFilters.value !== '{}' &&
    props.source === 'activity-sub-groups'
  ) {
    const filtersObj = JSON.parse(savedFilters.value)
    if (filtersObj.activity_groups) {
      params.activity_group_names = []
      filtersObj.activity_groups.v.forEach((value) => {
        params.activity_group_names.push(value)
      })
      delete filtersObj.activity_groups
    }
    if (
      Object.keys(filtersObj).length !== 0 &&
      filtersObj.constructor === Object
    ) {
      params.filters = JSON.stringify(filtersObj)
    }
  } else if (savedFilters.value !== undefined && savedFilters.value !== '{}') {
    params.filters = savedFilters.value
  }
  if (props.requested) {
    if (_isEmpty(params.filters)) {
      params.filters = {
        is_finalized: { v: [showFinalised.value] },
        is_request_final: { v: [true] },
      }
    } else {
      const filtersObj = JSON.parse(params.filters)
      filtersObj.is_finalized = { v: [showFinalised.value] }
      filtersObj.is_request_final = { v: [true] }
      params.filters = filtersObj
    }
  }
  const source =
    props.source !== 'activities-by-grouping'
      ? props.source
      : 'activity-groups'
  activitiesApi.get(params, source).then((resp) => {
    activities.value = transformItems(resp.data.items)
    total.value = resp.data.total
  })
  if (currentGroup.value) {
    activitiesApi.getSubGroups(currentGroup.value).then((resp) => {
      subgroups.value = resp.data.items
    })
  }
  if (currentSubGroup.value) {
    activitiesApi.getSubGroupActivities(currentSubGroup.value).then((resp) => {
      subgroupActivities.value = resp.data.items
    })
  }
  if (groupFormRef.value) {
    groupFormRef.value.getGroups()
  }
}

async function fetchGlobalAuditTrail(options) {
  const resp = await activitiesApi.getAuditTrail(props.source, options)
  return transformItems(resp.data.items)
}

function modifyFilters(jsonFilter, params) {
  if (jsonFilter['activity_group.name']) {
    params.activity_group_names = []
    jsonFilter['activity_group.name'].v.forEach((value) => {
      params.activity_group_names.push(value)
    })
    delete jsonFilter['activity_group.name']
  }
  if (jsonFilter.activity_groups) {
    params.activity_group_names = []
    jsonFilter.activity_groups.v.forEach((value) => {
      params.activity_group_names.push(value)
    })
    delete jsonFilter.activity_groups
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
  if (jsonFilter['activities.name']) {
    params.activity_names = []
    jsonFilter['activities.name'].v.forEach((value) => {
      params.activity_names.push(value)
    })
    delete jsonFilter['activities.name']
  }
  if (jsonFilter.specimen) {
    params.specimen_names = []
    jsonFilter.activities.v.forEach((value) => {
      params.specimen_names.push(value)
    })
    delete jsonFilter.specimen
  }
  return {
    jsonFilter: jsonFilter,
    params: params,
  }
}

function isExpand() {
  return props.source === 'activities-by-grouping'
}

function subGroupsDisplay(item) {
  let display = ''
  if (item.activity_subgroup.name === '') {
    return ''
  } else {
    item.activity_subgroup.name.forEach((element) => {
      display += '&#9679; ' + element + '</br>'
    })
    return display
  }
}

function groupsDisplay(item) {
  let display = ''
  if (item.activity_group.name === '') {
    return ''
  } else {
    item.activity_group.name.forEach((element) => {
      display += '&#9679; ' + element + '</br>'
    })
    return display
  }
}

function activitiesDisplay(item) {
  let display = ''
  if (item.activities) {
    item.activities.forEach((element) => {
      display += element.name + ', '
    })
  }
  return display.slice(0, -2)
}

function inactivateItem(item, source) {
  source = source === undefined ? props.source : source
  activitiesApi.inactivate(item.uid, source).then(() => {
    eventBusEmit('notification', {
      msg: t(`ActivitiesTable.inactivate_${props.source}_success`),
      type: 'success',
    })
    tableRef.value.filterTable()
  })
}

function reactivateItem(item, source) {
  source = source === undefined ? props.source : source
  activitiesApi.reactivate(item.uid, source).then(() => {
    eventBusEmit('notification', {
      msg: t(`ActivitiesTable.reactivate_${props.source}_success`),
      type: 'success',
    })
    tableRef.value.filterTable()
  })
}

function deleteItem(item, source) {
  source = source === undefined ? props.source : source
  activitiesApi.delete(item.uid, source).then(() => {
    eventBusEmit('notification', {
      msg: t(`ActivitiesTable.delete_${props.source}_success`),
      type: 'success',
    })
    tableRef.value.filterTable()
  })
}

function approveItem(item, source) {
  source = source === undefined ? props.source : source
  activitiesApi.approve(item.uid, source).then(() => {
    eventBusEmit('notification', {
      msg: t(`ActivitiesTable.approve_${props.source}_success`),
      type: 'success',
    })
    tableRef.value.filterTable()
  })
}

function newItemVersion(item, source) {
  source = source === undefined ? props.source : source
  activitiesApi.newVersion(item.uid, source).then(() => {
    eventBusEmit('notification', {
      msg: t('_global.new_version_success'),
      type: 'success',
    })
    tableRef.value.filterTable()
  })
}

function showForm() {
  switch (props.source) {
    case 'activities':
      if (props.requested) {
        showRequestedActivityForm.value = true
      } else {
        showActivityForm.value = true
      }
      return
    case 'activity-groups':
      groupMode.value = true
      showGroupsForm.value = true
      return
    case 'activity-sub-groups':
      groupMode.value = false
      showGroupsForm.value = true
      return
    case 'activity-instances':
      showInstantiationsForm.value = true
  }
}

function editItem(item) {
  activeItem.value = item
  switch (props.source) {
    case 'activities':
      if (props.requested) {
        showRequestedActivityForm.value = true
      } else {
        showActivityForm.value = true
      }
      return
    case 'activity-groups':
      groupMode.value = true
      showGroupsForm.value = true
      return
    case 'activity-sub-groups':
      groupMode.value = false
      showGroupsForm.value = true
      return
    case 'activity-instances':
      showInstantiationsForm.value = true
  }
}

async function openItemHistory(item) {
  activeItem.value = item
  const resp = await activitiesApi.getVersions(props.source, item.uid)
  historyItems.value = transformItems(resp.data)
  showHistory.value = true
}

function closeHistory() {
  activeItem.value = null
  showHistory.value = false
}

function createSponsorFromRequested(item) {
  activeItem.value = item
  showSponsorFromRequestedForm.value = true
}

function getSubGroups(items) {
  if (!items.length) {
    return
  }
  const item = items[items.length - 1]
  subgroups.value = []
  loading.value = true
  currentGroup.value = item.uid
  activitiesApi.getSubGroups(item.uid).then((resp) => {
    subgroups.value = resp.data.items
    loading.value = false
  })
}

function getSubgroupActivities(items) {
  if (!items.length) {
    return
  }
  const item = items[items.length - 1]
  subgroupActivities.value = []
  subLoading.value = true
  currentSubGroup.value = item
  activitiesApi.getSubGroupActivities(item).then((resp) => {
    subgroupActivities.value = resp.data.items
    subLoading.value = false
  })
}

function closeForm() {
  showActivityForm.value = false
  showRequestedActivityForm.value = false
  showGroupsForm.value = false
  showInstantiationsForm.value = false
  showSponsorFromRequestedForm.value = false
  activeItem.value = null
  tableRef.value.filterTable()
}

function setDefaultFilters() {
  if (props.source === 'activity-instances') {
    return [
      {
        title: t('ActivityTable.activity'),
        key: 'activity_name',
        disableColumnFilters: true,
      },
      { title: t('ActivityTable.instance'), key: 'name' },
      { title: t('_global.status'), key: 'status' },
      { title: t('ActivityTable.topic_code'), key: 'topic_code' },
      { title: t('ActivityTable.is_legacy_usage'), key: 'is_legacy_usage' },
    ]
  }
  return [{ title: t('_global.status'), key: 'status' }]
}
    
</script>
