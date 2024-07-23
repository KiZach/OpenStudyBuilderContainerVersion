<template>
  <div>
    <NNTable
      :headers="headers"
      :items="diseaseMilestones"
      item-value="uid"
      fixed-header
      :items-length="total"
      :history-data-fetcher="fetchDiseaseMilestonesHistory"
      :history-title="$t('DiseaseMilestoneTable.global_history_title')"
      export-object-label="DiseaseMilestones"
      :export-data-url="exportDataUrl"
      :column-data-resource="exportDataUrl"
      disable-filtering
      @filter="fetchDiseaseMilestones"
    >
      <template #actions="">
        <v-btn
          data-cy="create-disease-milestone"
          size="small"
          color="primary"
          :title="$t('DiseaseMilestoneForm.add_title')"
          :disabled="
            !checkPermission($roles.STUDY_WRITE) ||
            selectedStudyVersion !== null
          "
          icon="mdi-plus"
          @click="createDiseaseMilestone()"
        />
      </template>
      <template #[`item.actions`]="{ item }">
        <div class="pr-0 mr-0">
          <ActionsMenu :actions="actions" :item="item" />
        </div>
      </template>
      <template #[`item.repetition_indicator`]="{ item }">
        {{ $filters.yesno(item.repetition_indicator) }}
      </template>
      <template #[`item.start_date`]="{ item }">
        {{ $filters.date(item.start_date) }}
      </template>
    </NNTable>
    <DiseaseMilestoneForm
      :open="showForm"
      :disease-milestone="selectedDiseaseMilestone"
      @close="closeForm"
    />
    <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
    <v-dialog
      v-model="showHistory"
      persistent
      :fullscreen="$globals.historyDialogFullscreen"
      @keydown.esc="closeHistory"
    >
      <HistoryTable
        :title="diseaseMilestoneHistoryTitle"
        :headers="headers"
        :items="historyItems"
        @close="closeHistory"
      />
    </v-dialog>
    <SelectionOrderUpdateForm
      v-if="selectedDiseaseMilestone"
      ref="orderForm"
      :initial-value="selectedDiseaseMilestone.order"
      :open="showOrderForm"
      @close="closeOrderForm"
      @submit="submitOrder"
    />
  </div>
</template>

<script>
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import dataFormating from '@/utils/dataFormating'
import DiseaseMilestoneForm from './DiseaseMilestoneForm.vue'
import filteringParameters from '@/utils/filteringParameters'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import NNTable from '@/components/tools/NNTable.vue'
import SelectionOrderUpdateForm from '@/components/studies/SelectionOrderUpdateForm.vue'
import study from '@/api/study'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesGeneralStore } from '@/stores/studies-general'

