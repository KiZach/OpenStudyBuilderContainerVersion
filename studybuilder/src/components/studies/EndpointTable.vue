<template>
  <div>
    <NNTable
      key="endpointTable1"
      :headers="headers"
      :items="formatedStudyEndpoints"
      item-value="study_endpoint_uid"
      :column-data-resource="`studies/${selectedStudy.uid}/study-endpoints`"
      :export-data-url="exportDataUrl"
      export-object-label="StudyEndpoints"
      :items-length="total"
      :history-data-fetcher="fetchEndpointsHistory"
      :history-title="$t('StudyEndpointsTable.global_history_title')"
      :history-html-fields="historyHtmlFields"
      :loading="loading"
      @filter="fetchEndpoints"
    >
      <template #actions="">
        <slot name="extraActions" />
        <v-btn
          size="small"
          icon="mdi-plus"
          color="primary"
          :title="$t('StudyEndpointsTable.add_endpoint')"
          :disabled="
            !checkPermission($roles.STUDY_WRITE) ||
            selectedStudyVersion !== null
          "
          @click.stop="showForm = true"
        />
      </template>
      <template #[`item.name`]="{ item }">
        <template v-if="item.endpoint_template">
          <NNParameterHighlighter
            :name="item.endpoint_template.name"
            default-color="orange"
          />
        </template>
        <template v-else-if="item.endpoint">
          <NNParameterHighlighter
            :name="item.endpoint.name"
            :show-prefix-and-postfix="false"
          />
        </template>
      </template>
      <template #[`item.actions`]="{ item }">
        <ActionsMenu
          :actions="actions"
          :item="item"
          :badge="actionsMenuBadge(item)"
        />
      </template>
      <template #[`item.start_date`]="{ item }">
        {{ $filters.date(item.start_date) }}
      </template>
      <template #[`item.endpoint.name`]="{ item }">
        <div class="d-flex">
          <NNParameterHighlighter
            v-if="item.endpoint"
            :name="item.endpoint.name"
            :show-prefix-and-postfix="false"
          />
          <NNParameterHighlighter
            v-else
            :name="item.endpoint_template.name"
            :show-prefix-and-postfix="false"
          />
          <v-tooltip
            v-if="item.endpoint && item.endpoint.name.length > 254"
            location="bottom"
          >
            <template #activator="{ props }">
              <v-icon
                class="mb-2 ml-1"
                v-bind="props"
                color="red"
                icon="mdi-alert-circle-outline"
              />
            </template>
            <span>{{ $t('StudyEndpointForm.endpoint_title_warning') }}</span>
          </v-tooltip>
        </div>
      </template>
      <template #[`item.study_objective.objective.name`]="{ item }">
        <NNParameterHighlighter
          v-if="item.study_objective"
          :name="item.study_objective.objective.name"
          :show-prefix-and-postfix="false"
        />
        <span v-else>{{ $t('StudyEndpointForm.select_later') }}</span>
      </template>
      <template #[`item.timeframe.name`]="{ item }">
        <NNParameterHighlighter
          v-if="item.timeframe"
          :name="item.timeframe.name"
          :show-prefix-and-postfix="false"
        />
        <span v-else>{{ $t('StudyEndpointForm.select_later') }}</span>
      </template>
    </NNTable>
    <v-dialog
      v-model="showForm"
      persistent
      fullscreen
      content-class="fullscreen-dialog"
    >
      <EndpointForm
        :study-endpoint="selectedStudyEndpoint"
        :current-study-endpoints="studyEndpoints"
        class="fullscreen-dialog"
        @close="closeForm"
        @added="fetchEndpoints"
      />
    </v-dialog>
    <EndpointEditForm
      :open="showEditForm"
      :study-endpoint="selectedStudyEndpoint"
      @close="closeEditForm"
      @updated="fetchEndpoints"
    />
    <v-dialog
      v-model="showHistory"
      persistent
      :fullscreen="$globals.historyDialogFullscreen"
      @keydown.esc="closeHistory"
    >
      <HistoryTable
        :title="studyEndpointHistoryTitle"
        :headers="headers"
        :items="endpointHistoryItems"
        :html-fields="historyHtmlFields"
        @close="closeHistory"
      />
    </v-dialog>
    <ConfirmDialog ref="confirm" width="600" />
    <SelectionOrderUpdateForm
      v-if="selectedStudyEndpoint"
      :initial-value="selectedStudyEndpoint.order"
      :open="showOrderForm"
      @close="closeOrderForm"
      @submit="submitOrder"
    />
    <v-snackbar v-model="snackbar" color="error" location="top">
      <v-icon class="mr-2"> mdi-alert </v-icon>
      {{ $t('StudyEndpointsTable.sort_help_msg') }}
    </v-snackbar>
  </div>
