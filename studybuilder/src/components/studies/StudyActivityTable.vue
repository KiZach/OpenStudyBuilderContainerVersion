<template>
  <NNTable
    key="studyActivityTable"
    ref="table"
    :headers="headers"
    :items="studyActivities"
    :items-length="total"
    item-value="study_activity_uid"
    export-object-label="StudyActivities"
    :export-data-url="exportDataUrl"
    :column-data-resource="`studies/${selectedStudy.uid}/study-activities`"
    :history-data-fetcher="fetchActivitiesHistory"
    :history-title="$t('StudyActivityTable.global_history_title')"
    :extra-item-class="getItemRowClass"
    :filters-modify-function="modifyFilters"
    @filter="getStudyActivities"
  >
    <template #[`footer.prepend`]>
      <v-chip color="yellow" variant="flat">
        {{ $t('StudyActivityTable.submitted') }}
      </v-chip>
      <v-chip class="ml-2" color="warning" variant="flat">
        {{ $t('StudyActivityTable.not_submitted') }}
      </v-chip>
      <v-spacer />
    </template>
    <template #actions="slot">
      <v-btn
        v-if="slot.showSelectBoxes"
        size="small"
        color="primary"
        :title="$t('StudyActivityTable.edit_activity_selection')"
        :disabled="
          !checkPermission($roles.STUDY_WRITE) || selectedStudyVersion !== null
        "
        icon="mdi-pencil-box-multiple-outline"
        @click="openBatchEditForm(slot.selected)"
      />
      <v-btn
        size="small"
        class="ml-2"
        color="primary"
        data-cy="add-study-activity"
        :title="$t('StudyActivityForm.add_title')"
        :disabled="
          !checkPermission($roles.STUDY_WRITE) || selectedStudyVersion !== null
        "
        icon="mdi-plus"
        @click.stop="showActivityForm = true"
      />
    </template>
    <template #[`item.actions`]="{ item }">
      <ActionsMenu
        :actions="getActionsForItem(item)"
        :item="item"
        :badge="actionsMenuBadge(item)"
      />
    </template>
    <template #[`item.activity.name`]="{ item }">
      <router-link
        :to="{
          name: 'StudyActivityOverview',
          params: { study_id: selectedStudy.uid, id: item.study_activity_uid },
        }"
      >
        {{ item.activity.name }}
      </router-link>
    </template>
    <template #[`item.activity.is_data_collected`]="{ item }">
      {{ $filters.yesno(item.activity.is_data_collected) }}
    </template>
    <template #[`item.start_date`]="{ item }">
      {{ $filters.date(item.start_date) }}
    </template>
  </NNTable>
  <v-dialog
    v-model="showActivityForm"
    persistent
    fullscreen
    content-class="fullscreen-dialog"
  >
    <StudyActivityForm @close="closeForm" @added="onStudyActivitiesUpdated" />
  </v-dialog>
  <v-dialog v-model="showActivityEditForm" max-width="1000px">
    <StudyActivityEditForm
      :study-activity="selectedStudyActivity"
      @close="closeEditForm"
      @updated="onStudyActivitiesUpdated"
    />
  </v-dialog>
  <v-dialog v-model="showDraftedActivityEditForm" max-width="1000px">
    <StudyDraftedActivityEditForm
      :study-activity="selectedStudyActivity"
      class="fullscreen-dialog"
      @close="closeEditForm"
      @updated="onStudyActivitiesUpdated"
    />
  </v-dialog>
  <v-dialog
    v-model="showHistory"
    persistent
    :fullscreen="$globals.historyDialogFullscreen"
    @keydown.esc="closeHistory"
  >
    <HistoryTable
      :title="activityHistoryTitle"
      :headers="headers"
      :items="activityHistoryItems"
      @close="closeHistory"
    />
  </v-dialog>
  <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
  <StudyActivityBatchEditForm
    :open="showBatchEditForm"
    :selection="currentSelection"
    @updated="onStudyActivitiesUpdated"
    @close="closeBatchEditForm"
    @remove="unselectItem"
  />
  <SelectionOrderUpdateForm
    v-if="selectedStudyActivity"
    ref="orderForm"
    :initial-value="selectedStudyActivity.order"
    :open="showOrderForm"
    @close="closeOrderForm"
    @submit="submitOrder"
  />
</template>