export default {
  components: {
    ActionsMenu,
    ConfirmDialog,
    DiseaseMilestoneForm,
    HistoryTable,
    NNTable,
    SelectionOrderUpdateForm,
  },
  inject: ['eventBusEmit'],
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    return {
      ...useAccessGuard(),
      selectedStudy: studiesGeneralStore.selectedStudy,
      selectedStudyVersion: studiesGeneralStore.selectedStudyVersion,
    }
  },
  data() {
    return {
      actions: [
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil-outline',
          iconColor: 'primary',
          condition: () => !this.selectedStudyVersion,
          click: this.editDiseaseMilestone,
          accessRole: this.$roles.STUDY_WRITE,
        },
        {
          label: this.$t('_global.change_order'),
          icon: 'mdi-pencil-outline',
          iconColor: 'primary',
          condition: () => !this.selectedStudyVersion,
          click: this.changeOrder,
          accessRole: this.$roles.STUDY_WRITE,
        },
        {
          label: this.$t('_global.delete'),
          icon: 'mdi-delete-outline',
          iconColor: 'error',
          condition: () => !this.selectedStudyVersion,
          click: this.deleteDiseaseMilestone,
          accessRole: this.$roles.STUDY_WRITE,
        },
        {
          label: this.$t('_global.history'),
          icon: 'mdi-history',
          click: this.openHistory,
        },
      ],
      diseaseMilestones: [],
      headers: [
        { title: '', key: 'actions', width: '5%' },
        { title: '#', key: 'order', width: '5%' },
        {
          title: this.$t('DiseaseMilestone.disease_milestone_type'),
          key: 'disease_milestone_type_named',
        },
        {
          title: this.$t('_global.definition'),
          key: 'disease_milestone_type_definition',
        },
        {
          title: this.$t('DiseaseMilestone.repetition_indicator'),
          key: 'repetition_indicator',
        },
        { title: this.$t('_global.modified'), key: 'start_date' },
        { title: this.$t('_global.modified_by'), key: 'user_initials' },
      ],
      historyItems: [],
      selectedDiseaseMilestone: null,
      showForm: false,
      showHistory: false,
      showOrderForm: false,
      total: 0,
    }
  },
  computed: {
    exportDataUrl() {
      return `studies/${this.selectedStudy.uid}/study-disease-milestones`
    },
    diseaseMilestoneHistoryTitle() {
      if (this.selectedDiseaseMilestone) {
        return this.$t('DiseaseMilestoneTable.item_history_title', {
          uid: this.selectedDiseaseMilestone.uid,
        })
      }
      return ''
    },
  },
  methods: {
    fetchDiseaseMilestones(filters, options, filtersUpdated) {
      const params = filteringParameters.prepareParameters(
        options,
        filters,
        filtersUpdated
      )
      study
        .getStudyDiseaseMilestones(this.selectedStudy.uid, params)
        .then((resp) => {
          this.diseaseMilestones = resp.data.items
          this.total = resp.data.total
        })
    },
    formatItems(items) {
      const result = []
      for (const item of items) {
        item.repetition_indicator = dataFormating.yesno(
          item.repetition_indicator
        )
        result.push(item)
      }
      return result
    },
    async fetchDiseaseMilestonesHistory() {
      const resp = await study.getStudyDiseaseMilestonesAuditTrail(
        this.selectedStudy.uid
      )
      return this.formatItems(resp.data)
    },
    createDiseaseMilestone() {
      this.selectedDiseaseMilestone = null
      this.showForm = true
    },
    closeForm() {
      this.showForm = false
      this.fetchDiseaseMilestones()
    },
    editDiseaseMilestone(item) {
      this.selectedDiseaseMilestone = item
      this.showForm = true
    },
    async deleteDiseaseMilestone(item) {
      const options = { type: 'warning' }
      const context = { name: item.disease_milestone_type_named }
      const msg = this.$t('DiseaseMilestoneTable.confirm_delete', context)
      if (!(await this.$refs.confirm.open(msg, options))) {
        return
      }
      study
        .deleteStudyDiseaseMilestone(this.selectedStudy.uid, item.uid)
        .then(() => {
          this.eventBusEmit('notification', {
            msg: this.$t('DiseaseMilestoneTable.delete_success'),
          })
          this.fetchDiseaseMilestones()
        })
    },
    async openHistory(item) {
      this.selectedDiseaseMilestone = item
      const resp = await study.getStudyDiseaseMilestoneAuditTrail(
        this.selectedStudy.uid,
        item.uid
      )
      this.historyItems = this.formatItems(resp.data)
      this.showHistory = true
    },
    closeHistory() {
      this.showHistory = false
    },
    submitOrder(value) {
      study
        .updateStudyDiseaseMilestoneOrder(
          this.selectedDiseaseMilestone.study_uid,
          this.selectedDiseaseMilestone.uid,
          value
        )
        .then(() => {
          this.fetchDiseaseMilestones()
          this.closeOrderForm()
          this.eventBusEmit('notification', {
            msg: this.$t('_global.order_updated'),
          })
        })
    },
    changeOrder(diseaseMilestone) {
      this.selectedDiseaseMilestone = diseaseMilestone
      this.showOrderForm = true
    },
    closeOrderForm() {
      this.showOrderForm = false
    },
  },
}
</script>
