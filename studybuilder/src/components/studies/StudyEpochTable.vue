<template>
  <div>
    <NNTable
      :headers="headers"
      :default-headers="headers"
      :items="studyEpochs"
      item-value="uid"
      :export-data-url="exportDataUrl"
      export-object-label="StudyEpochs"
      :items-length="studyEpochs.length"
      :column-data-resource="`studies/${selectedStudy.uid}/study-epochs`"
      :history-data-fetcher="fetchEpochsHistory"
      :history-title="$t('StudyEpochTable.global_history_title')"
      @filter="fetchEpochs"
    >
      <template #[`item.color_hash`]="{ item }">
        <v-chip
          :data-cy="'color=' + item.color_hash"
          :color="item.color_hash"
          size="small"
          variant="flat"
        >
          <span>&nbsp;</span>
          <span>&nbsp;</span>
        </v-chip>
      </template>
      <template #[`item.epoch_name`]="{ item }">
        <router-link
          :to="{
            name: 'StudyEpochOverview',
            params: { study_id: selectedStudy.uid, id: item.uid },
          }"
        >
          {{ item.epoch_name }}
        </router-link>
      </template>
      <template #[`item.actions`]="{ item }">
        <ActionsMenu :actions="actions" :item="item" />
      </template>
      <template #actions="">
        <v-btn
          data-cy="create-epoch"
          size="small"
          color="primary"
          :title="$t('StudyEpochForm.add_title')"
          :disabled="
            !checkPermission($roles.STUDY_WRITE) ||
            selectedStudyVersion !== null
          "
          icon="mdi-plus"
          @click="createEpoch()"
        />
      </template>
    </NNTable>
    <StudyEpochForm
      :open="showForm"
      :study-epoch="selectedStudyEpoch"
      @close="closeForm"
    />
    <v-dialog
      v-model="showEpochHistory"
      persistent
      :fullscreen="$globals.historyDialogFullscreen"
      @keydown.esc="closeEpochHistory"
    >
      <HistoryTable
        :title="studyEpochHistoryTitle"
        :headers="headers"
        :items="epochHistoryItems"
        @close="closeEpochHistory"
      />
    </v-dialog>
    <SelectionOrderUpdateForm
      v-if="selectedStudyEpoch"
      ref="orderForm"
      :initial-value="selectedStudyEpoch.order"
      :open="showOrderForm"
      @close="closeOrderForm"
      @submit="submitOrder"
    />
  </div>
</template>

<script>
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import NNTable from '@/components/tools/NNTable.vue'
import StudyEpochForm from './StudyEpochForm.vue'
import epochs from '@/api/studyEpochs'
import filteringParameters from '@/utils/filteringParameters'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useEpochsStore } from '@/stores/studies-epochs'
import { useUnitsStore } from '@/stores/units'
import { computed } from 'vue'
import SelectionOrderUpdateForm from '@/components/studies/SelectionOrderUpdateForm.vue'

