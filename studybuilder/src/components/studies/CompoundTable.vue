<template>
  <NNTable
    :headers="headers"
    :items="formatedStudyCompounds"
    item-value="study_compound_uid"
    export-object-label="StudyCompounds"
    :export-data-url="exportDataUrl"
    :column-data-resource="`studies/${selectedStudy.uid}/study-compounds`"
    :items-length="studiesCompoundsStore.studyCompoundTotal"
    :history-data-fetcher="fetchCompoundsHistory"
    :history-title="$t('StudyCompoundTable.global_history_title')"
    @filter="fetchCompounds"
  >
    <template #actions="">
      <v-btn
        data-cy="add-study-compound"
        size="small"
        color="primary"
        :title="$t('StudyCompoundForm.add_title')"
        :disabled="
          !checkPermission($roles.STUDY_WRITE) || selectedStudyVersion !== null
        "
        icon="mdi-plus"
        @click.stop="showForm = true"
      />
    </template>
    <template #[`item.actions`]="{ item }">
      <ActionsMenu :actions="actions" :item="item" />
    </template>
    <template #[`item.overview`]="{ item }">
      <router-link
        :to="{
          name: 'StudyCompoundOverview',
          params: { study_id: selectedStudy.uid, id: item.study_compound_uid },
        }"
      >
        <v-icon>mdi-eye-outline</v-icon>
      </router-link>
    </template>
  </NNTable>
  <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
  <v-dialog
    v-model="showForm"
    persistent
    fullscreen
    content-class="fullscreen-dialog"
  >
    <CompoundForm
      :study-compound="selectedStudyCompound"
      @added="fetchCompounds"
      @close="closeForm"
    />
  </v-dialog>
  <v-dialog
    v-model="showCompoundHistory"
    persistent
    :fullscreen="$globals.historyDialogFullscreen"
    @keydown.esc="closeStudyCompoundHistory"
  >
    <HistoryTable
      :title="studyCompoundHistoryTitle"
      :headers="headers"
      :items="compoundHistoryItems"
      @close="closeStudyCompoundHistory"
    />
  </v-dialog>
</template>

<script>
import { computed } from 'vue'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import CompoundForm from './CompoundForm.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import dataFormating from '@/utils/dataFormating'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import filteringParameters from '@/utils/filteringParameters'
import NNTable from '@/components/tools/NNTable.vue'
import study from '@/api/study'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesCompoundsStore } from '@/stores/studies-compounds'
import { useStudiesGeneralStore } from '@/stores/studies-general'

