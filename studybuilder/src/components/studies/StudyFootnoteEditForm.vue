<template>
  <StudySelectionEditForm
    v-if="studyFootnote"
    ref="form"
    :title="$t('StudyFootnoteEditForm.title')"
    :study-selection="studyFootnote"
    :template="template"
    :library-name="library.name"
    object-type="footnote"
    :open="open"
    :get-object-from-selection="(selection) => selection.footnote"
    :prepare-template-payload-func="prepareTemplatePayload"
    @init-form="initForm"
    @submit="submit"
    @close="close"
  >
    <template #formFields="{}">
      <p class="mt-6 text-secondary text-h6">
        {{ $t('StudyFootnoteEditForm.linked_items') }}
        <v-btn
          icon="mdi-table-plus"
          variant="text"
          color="primary"
          :title="$t('StudyFootnoteEditForm.link_items')"
          @click="redirectToDetailedSoA"
        />
      </p>
      <v-row>
        <v-col cols="12">
          <v-text-field
            v-if="referencedSoAGroups.length > 0"
            v-model="referencedSoAGroups"
            :label="$t('StudyFootnoteEditForm.ref_soa_groups')"
            density="compact"
            disabled
            readonly
          />
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="12">
          <v-text-field
            v-if="referencedActivities.length > 0"
            v-model="referencedActivities"
            :label="$t('StudyFootnoteEditForm.ref_activities')"
            density="compact"
            disabled
            readonly
          />
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="12">
          <v-text-field
            v-if="referencedEpochsAndVisits.length > 0"
            v-model="referencedEpochsAndVisits"
            :label="$t('StudyFootnoteEditForm.ref_epochs_visits')"
            density="compact"
            disabled
            readonly
          />
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="12">
          <v-text-field
            v-if="referencedSchedules.length > 0"
            v-model="referencedSchedules"
            :label="$t('StudyFootnoteEditForm.ref_schedules')"
            density="compact"
            disabled
            readonly
          />
        </v-col>
      </v-row>
    </template>
  </StudySelectionEditForm>
</template>

<script>
import { computed } from 'vue'
import _isEmpty from 'lodash/isEmpty'
import formUtils from '@/utils/forms'
import instances from '@/utils/instances'
import study from '@/api/study'
import StudySelectionEditForm from './StudySelectionEditForm.vue'
import terms from '@/api/controlledTerminology/terms'
import footnoteConstants from '@/constants/footnotes'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useFootnotesStore } from '@/stores/studies-footnotes'

export default {
  components: {
    StudySelectionEditForm,
  },
  inject: ['eventBusEmit'],
  props: {
    studyFootnote: {
      type: Object,
      default: undefined,
    },
    open: Boolean,
  },
  emits: ['close', 'enableFootnoteMode', 'updated'],
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    const footnotesStore = useFootnotesStore()
    return {
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
      footnotesStore,
    }
  },
  data() {
    return {
      referencedSoAGroups: [],
      referencedActivities: [],
      referencedEpochsAndVisits: [],
      referencedSchedules: [],
    }
  },
  computed: {
    template() {
      return this.studyFootnote.footnote
        ? this.studyFootnote.footnote.footnote_template
        : this.studyFootnote.footnote_template
    },
    library() {
      return this.studyFootnote.footnote
        ? this.studyFootnote.footnote.library
        : this.studyFootnote.footnote_template.library
    },
  },
  mounted() {
    terms.getByCodelist('footnoteTypes').then((resp) => {
      for (const type of resp.data.items) {
        if (
          type.name.sponsor_preferred_name ===
          footnoteConstants.FOOTNOTE_TYPE_SOA
        ) {
          this.footnoteType = type
          break
        }
      }
    })
  },
  methods: {
    redirectToDetailedSoA() {
      if (window.location.href.includes('detailed')) {
        this.$emit('enableFootnoteMode', this.studyFootnote)
      } else {
        this.$router.push({
          name: 'StudyActivities',
          params: {
            study_id: this.selectedStudy.uid,
            tab: 'detailed',
          },
        })
        this.$emit('enableFootnoteMode', this.studyFootnote)
      }
      this.$refs.form.close()
    },
    initForm(form) {
      this.originalForm = JSON.parse(JSON.stringify(form))
      this.referencedActivities = []
      this.referencedEpochsAndVisits = []
      this.studyFootnote.referenced_items.forEach((item) => {
        if (['StudySoAGroup'].indexOf(item.item_type) > -1) {
          this.referencedSoAGroups.push(item.item_name)
        } else if (
          [
            'StudyActivity',
            'StudyActivityGroup',
            'StudyActivitySubGroup',
          ].indexOf(item.item_type) > -1
        ) {
          this.referencedActivities.push(item.item_name)
        } else if (['StudyVisit', 'StudyEpoch'].indexOf(item.item_type) > -1) {
          this.referencedEpochsAndVisits.push(item.item_name)
        } else if (['StudyActivitySchedule'].indexOf(item.item_type) > -1) {
          this.referencedSchedules.push(item.item_name)
        }
      })
      this.referencedActivities = this.removeDuplicates(
        this.referencedActivities
      ).join(', ')
      this.referencedSoAGroups = this.removeDuplicates(
        this.referencedSoAGroups
      ).join(', ')
      this.referencedEpochsAndVisits = this.referencedEpochsAndVisits.join(', ')
      this.referencedSchedules = this.referencedSchedules.join(', ')
    },
    removeDuplicates(arr) {
      return arr.filter((item, index, self) => {
        return self.indexOf(item) === index
      })
    },
    prepareTemplatePayload(data) {
      data.type_uid = this.footnoteType.term_uid
    },
    async getStudyFootnoteNamePreview(parameters) {
      const footnoteData = {
        footnote_template_uid:
          this.studyFootnote.footnote.footnote_template.uid,
        parameter_terms: await instances.formatParameterValues(parameters),
        library_name: this.studyFootnote.footnote.library.name,
      }
      const resp = await study.getStudyFootnotePreview(this.selectedStudy.uid, {
        footnote_data: footnoteData,
      })
      return resp.data.footnote.name
    },
    async submit(newTemplate, form, parameters) {
      const payload = formUtils.getDifferences(this.originalForm, form)
      if (!this.studyFootnote.footnote) {
        payload.parameters = parameters
      } else {
        const namePreview = await this.getStudyFootnoteNamePreview(parameters)
        if (namePreview !== this.studyFootnote.footnote.name) {
          payload.parameters = parameters
        }
      }
      if (_isEmpty(payload) && !newTemplate) {
        this.eventBusEmit('notification', {
          msg: this.$t('_global.no_changes'),
          type: 'info',
        })
        this.$refs.form.close()
        return
      }
      const args = {
        studyUid: this.selectedStudy.uid,
        studyFootnoteUid: this.studyFootnote.uid,
        form: payload,
        library: this.library,
      }
      if (newTemplate) {
        args.template = newTemplate
      } else {
        args.template = this.template
      }
      await this.footnotesStore.updateStudyFootnote(args)
      this.eventBusEmit('notification', {
        msg: this.$t('StudyFootnoteEditForm.update_success'),
      })
      this.$emit('updated')
      this.$refs.form.close()
    },
    close() {
      this.referencedSoAGroups = []
      this.referencedActivities = []
      this.referencedEpochsAndVisits = []
      this.referencedSchedules = []
      this.$emit('close')
    },
  },
}
</script>