export default {
  components: {
    ActionsMenu,
    NNTable,
    StudyEpochForm,
    HistoryTable,
    SelectionOrderUpdateForm,
  },
  inject: ['eventBusEmit'],
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    const epochsStore = useEpochsStore()
    const unitsStore = useUnitsStore()
    return {
      selectedStudy: studiesGeneralStore.selectedStudy,
      selectedStudyVersion: studiesGeneralStore.selectedStudyVersion,
      studyEpochs: computed(() => epochsStore.studyEpochs),
      fetchUnits: unitsStore.fetchUnits,
      fetchFilteredStudyEpochs: epochsStore.fetchFilteredStudyEpochs,
      deleteStudyEpoch: epochsStore.deleteStudyEpoch,
      ...useAccessGuard(),
    }
  },
  data() {
    return {
      actions: [
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil-outline',
          iconColor: 'primary',
          condition: (item) =>
            item.possible_actions.find((action) => action === 'edit') &&
            !this.selectedStudyVersion,
          click: this.editEpoch,
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
          condition: (item) =>
            item.possible_actions.find((action) => action === 'delete') &&
            !this.selectedStudyVersion,
          click: this.deleteEpoch,
          accessRole: this.$roles.STUDY_WRITE,
        },
        {
          label: this.$t('_global.history'),
          icon: 'mdi-history',
          click: this.openEpochHistory,
        },
      ],
      headers: [
        { title: '', key: 'actions', width: '5%' },
        { title: this.$t('StudyEpochTable.number'), key: 'order', width: '5%' },
        { title: this.$t('StudyEpochTable.name'), key: 'epoch_name' },
        { title: this.$t('StudyEpochTable.type'), key: 'epoch_type_name' },
        {
          title: this.$t('StudyEpochTable.sub_type'),
          key: 'epoch_subtype_name',
        },
        { title: this.$t('StudyEpochTable.start_rule'), key: 'start_rule' },
        { title: this.$t('StudyEpochTable.end_rule'), key: 'end_rule' },
        {
          title: this.$t('StudyEpochTable.description'),
          key: 'description',
          width: '20%',
        },
        {
          title: this.$t('StudyEpochTable.visit_count'),
          key: 'study_visit_count',
        },
        { title: this.$t('StudyEpochTable.colour'), key: 'color_hash' },
      ],
      defaultColums: [
        { title: '', key: 'actions', width: '5%' },
        { title: this.$t('StudyEpochTable.number'), key: 'order', width: '3%' },
        { title: this.$t('StudyEpochTable.name'), key: 'epoch_name' },
        {
          title: this.$t('StudyEpochTable.sub_type'),
          key: 'epoch_subtype_name',
        },
        { title: this.$t('StudyEpochTable.type'), key: 'epoch_type_name' },
        { title: this.$t('StudyEpochTable.start_rule'), key: 'start_rule' },
        { title: this.$t('StudyEpochTable.end_rule'), key: 'end_rule' },
        { title: this.$t('StudyEpochTable.description'), key: 'description' },
      ],
      selectedStudyEpoch: null,
      showForm: false,
      showEpochHistory: false,
      epochHistoryItems: [],
      componentKey: 0,
      showStudyEpochsHistory: false,
      showOrderForm: false,
      selectMode: false,
      total: 0,
    }
  },
  computed: {
    exportDataUrl() {
      return `studies/${this.selectedStudy.uid}/study-epochs`
    },
    studyEpochHistoryTitle() {
      if (this.selectedStudyEpoch) {
        return this.$t('StudyEpochTable.study_epoch_history_title', {
          epochUid: this.selectedStudyEpoch.uid,
        })
      }
      return ''
    },
  },
  mounted() {
    this.fetchUnits()
  },
  methods: {
    async fetchEpochsHistory() {
      const resp = await epochs.getStudyEpochsVersions(this.selectedStudy.uid)
      return resp.data
    },
    fetchEpochs(filters, options, filtersUpdated) {
      const params = filteringParameters.prepareParameters(
        options,
        filters,
        filtersUpdated
      )
      params.study_uid = this.selectedStudy.uid
      this.fetchFilteredStudyEpochs(params)
    },
    createMapping(codelist) {
      const returnValue = {}
      codelist.forEach((item) => {
        returnValue[item.term_uid] = item.sponsor_preferred_name
      })
      return returnValue
    },
    editEpoch(item) {
      this.selectedStudyEpoch = item
      this.showForm = true
    },
    submitOrder(value) {
      epochs
        .reorderStudyEpoch(
          this.selectedStudyEpoch.study_uid,
          this.selectedStudyEpoch.uid,
          parseInt(value) - 1
        )
        .then(() => {
          this.fetchEpochs()
          this.closeOrderForm()
          this.eventBusEmit('notification', {
            msg: this.$t('_global.order_updated'),
          })
        })
        .catch((err) => {
          console.log(err)
          this.fetchEpochs()
        })
    },
    changeOrder(studyEpoch) {
      this.selectedStudyEpoch = studyEpoch
      this.showOrderForm = true
    },
    closeOrderForm() {
      this.showOrderForm = false
    },
    createEpoch() {
      this.selectedStudyEpoch = null
      this.showForm = true
    },
    closeForm() {
      this.selectedStudyEpoch = null
      this.showForm = false
    },
    deleteEpoch(item) {
      if (item.study_visit_count > 0) {
        const epoch = item.epoch_name
        this.eventBusEmit('notification', {
          type: 'warning',
          msg: this.$t('StudyEpochTable.epoch_linked_to_visits_warning', {
            epoch,
          }),
        })
        return
      }
      this.deleteStudyEpoch({
        studyUid: this.selectedStudy.uid,
        studyEpochUid: item.uid,
      }).then(() => {
        this.eventBusEmit('notification', {
          msg: this.$t('StudyEpochTable.delete_success'),
        })
      })
    },
    async openEpochHistory(epoch) {
      this.selectedStudyEpoch = epoch
      const resp = await epochs.getStudyEpochVersions(
        this.selectedStudy.uid,
        epoch.uid
      )
      this.epochHistoryItems = resp.data
      this.showEpochHistory = true
    },
    closeEpochHistory() {
      this.selectedStudyEpoch = null
      this.showEpochHistory = false
    },
  },
}
</script>
