<template>
  <div>
    <NNTable
      :headers="headers"
      :items="studyElements"
      :items-length="total"
      :sort-desc="sortDesc"
      export-object-label="StudyElements"
      item-value="element_uid"
      :export-data-url="exportDataUrl"
      :column-data-resource="`studies/${selectedStudy.uid}/study-elements`"
      :history-data-fetcher="fetchElementsHistory"
      :history-title="$t('StudyElements.global_history_title')"
      @filter="getStudyElements"
    >
      <template #[`item.name`]="{ item }">
        <router-link
          :to="{
            name: 'StudyElementOverview',
            params: { study_id: selectedStudy.uid, id: item.element_uid },
          }"
        >
          {{ item.name }}
        </router-link>
      </template>
      <template #[`item.element_colour`]="{ item }">
        <v-chip
          :data-cy="'color=' + item.element_colour"
          :color="item.element_colour"
          size="small"
          variant="flat"
        >
          <span>&nbsp;</span>
          <span>&nbsp;</span>
        </v-chip>
      </template>
      <template #[`item.start_date`]="{ item }">
        {{ $filters.date(item.start_date) }}
      </template>
      <template #[`item.actions`]="{ item }">
        <div class="pr-0 mr-0">
          <ActionsMenu :actions="actions" :item="item" />
        </div>
      </template>
      <template #[`item.element_type`]="{ item }">
        {{ getElementType(item) }}
      </template>
      <template #actions="">
        <v-btn
          size="small"
          color="primary"
          :title="$t('StudyElements.add_element')"
          :disabled="
            !checkPermission($roles.STUDY_WRITE) ||
            selectedStudyVersion !== null
          "
          icon="mdi-plus"
          @click.stop="showForm = true"
        />
      </template>
    </NNTable>
    <StudyElementsForm
      :open="showForm"
      :metadata="activeElement"
      @close="closeForm"
    />
    <v-dialog
      v-model="showElementHistory"
      persistent
      :fullscreen="$globals.historyDialogFullscreen"
      @keydown.esc="closeElementHistory"
    >
      <HistoryTable
        :title="studyElementHistoryTitle"
        :headers="headers"
        :items="elementHistoryItems"
        @close="closeElementHistory"
      />
    </v-dialog>
    <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
    <SelectionOrderUpdateForm
      v-if="selectedElement"
      ref="orderForm"
      :initial-value="selectedElement.order"
      :open="showOrderForm"
      @close="closeOrderForm"
      @submit="submitOrder"
    />
  </div>
</template>

<script>
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import NNTable from '@/components/tools/NNTable.vue'
import StudyElementsForm from './StudyElementsForm.vue'
import arms from '@/api/arms'
import terms from '@/api/controlledTerminology/terms'
import filteringParameters from '@/utils/filteringParameters'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useUnitsStore } from '@/stores/units'
import SelectionOrderUpdateForm from '@/components/studies/SelectionOrderUpdateForm.vue'