<script>
import { computed } from 'vue'
import study from '@/api/study'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import filteringParameters from '@/utils/filteringParameters'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import NNTable from '@/components/tools/NNTable.vue'
import StudyActivityBatchEditForm from './StudyActivityBatchEditForm.vue'
import StudyActivityEditForm from './StudyActivityEditForm.vue'
import StudyDraftedActivityEditForm from './StudyDraftedActivityEditForm.vue'
import StudyActivityForm from './StudyActivityForm.vue'
import SelectionOrderUpdateForm from '@/components/studies/SelectionOrderUpdateForm.vue'
import libConstants from '@/constants/libraries'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useStudyActivitiesStore } from '@/stores/studies-activities'

export default {
  components: {
    ActionsMenu,
    ConfirmDialog,
    NNTable,
    StudyActivityBatchEditForm,
    StudyActivityEditForm,
    StudyDraftedActivityEditForm,
    StudyActivityForm,
    HistoryTable,
    SelectionOrderUpdateForm,
  },
  inject: ['eventBusEmit'],
  setup() {
    const accessGuard = useAccessGuard()
    const studiesGeneralStore = useStudiesGeneralStore()
    const activitiesStore = useStudyActivitiesStore()

    return {
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
      selectedStudyVersion: computed(
        () => studiesGeneralStore.selectedStudyVersion
      ),
      activitiesStore,
      ...accessGuard,
    }
  },
  data() {
    return {
      libConstants: libConstants,
      actions: [
        {
          label: this.$t('StudyActivityTable.remove_and_info'),
          icon: 'mdi-delete-outline',
          iconColor: 'error',
          condition: (item) =>
            !this.selectedStudyVersion && this.checkIfRejected(item),
          click: this.showRejectingInfo,
          accessRole: this.$roles.STUDY_WRITE,
        },
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil-outline',
          iconColor: 'primary',
          condition: (item) =>
            !this.selectedStudyVersion &&
            !this.checkIfRejected(item) &&
            this.checkIfActivityRequestIsEditable(item),
          click: this.editStudyActivity,
          accessRole: this.$roles.STUDY_WRITE,
        },
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil-outline',
          iconColor: 'primary',
          condition: (item) =>
            !this.selectedStudyVersion &&
            !this.checkIfRejected(item) &&
            !this.checkIfActivityRequestIsEditable(item),
          click: this.editStudyDraftedActivity,
          accessRole: this.$roles.STUDY_WRITE,
        },
        {
          label: this.$t('_global.change_order'),
          icon: 'mdi-pencil-outline',
          iconColor: 'primary',
          condition: () => !this.selectedStudyVersion,
          click: this.changeActivityOrder,
          accessRole: this.$roles.STUDY_WRITE,
        },
        {
          label: this.$t('_global.delete'),
          icon: 'mdi-delete-outline',
          iconColor: 'error',
          condition: () => !this.selectedStudyVersion,
          click: this.deleteStudyActivity,
          accessRole: this.$roles.STUDY_WRITE,
        },
        {
          label: this.$t('_global.history'),
          icon: 'mdi-history',
          click: this.openHistory,
        },
      ],
      activityHistoryItems: [],
      currentSelection: [],
      selectedStudyActivity: null,
      showActivityEditForm: false,
      showDraftedActivityEditForm: false,
      showActivityForm: false,
      showBatchEditForm: false,
      showHistory: false,
      showOrderForm: false,
      headers: [
        { title: '', key: 'actions', width: '5%' },
        { title: '#', key: 'order', width: '5%' },
        { title: this.$t('_global.library'), key: 'activity.library_name' },
        {
          title: this.$t('StudyActivity.flowchart_group'),
          key: 'study_soa_group.soa_group_name',
        },
        {
          title: this.$t('StudyActivity.activity_group'),
          key: 'study_activity_group.activity_group_name',
          externalFilterSource: 'concepts/activities/activity-groups$name',
          exludeFromHeader: ['activity.is_data_collected'],
        },
        {
          title: this.$t('StudyActivity.activity_sub_group'),
          key: 'study_activity_subgroup.activity_subgroup_name',
          externalFilterSource: 'concepts/activities/activity-sub-groups$name',
          exludeFromHeader: ['activity.is_data_collected'],
        },
        { title: this.$t('StudyActivity.activity'), key: 'activity.name' },
        {
          title: this.$t('StudyActivity.data_collection'),
          key: 'activity.is_data_collected',
        },
        { title: this.$t('_global.modified'), key: 'start_date' },
        { title: this.$t('_global.modified_by'), key: 'user_initials' },
      ],
      studyActivities: [],
      total: 0,
    }
  },
  computed: {
    exportDataUrl() {
      return `studies/${this.selectedStudy.uid}/study-activities`
    },
    activityHistoryTitle() {
      if (this.selectedStudyActivity) {
        return this.$t('StudyActivityTable.study_activity_history_title', {
          studyActivityUid: this.selectedStudyActivity.study_activity_uid,
        })
      }
      return ''
    },
  },
  methods: {
    checkIfActivityRequestIsEditable(activity) {
      if (activity.activity.library_name === 'Requested') {
        return activity.activity.is_request_final
      }
      return true
    },
    checkIfRejected(activity) {
      if (
        activity.latest_activity &&
        activity.latest_activity.is_request_rejected
      ) {
        return true
      }
      return false
    },
    async showRejectingInfo(item) {
      const options = {
        type: 'info',
        width: 600,
        agreeLabel: this.$t('_global.accept'),
      }
      const msg = `${this.$t('StudyActivityTable.rejected_activity_info_part_1')}
        <p style="color:orange;"><b>${item.latest_activity.name}</b></p> ${this.$t('StudyActivityTable.rejected_activity_info_part_2')}
        <p style="color:orange;"><b>${item.latest_activity.reason_for_rejecting}.</b></p>${this.$t('StudyActivityTable.rejected_activity_info_part_3')}
        <b style="color:orange;">${item.latest_activity.contact_person.toUpperCase()}</b>${this.$t('StudyActivityTable.rejected_activity_info_part_4')}`
      if (await this.$refs.confirm.open(msg, options)) {
        study
          .deleteStudyActivity(this.selectedStudy.uid, item.study_activity_uid)
          .then(() => {
            this.$refs.table.filterTable()
            this.eventBusEmit('notification', {
              type: 'success',
              msg: this.$t('StudyActivityTable.delete_success'),
            })
          })
      }
    },
    getActionsForItem(item) {
      const result = [...this.actions]
      if (item.activity.replaced_by_activity) {
        result.unshift({
          label: this.$t('StudyActivityTable.update_activity_request'),
          icon: 'mdi-bell-outline',
          iconColor: 'red',
          click: this.updateActivityRequest,
        })
      }
      return result
    },
    actionsMenuBadge(item) {
      if (
        item.activity.replaced_by_activity ||
        (item.latest_activity && item.latest_activity.is_request_rejected)
      ) {
        return {
          color: 'error',
          icon: 'mdi-exclamation',
        }
      }
      return undefined
    },
    closeForm() {
      this.showActivityForm = false
    },
    closeEditForm() {
      this.showActivityEditForm = false
      this.showDraftedActivityEditForm = false
      this.selectedStudyActivity = null
    },
    async deleteStudyActivity(sa) {
      const options = { type: 'warning' }
      const activity = sa.activity.name
      const msg =
        !sa.show_activity_group_in_protocol_flowchart ||
        !sa.show_activity_subgroup_in_protocol_flowchart
          ? this.$t('StudyActivityTable.confirm_delete_side_effect')
          : this.$t('StudyActivityTable.confirm_delete', { activity })
      if (await this.$refs.confirm.open(msg, options)) {
        study
          .deleteStudyActivity(this.selectedStudy.uid, sa.study_activity_uid)
          .then(() => {
            this.$refs.table.filterTable()
            this.eventBusEmit('notification', {
              type: 'success',
              msg: this.$t('StudyActivityTable.delete_success'),
            })
          })
      }
    },
    editStudyActivity(sa) {
      this.selectedStudyActivity = sa
      this.showActivityEditForm = true
    },
    editStudyDraftedActivity(sa) {
      this.selectedStudyActivity = sa
      this.showDraftedActivityEditForm = true
    },
    updateActivityRequest(sa) {
      study
        .updateToApprovedActivity(this.selectedStudy.uid, sa.study_activity_uid)
        .then(() => {
          this.eventBusEmit('notification', {
            type: 'success',
            msg: this.$t('StudyActivityTable.update_success'),
          })
          this.$refs.table.filterTable()
        })
    },
    async openHistory(sa) {
      this.selectedStudyActivity = sa
      const resp = await study.getStudyActivityAuditTrail(
        this.selectedStudy.uid,
        sa.study_activity_uid
      )
      this.activityHistoryItems = resp.data
      this.showHistory = true
    },
    closeHistory() {
      this.selectedStudyActivity = null
      this.showHistory = false
    },
    async getStudyActivities(filters, options, filtersUpdated) {
      const params = filteringParameters.prepareParameters(
        options,
        filters,
        filtersUpdated
      )
      if (filters && filters !== undefined && filters !== '{}') {
        const filtersObj = JSON.parse(filters)
        if (filtersObj['study_activity_group.activity_group_name']) {
          params.activity_group_names = []
          filtersObj['study_activity_group.activity_group_name'].v.forEach(
            (value) => {
              params.activity_group_names.push(value)
            }
          )
          delete filtersObj['study_activity_group.activity_group_name']
        }
        if (filtersObj['study_activity_subgroup.activity_subgroup_name']) {
          params.activity_subgroup_names = []
          filtersObj[
            'study_activity_subgroup.activity_subgroup_name'
          ].v.forEach((value) => {
            params.activity_subgroup_names.push(value)
          })
          delete filtersObj['study_activity_subgroup.activity_subgroup_name']
        }
        if (filtersObj.name) {
          params.activity_names = []
          filtersObj.name.v.forEach((value) => {
            params.activity_names.push(value)
          })
          delete filtersObj.name
        }
        if (Object.keys(filtersObj).length) {
          params.filters = JSON.stringify(filtersObj)
        }
      }
      params.studyUid = this.selectedStudy.uid
      const resp = await this.activitiesStore.fetchStudyActivities(params)
      this.studyActivities = resp.data.items
      this.total = resp.data.total
    },
    modifyFilters(jsonFilter, params) {
      if (jsonFilter['study_activity_group.activity_group_name']) {
        params.activity_group_names = []
        jsonFilter['study_activity_group.activity_group_name'].v.forEach(
          (value) => {
            params.activity_group_names.push(value)
          }
        )
        delete jsonFilter['study_activity_group.activity_group_name']
      }
      if (jsonFilter['study_activity_subgroup.activity_subgroup_name']) {
        params.activity_subgroup_names = []
        jsonFilter['study_activity_subgroup.activity_subgroup_name'].v.forEach(
          (value) => {
            params.activity_subgroup_names.push(value)
          }
        )
        delete jsonFilter['study_activity_subgroup.activity_subgroup_name']
      }
      if (jsonFilter['activity.name']) {
        params.activity_names = []
        jsonFilter['activity.name'].v.forEach((value) => {
          params.activity_names.push(value)
        })
        delete jsonFilter['activity.name']
      }
      return {
        jsonFilter: jsonFilter,
        params: params,
      }
    },
    openBatchEditForm(selection) {
      if (!selection.length) {
        this.eventBusEmit('notification', {
          type: 'warning',
          msg: this.$t('StudyActivityTable.batch_edit_no_selection'),
        })
        return
      }
      this.currentSelection = selection
      this.showBatchEditForm = true
    },
    closeBatchEditForm() {
      this.currentSelection = []
      this.showBatchEditForm = false
    },
    submitOrder(value) {
      study
        .updateStudyActivityOrder(
          this.selectedStudyActivity.study_uid,
          this.selectedStudyActivity.study_activity_uid,
          value
        )
        .then(() => {
          this.$refs.table.filterTable()
          this.closeOrderForm()
          this.eventBusEmit('notification', {
            msg: this.$t('_global.order_updated'),
          })
        })
    },
    changeActivityOrder(activity) {
      this.selectedStudyActivity = activity
      this.showOrderForm = true
    },
    closeOrderForm() {
      this.selectedStudyActivity = null
      this.showOrderForm = false
    },
    onStudyActivitiesUpdated() {
      this.$refs.table.filterTable()
    },
    unselectItem(item) {
      this.currentSelection = this.currentSelection.filter(
        (sa) => sa.study_activity_uid !== item.study_activity_uid
      )
    },
    async fetchActivitiesHistory() {
      const resp = await study.getStudyActivitiesAuditTrail(
        this.selectedStudy.uid
      )
      return resp.data
    },
    getItemRowClass(item) {
      return item.activity.library_name === libConstants.LIBRARY_REQUESTED
        ? item.activity.is_request_final
          ? 'yellow'
          : 'warning'
        : ''
    },
  },
}
</script>