</template>

<script>
import study from '@/api/study'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import NNParameterHighlighter from '@/components/tools/NNParameterHighlighter.vue'
import EndpointEditForm from '@/components/studies/EndpointEditForm.vue'
import EndpointForm from '@/components/studies/EndpointForm.vue'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import statuses from '@/constants/statuses'
import NNTable from '@/components/tools/NNTable.vue'
import SelectionOrderUpdateForm from '@/components/studies/SelectionOrderUpdateForm.vue'
import filteringParameters from '@/utils/filteringParameters'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useStudiesEndpointsStore } from '@/stores/studies-endpoints'
import { computed } from 'vue'

export default {
  components: {
    ActionsMenu,
    NNParameterHighlighter,
    EndpointEditForm,
    EndpointForm,
    HistoryTable,
    ConfirmDialog,
    NNTable,
    SelectionOrderUpdateForm,
  },
  inject: ['eventBusEmit'],
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    const studiesEndpointsStore = useStudiesEndpointsStore()
    const accessGuard = useAccessGuard()
    return {
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
      selectedStudyVersion: computed(
        () => studiesGeneralStore.selectedStudyVersion
      ),
      fetchAllUnits: studiesGeneralStore.fetchAllUnits,
      fetchEndpointLevels: studiesGeneralStore.fetchEndpointLevels,
      fetchEndpointSubLevels: studiesGeneralStore.fetchEndpointSubLevels,
      studyEndpoints: computed(() => studiesEndpointsStore.studyEndpoints),
      total: computed(() => studiesEndpointsStore.total),
      fetchStudyEndpoints: studiesEndpointsStore.fetchStudyEndpoints,
      updateStudyEndpointTimeframeLatestVersion:
        studiesEndpointsStore.updateStudyEndpointTimeframeLatestVersion,
      updateStudyEndpointAcceptVersion:
        studiesEndpointsStore.updateStudyEndpointAcceptVersion,
      updateStudyEndpointEndpointLatestVersion:
        studiesEndpointsStore.updateStudyEndpointEndpointLatestVersion,
      deleteStudyEndpoint: studiesEndpointsStore.deleteStudyEndpoint,
      ...accessGuard,
    }
  },
  data() {
    return {
      abortConfirm: false,
      actions: [
        {
          label: this.$t(
            'StudyEndpointsTable.update_timeframe_version_retired'
          ),
          icon: 'mdi-alert-outline',
          iconColor: 'orange',
          condition: this.isTimeframeRetired || !this.selectedStudyVersion,
          accessRole: this.$roles.STUDY_WRITE,
        },
        {
          label: this.$t('StudyEndpointsTable.update_timeframe_version'),
          icon: 'mdi-bell-ring-outline',
          iconColorFunc: this.itemUpdateAborted,
          condition: this.timeframeNeedsUpdate || !this.selectedStudyVersion,
          click: this.updateTimeframeVersion,
          accessRole: this.$roles.STUDY_WRITE,
        },
        {
          label: this.$t('StudyEndpointsTable.update_endpoint_version_retired'),
          icon: 'mdi-alert-outline',
          iconColor: 'orange',
          condition: this.isEndpointRetired || !this.selectedStudyVersion,
          accessRole: this.$roles.STUDY_WRITE,
        },
        {
          label: this.$t('StudyEndpointsTable.update_endpoint_version'),
          icon: 'mdi-bell-ring-outline',
          iconColorFunc: this.itemUpdateAborted,
          condition: this.endpointNeedsUpdate || !this.selectedStudyVersion,
          click: this.updateEndpointVersion,
          accessRole: this.$roles.STUDY_WRITE,
        },
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil-outline',
          iconColor: 'primary',
          condition: () => !this.selectedStudyVersion,
          click: this.editStudyEndpoint,
          accessRole: this.$roles.STUDY_WRITE,
        },
        {
          label: this.$t('_global.change_order'),
          icon: 'mdi-pencil-outline',
          iconColor: 'primary',
          condition: () => !this.selectedStudyVersion,
          click: this.changeEndpointOrder,
          accessRole: this.$roles.STUDY_WRITE,
        },
        {
          label: this.$t('_global.delete'),
          icon: 'mdi-delete-outline',
          iconColor: 'error',
          condition: () => !this.selectedStudyVersion,
          click: this.deleteEndpoint,
          accessRole: this.$roles.STUDY_WRITE,
        },
        {
          label: this.$t('_global.history'),
          icon: 'mdi-history',
          click: this.openEndpointHistory,
        },
      ],
      actionsMenu: false,
      endpointHistoryItems: [],
      headers: [
        { title: '', key: 'actions', width: '5%' },
        {
          title: this.$t('StudyEndpointsTable.order'),
          key: 'order',
          width: '5%',
        },
        {
          title: this.$t('StudyEndpointsTable.endpoint_level'),
          key: 'endpoint_level.sponsor_preferred_name',
        },
        {
          title: this.$t('StudyEndpointsTable.endpoint_sub_level'),
          key: 'endpoint_sublevel.sponsor_preferred_name',
        },
        {
          title: this.$t('StudyEndpointsTable.endpoint_title'),
          key: 'endpoint.name',
          width: '25%',
        },
        {
          title: this.$t('StudyEndpointsTable.units'),
          key: 'units',
          width: '10%',
        },
        {
          title: this.$t('StudyEndpointsTable.time_frame'),
          key: 'timeframe.name',
          width: '25%',
        },
        {
          title: this.$t('StudyEndpointsTable.objective'),
          key: 'study_objective.objective.name',
          filteringName: 'study_objective.objective.name',
          width: '25%',
        },
        { title: this.$t('_global.modified'), key: 'start_date', width: '10%' },
        {
          title: this.$t('_global.modified_by'),
          key: 'user_initials',
          width: '10%',
        },
      ],
      historyHtmlFields: [
        'endpoint.name',
        'timeframe.name',
        'study_objective.objective.name',
      ],
      selectedStudyEndpoint: null,
      showEditForm: false,
      showForm: false,
      showHistory: false,
      showOrderForm: false,
      snackbar: false,
      sortBy: 'start_date',
      endpoints: [],
      loading: false
    }
  },
  computed: {
    filteredHeaders() {
      return this.headers.filter(
        (header) => header.show === true || header.show === undefined
      )
    },
    exportDataUrl() {
      return `studies/${this.selectedStudy.uid}/study-endpoints`
    },
    formatedStudyEndpoints() {
      return this.transformItems(this.studyEndpoints)
    },
    studyEndpointHistoryTitle() {
      if (this.selectedStudyEndpoint) {
        return this.$t('StudyEndpointsTable.study_endpoint_history_title', {
          studyEndpointUid: this.selectedStudyEndpoint.study_endpoint_uid,
        })
      }
      return ''
    },
  },
  mounted() {
    this.fetchAllUnits()
    this.fetchEndpointLevels()
    this.fetchEndpointSubLevels()
  },
  methods: {
    fetchEndpoints(filters, options, filtersUpdated) {
      this.loading = true
      const params = filteringParameters.prepareParameters(
        options,
        filters,
        filtersUpdated
      )
      params.studyUid = this.selectedStudy.uid
      this.fetchStudyEndpoints(params).then(() => {
        this.loading = false
      })
    },
    async fetchEndpointsHistory() {
      const resp = await study.getStudyEndpointsAuditTrail(
        this.selectedStudy.uid
      )
      return this.transformItems(resp.data)
    },
    actionsMenuBadge(item) {
      if (this.endpointNeedsUpdate(item) || this.timeframeNeedsUpdate(item)) {
        return {
          color: 'error',
          icon: 'mdi-bell-outline',
        }
      }
      if (
        !item.endpoint &&
        item.endpoint_template &&
        item.endpoint_template.parameters.length > 0
      ) {
        return {
          color: 'error',
          icon: 'mdi-exclamation',
        }
      }
      return null
    },
    timeframeNeedsUpdate(item) {
      if (item.latest_timeframe) {
        if (!this.isTimeframeRetired(item)) {
          return item.timeframe.version !== item.latest_timeframe.version
        }
      }
      return false
    },
    isTimeframeRetired(item) {
      if (item.latest_timeframe) {
        return item.latest_timeframe.status === statuses.RETIRED
      }
      return false
    },
    async updateTimeframeVersion(item) {
      const options = {
        type: 'warning',
        width: 1000,
        cancelLabel: this.$t('StudyObjectivesTable.keep_old_version'),
        agreeLabel: this.$t('StudyObjectivesTable.use_new_version'),
      }
      const message =
        this.$t('StudyEndpointsTable.update_timeframe_version_alert') +
        ' ' +
        this.$t('StudyEndpointsTable.previous_version') +
        ' ' +
        item.timeframe.name_plain +
        ' ' +
        this.$t('StudyEndpointsTable.new_version') +
        ' ' +
        item.latest_timeframe.name_plain

      if (await this.$refs.confirm.open(message, options)) {
        const args = {
          studyUid: item.study_uid,
          studyEndpointUid: item.study_endpoint_uid,
        }
        this.updateStudyEndpointTimeframeLatestVersion(args).then(() => {
          this.eventBusEmit('notification', {
            msg: this.$t('StudyObjectivesTable.update_version_successful'),
          })
        })
      } else {
        this.abortConfirm = true
        const args = {
          studyUid: item.study_uid,
          studyEndpointUid: item.study_endpoint_uid,
        }
        this.updateStudyEndpointAcceptVersion(args)
      }
    },
    endpointNeedsUpdate(item) {
      if (item.latest_endpoint) {
        if (!this.isEndpointRetired(item)) {
          return item.endpoint.version !== item.latest_endpoint.version
        }
      }
      return false
    },
    isEndpointRetired(item) {
      if (item.latest_endpoint) {
        return item.latest_endpoint.status === statuses.RETIRED
      }
      return false
    },
    itemUpdateAborted(item) {
      return item.acceptedVersion ? '' : 'error'
    },
    async updateEndpointVersion(item) {
      const options = {
        type: 'warning',
        width: 1200,
        cancelLabel: this.$t('StudyObjectivesTable.keep_old_version'),
        agreeLabel: this.$t('StudyObjectivesTable.use_new_version'),
      }
      const message =
        this.$t('StudyEndpointsTable.update_endpoint_version_alert') +
        ' ' +
        this.$t('StudyEndpointsTable.previous_version') +
        ' ' +
        item.endpoint.name_plain +
        ' ' +
        this.$t('StudyEndpointsTable.new_version') +
        ' ' +
        item.latest_endpoint.name_plain

      if (await this.$refs.confirm.open(message, options)) {
        const args = {
          studyUid: item.study_uid,
          studyEndpointUid: item.study_endpoint_uid,
        }
        this.updateStudyEndpointEndpointLatestVersion(args).then(() => {
          this.eventBusEmit('notification', {
            msg: this.$t('StudyEndpointsTable.update_version_successful'),
          })
        })
      } else {
        this.abortConfirm = true
        const args = {
          studyUid: item.study_uid,
          studyEndpointUid: item.study_endpoint_uid,
        }
        await this.updateStudyEndpointAcceptVersion(args)
      }
    },
    closeForm() {
      this.showForm = false
      this.selectedStudyEndpoint = null
      this.fetchEndpoints()
    },
    closeEditForm() {
      this.showEditForm = false
      this.selectedStudyEndpoint = null
    },
    getHeaderLabel(value) {
      return this.headers.filter((item) => item.value === value)[0].text
    },
    editStudyEndpoint(studyEndpoint) {
      this.selectedStudyEndpoint = studyEndpoint
      this.showEditForm = true
    },
    displayUnits(units) {
      const unitNames = units.units.map((unit) => unit.name)
      if (unitNames.length > 1) {
        return unitNames.join(` ${units.separator} `)
      }
      return unitNames[0]
    },
    async deleteEndpoint(studyEndpoint) {
      const options = { type: 'warning' }
      const endpoint = studyEndpoint.endpoint
        ? studyEndpoint.endpoint.name_plain
        : '(unnamed)'

      if (
        await this.$refs.confirm.open(
          this.$t('StudyEndpointsTable.confirm_delete', { endpoint }),
          options
        )
      ) {
        // Make sure to set current studyObjective so the list of
        // endpoints is updated after deletion
        this.deleteStudyEndpoint({
          studyUid: this.selectedStudy.uid,
          studyEndpointUid: studyEndpoint.study_endpoint_uid,
        }).then(() => {
          this.eventBusEmit('notification', {
            msg: this.$t('StudyEndpointsTable.delete_success'),
          })
          this.fetchEndpoints()
        })
      }
    },
    closeHistory() {
      this.selectedStudyEndpoint = null
      this.showHistory = false
    },
    async openEndpointHistory(studyEndpoint) {
      this.selectedStudyEndpoint = studyEndpoint
      const resp = await study.getStudyEndpointAuditTrail(
        this.selectedStudy.uid,
        studyEndpoint.study_endpoint_uid
      )
      this.endpointHistoryItems = this.transformItems(resp.data)
      this.showHistory = true
    },
    submitOrder(value) {
      study
        .updateStudyEndpointOrder(
          this.selectedStudyEndpoint.study_uid,
          this.selectedStudyEndpoint.study_endpoint_uid,
          value
        )
        .then(() => {
          this.fetchEndpoints()
          this.closeOrderForm()
          this.eventBusEmit('notification', {
            msg: this.$t('_global.order_updated'),
          })
        })
    },
    changeEndpointOrder(endpoint) {
      this.selectedStudyEndpoint = endpoint
      this.showOrderForm = true
    },
    closeOrderForm() {
      this.showOrderForm = false
    },
    transformItems(items) {
      const result = []
      for (const item of items) {
        const newItem = { ...item }
        if (item.endpoint_units && item.endpoint_units.units) {
          newItem.units = this.displayUnits(item.endpoint_units)
        }
        result.push(newItem)
      }
      return result
    },
  },
}
</script>
<style scoped>
.roundChip {
  width: 25px;
  justify-content: space-evenly;
}
</style>