export default {
  components: {
    ActionsMenu,
    CompoundForm,
    ConfirmDialog,
    HistoryTable,
    NNTable,
  },
  inject: ['eventBusEmit'],
  setup() {
    const accessGuard = useAccessGuard()
    const studiesCompoundsStore = useStudiesCompoundsStore()
    const studiesGeneralStore = useStudiesGeneralStore()
    return {
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
      selectedStudyVersion: computed(
        () => studiesGeneralStore.selectedStudyVersion
      ),
      nullValues: computed(() => studiesGeneralStore.nullValues),
      studiesCompoundsStore,
      ...accessGuard,
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
          click: this.editStudyCompound,
          accessRole: this.$roles.STUDY_WRITE,
        },
        {
          label: this.$t('_global.delete'),
          icon: 'mdi-delete-outline',
          iconColor: 'error',
          condition: () => !this.selectedStudyVersion,
          click: this.deleteStudyCompound,
          accessRole: this.$roles.STUDY_WRITE,
        },
        {
          label: this.$t('_global.history'),
          icon: 'mdi-history',
          click: this.openStudyCompoundHistory,
        },
      ],
      compoundHistoryItems: [],
      headers: [
        { title: '', key: 'actions', width: '5%' },
        { title: '#', key: 'order' },
        { title: '', key: 'overview', width: '5%' },
        {
          title: this.$t('StudyCompoundTable.type_of_treatment'),
          key: 'type_of_treatment.name',
        },
        {
          title: this.$t('StudyCompoundTable.reason_for_missing'),
          key: 'reason_for_missing_null_value.name',
        },
        { title: this.$t('StudyCompoundTable.compound'), key: 'compound.name' },
        {
          title: this.$t('StudyCompoundTable.sponsor_compound'),
          key: 'compound.is_sponsor_compound',
        },
        {
          title: this.$t('StudyCompoundTable.is_name_inn'),
          key: 'compound.is_name_inn',
        },
        { title: this.$t('StudyCompoundTable.substance'), key: 'substances' },
        {
          title: this.$t('StudyCompoundTable.pharma_class'),
          key: 'pharmacological_classes',
        },
        {
          title: this.$t('StudyCompoundTable.compound_alias'),
          key: 'compound_alias.name',
        },
        {
          title: this.$t('StudyCompoundTable.preferred_alias'),
          key: 'compound_alias.is_preferred_synonym',
        },
        {
          title: this.$t('StudyCompoundTable.strength'),
          key: 'strength_value',
        },
        {
          title: this.$t('StudyCompoundTable.dosage_form'),
          key: 'dosage_form.name',
        },
        {
          title: this.$t('StudyCompoundTable.route_of_admin'),
          key: 'route_of_administration.name',
        },
        {
          title: this.$t('StudyCompoundTable.dispensed_in'),
          key: 'dispensed_in.name',
        },
        { title: this.$t('StudyCompoundTable.device'), key: 'device.name' },
        {
          title: this.$t('StudyCompoundTable.half_life'),
          key: 'compound.half_life',
        },
        { title: this.$t('StudyCompoundTable.lag_time'), key: 'lag_times' },
        {
          title: this.$t('StudyCompoundTable.nnc_number_long'),
          key: 'nnc_long_number',
        },
        {
          title: this.$t('StudyCompoundTable.nnc_number_short'),
          key: 'nnc_short_number',
        },
        {
          title: this.$t('StudyCompoundTable.analyte_number'),
          key: 'analyte_number',
        },
        {
          title: this.$t('StudyCompoundTable.compound_definition'),
          key: 'compound.definition',
        },
        {
          title: this.$t('StudyCompoundTable.alias_definition'),
          key: 'compound_alias.definition',
        },
      ],
      selectedStudyCompound: null,
      showCompoundHistory: false,
      showForm: false,
    }
  },
  computed: {
    exportDataUrl() {
      return `studies/${this.selectedStudy.uid}/study-compounds`
    },
    studyCompoundHistoryTitle() {
      if (this.selectedStudyCompound) {
        return this.$t('StudyCompoundTable.study_compound_history_title', {
          studyCompoundUid: this.selectedStudyCompound.study_compound_uid,
        })
      }
      return ''
    },
    formatedStudyCompounds() {
      return this.transformItems(this.studiesCompoundsStore.studyCompounds)
    },
  },
  methods: {
    fetchCompounds(filters, options, filtersUpdated) {
      const params = filteringParameters.prepareParameters(
        options,
        filters,
        filtersUpdated
      )
      params.studyUid = this.selectedStudy.uid
      this.studiesCompoundsStore.fetchStudyCompounds(params)
    },
    async fetchCompoundsHistory() {
      const resp = await study.getStudyCompoundsAuditTrail(
        this.selectedStudy.uid
      )
      return this.transformItems(resp.data)
    },
    async deleteStudyCompound(studyCompound) {
      const options = { type: 'warning' }
      let msg
      if (studyCompound.compound) {
        const compound = studyCompound.compound.name
        const context = { compound }
        if (studyCompound.study_compound_dosing_count) {
          context.compoundDosings = studyCompound.study_compound_dosing_count
          msg = this.$t('StudyCompoundTable.confirm_delete_cascade', context)
        } else {
          msg = this.$t('StudyCompoundTable.confirm_delete', context)
        }
      } else {
        msg = this.$t('StudyCompoundTable.confirm_delete_na')
      }
      if (!(await this.$refs.confirm.open(msg, options))) {
        return
      }
      this.studiesCompoundsStore
        .deleteStudyCompound(
          this.selectedStudy.uid,
          studyCompound.study_compound_uid
        )
        .then(() => {
          this.eventBusEmit('notification', {
            msg: this.$t('StudyCompoundTable.delete_compound_success'),
          })
        })
    },
    editStudyCompound(studyCompound) {
      const originalItem = this.studiesCompoundsStore.studyCompounds.find(
        (item) => item.study_compound_uid === studyCompound.study_compound_uid
      )
      this.selectedStudyCompound = originalItem
      this.showForm = true
    },
    async openStudyCompoundHistory(studyCompound) {
      this.selectedStudyCompound = studyCompound
      const resp = await study.getStudyCompoundAuditTrail(
        this.selectedStudy.uid,
        studyCompound.study_compound_uid
      )
      this.compoundHistoryItems = this.transformItems(resp.data)
      this.showCompoundHistory = true
    },
    closeStudyCompoundHistory() {
      this.selectedStudyCompound = null
      this.showCompoundHistory = false
    },
    closeForm() {
      this.showForm = false
      this.selectedStudyCompound = null
    },
    transformItems(items) {
      const result = []
      for (const item of items) {
        const newItem = { ...item }
        if (newItem.compound) {
          newItem.compound.is_sponsor_compound = dataFormating.yesno(
            newItem.compound.is_sponsor_compound
          )
          newItem.compound.is_name_inn = dataFormating.yesno(
            newItem.compound.is_name_inn
          )
          newItem.substances = dataFormating.substances(
            newItem.compound.substances
          )
          newItem.pharmacological_classes =
            dataFormating.pharmacologicalClasses(newItem.compound.substances)
          if (newItem.compound.half_life) {
            newItem.compound.half_life = dataFormating.numericValue(
              newItem.compound.half_life
            )
          }
          if (newItem.compound.lag_times) {
            newItem.lag_times = dataFormating.lagTimes(
              newItem.compound.lag_times
            )
          }
        }
        if (newItem.compound_alias) {
          newItem.compound_alias.is_preferred_synonym = dataFormating.yesno(
            newItem.is_preferred_synonym
          )
        }
        if (newItem.strength_value) {
          newItem.strength_value = dataFormating.numericValue(
            newItem.strength_value
          )
        }
        result.push(newItem)
      }
      return result
    },
  },
}
</script>