export default {
  components: {
    ConfirmDialog,
    NNTable,
    StudyElementsForm,
    ActionsMenu,
    HistoryTable,
    SelectionOrderUpdateForm,
  },
  inject: ['eventBusEmit'],
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    const unitsStore = useUnitsStore()
    return {
      ...useAccessGuard(),
      fetchUnits: unitsStore.fetchUnits,
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
          click: this.editStudyElement,
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
          click: this.deleteStudyElement,
          accessRole: this.$roles.STUDY_WRITE,
        },
        {
          label: this.$t('_global.history'),
          icon: 'mdi-history',
          click: this.openElementHistory,
        },
      ],
      headers: [
        { title: '', key: 'actions', width: '5%' },
        { title: '#', key: 'order', width: '5%' },
        {
          title: this.$t('StudyElements.el_type'),
          key: 'element_type.sponsor_preferred_name',
        },
        {
          title: this.$t('StudyElements.el_sub_type'),
          key: 'element_subtype.sponsor_preferred_name',
        },
        { title: this.$t('StudyElements.el_name'), key: 'name' },
        { title: this.$t('StudyElements.el_short_name'), key: 'short_name' },
        { title: this.$t('StudyElements.el_start_rule'), key: 'start_rule' },
        { title: this.$t('StudyElements.el_end_rule'), key: 'end_rule' },
        { title: this.$t('StudyElements.colour'), key: 'element_colour' },
        { title: this.$t('_global.description'), key: 'description' },
        { title: this.$t('_global.modified'), key: 'start_date' },
        { title: this.$t('_global.modified_by'), key: 'user_initials' },
      ],
      showForm: false,
      sortBy: 'name',
      sortDesc: false,
      studyElements: [],
      activeElement: null,
      elementTypes: [],
      total: 0,
      showElementHistory: false,
      showOrderForm: false,
      elementHistoryItems: [],
      selectedElement: null,
      showStudyElementsHistory: false,
    }
  },
  computed: {
    exportDataUrl() {
      return `studies/${this.selectedStudy.uid}/study-elements`
    },
    studyElementHistoryTitle() {
      if (this.selectedElement) {
        return this.$t('StudyElements.study_element_history_title', {
          elementUid: this.selectedElement.element_uid,
        })
      }
      return ''
    },
  },
  mounted() {
    this.fetchUnits()
    terms.getByCodelist('elementTypes').then((resp) => {
      this.elementTypes = resp.data.items
    })
  },
  methods: {
    async fetchElementsHistory() {
      const resp = await arms.getStudyElementsVersions(this.selectedStudy.uid)
      return resp.data
    },
    getStudyElements(filters, options, filtersUpdated) {
      const params = filteringParameters.prepareParameters(
        options,
        filters,
        filtersUpdated
      )
      params.study_uid = this.selectedStudy.uid
      arms.getStudyElements(this.selectedStudy.uid, params).then((resp) => {
        this.studyElements = resp.data.items
        this.total = resp.data.total
      })
    },
    async deleteStudyElement(element) {
      const options = { type: 'warning' }
      let msg
      const context = { element: element.name }
      if (element.study_compound_dosing_count) {
        context.compoundDosings = element.study_compound_dosing_count
        msg = this.$t('StudyElements.confirm_delete_cascade', context)
      } else {
        msg = this.$t('StudyElements.confirm_delete', context)
      }
      if (!(await this.$refs.confirm.open(msg, options))) {
        return
      }
      arms
        .deleteStudyElement(this.selectedStudy.uid, element.element_uid)
        .then(() => {
          this.eventBusEmit('notification', {
            msg: this.$t('StudyElements.el_deleted'),
          })
          this.getStudyElements()
        })
    },
    editStudyElement(item) {
      this.activeElement = item
      this.showForm = true
    },
    closeForm() {
      this.activeElement = null
      this.showForm = false
      this.getStudyElements()
    },
    async openElementHistory(element) {
      this.selectedElement = element
      const resp = await arms.getStudyElementVersions(
        this.selectedStudy.uid,
        element.element_uid
      )
      this.elementHistoryItems = resp.data
      this.showElementHistory = true
    },
    closeElementHistory() {
      this.showElementHistory = false
      this.selectedElement = null
    },
    getElementType(item) {
      const type = this.elementTypes.filter(
        (el) => el.term_uid === item.code
      )[0]
      if (item.code && type) {
        return type.name.sponsor_preferred_name
      }
    },
    submitOrder(value) {
      arms
        .updateElementOrder(
          this.selectedElement.study_uid,
          this.selectedElement.element_uid,
          value
        )
        .then(() => {
          this.getStudyElements()
          this.closeOrderForm()
          this.eventBusEmit('notification', {
            msg: this.$t('_global.order_updated'),
          })
        })
    },
    changeOrder(studyElement) {
      this.selectedElement = studyElement
      this.showOrderForm = true
    },
    closeOrderForm() {
      this.showOrderForm = false
    },
  },
}
</script>
