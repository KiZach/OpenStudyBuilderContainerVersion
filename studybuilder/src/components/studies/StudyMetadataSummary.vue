<template>
  <v-card elevation="0" class="rounded-0">
    <v-card-title
      style="z-index: 3; position: relative"
      class="pt-0 mt-3 d-flex align-center"
    >
      <v-spacer />
      <slot name="topActions" />
      <v-btn
        v-if="copyFromStudy"
        color="primary"
        data-cy="copy-from-study"
        size="small"
        :title="$t('NNTableTooltips.copy_from_study')"
        :disabled="
          !checkPermission($roles.STUDY_WRITE) ||
          studiesGeneralStore.selectedStudyVersion !== null
        "
        icon="mdi-content-copy"
        @click.stop="openCopyForm"
      />
      <v-btn
        size="small"
        class="ml-2"
        color="primary"
        :title="$t('NNTableTooltips.edit_content')"
        :disabled="
          !checkPermission($roles.STUDY_WRITE) ||
          studiesGeneralStore.selectedStudyVersion !== null ||
          disableEdit
        "
        data-cy="edit-content"
        icon="mdi-pencil-outline"
        @click.stop="openForm"
      />
      <v-btn
        class="ml-2"
        color="secondary"
        size="small"
        :title="$t('NNTableTooltips.history')"
        icon="mdi-history"
        @click="openHistory"
      />
    </v-card-title>
    <v-card-text>
      <v-data-table
        :headers="headers"
        :items="computedParams"
        item-value="name"
        :items-per-page="15"
      />
      <slot
        name="form"
        :open-handler="showForm"
        :close-handler="closeForm"
        :data="metadata"
        :data-to-copy="dataToCopy"
      />

      <v-dialog
        v-model="showCopyForm"
        persistent
        max-width="500px"
        @keydown.esc="closeCopyForm"
      >
        <CopyFromStudyForm
          :component="component"
          @close="closeCopyForm"
          @apply="openFormToCopy"
        />
      </v-dialog>

      <v-dialog
        v-model="showHistory"
        persistent
        :fullscreen="$globals.historyDialogFullscreen"
        @keydown.esc="closeHistory"
      >
        <HistoryTable
          :headers="historyHeaders"
          :items="historyItems"
          :title="historyTitle"
          :export-name="component"
          start-date-header="date"
          change-field="action"
          simple-styling
          @close="closeHistory"
        />
      </v-dialog>
    </v-card-text>
  </v-card>
</template>

<script>
import CopyFromStudyForm from '@/components/tools/CopyFromStudyForm.vue'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import study from '@/api/study'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesGeneralStore } from '@/stores/studies-general'

export default {
  components: {
    HistoryTable,
    CopyFromStudyForm,
  },
  props: {
    params: {
      type: Array,
      default: () => [],
    },
    metadata: {
      type: Object,
      default: undefined,
    },
    firstColLabel: {
      type: String,
      default: '',
    },
    persistentDialog: {
      type: Boolean,
      default: false,
    },
    formMaxWidth: {
      type: String,
      required: false,
      default: '',
    },
    copyFromStudy: {
      type: Boolean,
      default: false,
    },
    component: {
      type: String,
      default: '',
    },
    withReasonForMissing: {
      type: Boolean,
      default: true,
    },
    disableEdit: {
      type: Boolean,
      default: false,
    },
  },
  setup() {
    const accessGuard = useAccessGuard()
    const studiesGeneralStore = useStudiesGeneralStore()

    return {
      studiesGeneralStore,
      ...accessGuard,
    }
  },
  data() {
    const headers = [
      { title: this.firstColLabel, key: 'name', width: '30%' },
      { title: this.$t('StudyMetadataSummary.selected_values'), key: 'values' },
    ]
    if (this.withReasonForMissing) {
      headers.push({
        title: this.$t('StudyMetadataSummary.reason_for_missing'),
        key: 'reason_for_missing',
      })
    }
    return {
      headers,
      historyHeaders: [
        { title: this.$t('HistoryTable.field'), key: 'field' },
        {
          title: this.$t('HistoryTable.value_before'),
          key: 'before_value.term_uid',
        },
        {
          title: this.$t('HistoryTable.value_after'),
          key: 'after_value.term_uid',
        },
        { title: this.$t('_global.user'), key: 'user_initials' },
      ],
      historyItems: [],
      showHistory: false,
      showForm: false,
      showCopyForm: false,
      dataToCopy: {},
    }
  },
  computed: {
    computedParams() {
      return this.buildTableParams(this.params)
    },
    historyTitle() {
      return `${this.component} ${this.$t('HistoryTable.fields')} ${this.$t('HistoryTable.history')} (${this.studiesGeneralStore.selectedStudy.uid})`
    },
    exportDataUrl() {
      return `studies/${this.studiesGeneralStore.selectedStudy.uid}`
    },
  },
  methods: {
    openForm() {
      this.showForm = true
    },
    closeForm() {
      this.showForm = false
    },
    openFormToCopy(data) {
      this.dataToCopy = data
      this.showForm = true
      this.showCopyForm = false
    },
    openCopyForm() {
      this.showCopyForm = true
    },
    closeCopyForm() {
      this.showCopyForm = false
    },
    async openHistory() {
      this.historyItems = []
      const resp = await study.getStudyFieldsAuditTrail(
        this.studiesGeneralStore.selectedStudy.uid,
        this.component
      )
      for (const group of resp.data) {
        for (const groupItem of group.actions) {
          const row = {
            user_initials: group.user_initials,
            date: group.date,
            field: groupItem.field,
            action: groupItem.action,
            before_value: groupItem.before_value,
            after_value: groupItem.after_value,
          }
          this.historyItems.push(row)
        }
      }
      this.showHistory = true
    },
    closeHistory() {
      this.showHistory = false
    },
    buildTableParams(fields) {
      const result = []
      fields.forEach((field) => {
        let nullValueName = null
        if (field.nullValueName === undefined) {
          nullValueName = field.name
          const suffixes = ['_code', '_codes']
          suffixes.forEach((suffix) => {
            if (nullValueName.endsWith(suffix)) {
              nullValueName = nullValueName.replace(suffix, '')
            }
          })
          nullValueName += '_null_value_code'
        } else {
          nullValueName = field.nullValueName
        }
        let values = this.metadata[field.name]
        if (
          field.name === 'sex_of_participants_code' &&
          values !== undefined &&
          values !== null
        ) {
          values = values.name
        }
        if (field.name === 'study_stop_rules' && values == null) {
          values = this.$t('StudyDefineForm.none')
        }
        result.push({
          name: field.label,
          values:
            values !== undefined &&
            values !== null &&
            field.valuesDisplay &&
            field.name !== 'sex_of_participants_code'
              ? this[`${field.valuesDisplay}Display`](values)
              : values,
          reason_for_missing: this.naDisplay(this.metadata[nullValueName]),
        })
      })
      return result
    },
    yesnoDisplay(value) {
      return value ? this.$t('_global.yes') : this.$t('_global.no')
    },
    durationDisplay(value) {
      return `${value.duration_value} ${value.duration_unit_code.name}`
    },
    termDisplay(value) {
      if (!value) {
        return ''
      }
      return value.name
    },
    termsDisplay(value) {
      const result = value.map((item) => item.name)
      return result.join(', ')
    },
    naDisplay(value) {
      if (value) {
        return value.name
      }
    },
  },
}
</script>
