<template>
  <SimpleFormDialog
    ref="form"
    :title="$t('StudyDefineForm.title')"
    :help-items="helpItems"
    :help-text="$t('_help.StudyDefineForm.general')"
    :open="open"
    @close="cancel"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <v-row class="pr-4">
          <v-col cols="11">
            <v-autocomplete
              v-model="form.study_type_code"
              data-cy="study-type"
              :label="$t('StudyDefineForm.studytype')"
              :items="studiesGeneralStore.studyTypes"
              item-title="sponsor_preferred_name"
              item-value="term_uid"
              return-object
              density="compact"
              clearable
            />
          </v-col>
        </v-row>
        <v-row class="pr-4">
          <v-col cols="11">
            <MultipleSelect
              v-model="form.trial_type_codes"
              data-cy="trial-type"
              :label="$t('StudyDefineForm.trialtype')"
              :items="studiesGeneralStore.trialTypes"
              item-title="sponsor_preferred_name"
              item-value="term_uid"
              return-object
            />
          </v-col>
        </v-row>
        <v-row class="pr-4">
          <v-col cols="11">
            <v-select
              v-model="form.trial_phase_code"
              data-cy="study-phase-classification"
              :label="$t('StudyDefineForm.trialphase')"
              :items="studiesGeneralStore.trialPhases"
              item-title="sponsor_preferred_name_sentence_case"
              item-value="term_uid"
              return-object
              density="compact"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="5">
            <YesNoField
              v-model="form.is_extension_trial"
              data-cy="extension-study"
              :rules="[(value) => formRules.oneselected(value, null)]"
              :label="$t('StudyDefineForm.extensiontrial')"
            />
          </v-col>
          <v-col cols="5">
            <YesNoField
              v-model="form.is_adaptive_design"
              data-cy="adaptive-design"
              :label="$t('StudyDefineForm.adaptivedesign')"
            />
          </v-col>
        </v-row>
        <v-row class="pr-4 mb-4">
          <v-col cols="10">
            <v-text-field
              v-model="form.study_stop_rules"
              data-cy="stop-rule"
              :label="$t('StudyDefineForm.studystoprule')"
              density="compact"
              :disabled="stopRulesNone"
            />
          </v-col>
          <v-col cols="2">
            <v-checkbox
              v-model="stopRulesNone"
              color="primary"
              :label="$t('StudyDefineForm.none')"
              hide-details
              @change="updateStopRules"
            />
          </v-col>
        </v-row>
        <NotApplicableField
          :label="$t('StudyDefineForm.confirmed_resp_min_duration')"
          data-cy="confirmed-resp-min-dur-field"
          :clean-function="setNullValueConfirmedDuration"
          :checked="
            form.confirmed_response_minimum_duration_null_value_code
              ? true
              : false
          "
        >
          <template #mainField="{ notApplicable }">
            <DurationField
              v-model="form.confirmed_response_minimum_duration"
              data-cy="confirmed-resp-min-dur"
              numeric-field-name="duration_value"
              unit-field-name="duration_unit_code"
              :disabled="notApplicable"
            />
          </template>
        </NotApplicableField>
        <v-row class="mt-4">
          <v-col cols="9">
            <YesNoField
              v-model="form.post_auth_indicator"
              data-cy="post-auth-safety-indicator"
              :label="$t('StudyDefineForm.post_auth_safety_indicator')"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script>
import _isEqual from 'lodash/isEqual'
import DurationField from '@/components/tools/DurationField.vue'
import MultipleSelect from '@/components/tools/MultipleSelect.vue'
import NotApplicableField from '@/components/tools/NotApplicableField.vue'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import studyConstants from '@/constants/study'
import YesNoField from '@/components/tools/YesNoField.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useStudiesManageStore } from '@/stores/studies-manage'
import studyMetadataForms from '@/utils/studyMetadataForms'

export default {
  components: {
    DurationField,
    MultipleSelect,
    NotApplicableField,
    SimpleFormDialog,
    YesNoField,
  },
  inject: ['eventBusEmit', 'formRules'],
  props: {
    metadata: {
      type: Object,
      default: undefined,
    },
    open: Boolean,
  },
  emits: ['close', 'updated'],
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    const studiesManageStore = useStudiesManageStore()
    return {
      studiesGeneralStore,
      studiesManageStore,
    }
  },
  data() {
    return {
      form: {},
      helpItems: [
        'StudyDefineForm.studytype',
        'StudyDefineForm.studyintent',
        'StudyDefineForm.trialtype',
        'StudyDefineForm.trialphase',
        'StudyDefineForm.extensiontrial',
        'StudyDefineForm.adaptivedesign',
        'StudyDefineForm.studystoprule',
        'StudyDefineForm.confirmed_resp_min_duration',
        'StudyDefineForm.post_auth_safety_indicator',
      ],
      stopRulesNone: false,
    }
  },
  watch: {
    metadata: {
      handler(value) {
        this.form = { ...value }
        // The API does not return the exact same properties when data
        // is coming from study metadata. It includes a 'name' property
        // while we use 'sponsor_preferred_name' in lists (data is
        // coming from codelist names)
        if (this.form.study_type_code) {
          this.form.study_type_code.sponsor_preferred_name =
            this.form.study_type_code.name
        }
        if (this.form.trial_type_codes) {
          for (let code of this.form.trial_type_codes) {
            code.sponsor_preferred_name = code.name
          }
        }
        if (this.form.trial_phase_code) {
          this.form.trial_phase_code.sponsor_preferred_name_sentence_case =
            this.form.trial_phase_code.name
        }
        if (!this.form.confirmed_response_minimum_duration) {
          this.form.confirmed_response_minimum_duration = {}
        }
        if (
          this.form.study_stop_rules == null ||
          this.form.study_stop_rules === studyConstants.STOP_RULE_NONE
        ) {
          this.stopRulesNone = true
          this.form.study_stop_rules = null
        } else {
          this.stopRulesNone = false
        }
      },
      immediate: true,
      deep: true,
    },
  },
  methods: {
    setNullValueConfirmedDuration() {
      this.form.confirmed_response_minimum_duration = {}
      if (this.form.confirmed_response_minimum_duration_null_value_code) {
        this.form.confirmed_response_minimum_duration_null_value_code = null
      } else {
        this.form.confirmed_response_minimum_duration_null_value_code = {
          term_uid: this.$t('_global.na_uid'),
          name: this.$t('_global.not_applicable_full_name'),
        }
      }
    },
    close() {
      this.$emit('close')
      this.$refs.observer.resetValidation()
    },
    prepareRequestPayload() {
      const data = { ...this.form }
      if (!data.confirmed_response_minimum_duration.duration_value) {
        data.confirmed_response_minimum_duration = null
      }
      data.study_type_code = studyMetadataForms.getTermPayload(
        data,
        'study_type_code'
      )
      data.trial_intent_types_codes = studyMetadataForms.getTermsPayload(
        data,
        'trial_intent_types_codes'
      )
      data.trial_type_codes = studyMetadataForms.getTermsPayload(
        data,
        'trial_type_codes'
      )
      data.trial_phase_code = studyMetadataForms.getTermPayload(
        data,
        'trial_phase_code'
      )
      if (this.stopRulesNone) {
        // This whole block can be removed if we decide to store NONE values as null in the backend
        data.study_stop_rules = studyConstants.STOP_RULE_NONE
      }
      return data
    },
    async cancel() {
      if (_isEqual(this.metadata, this.prepareRequestPayload())) {
        this.close()
        return
      }
      const options = {
        type: 'warning',
        cancelLabel: this.$t('_global.cancel'),
        agreeLabel: this.$t('_global.continue'),
      }
      if (
        await this.$refs.form.confirm(
          this.$t('_global.cancel_changes'),
          options
        )
      ) {
        this.close()
      }
    },
    async submit() {
      const data = this.prepareRequestPayload()
      try {
        const parentUid = this.studiesGeneralStore.selectedStudy
          .study_parent_part
          ? this.studiesGeneralStore.selectedStudy.study_parent_part.uid
          : null
        await this.studiesManageStore.editStudyType(
          this.studiesGeneralStore.selectedStudy.uid,
          data,
          parentUid
        )
        this.$emit('updated', data)
        this.eventBusEmit('notification', {
          msg: this.$t('StudyDefineForm.update_success'),
        })
        this.close()
      } finally {
        this.$refs.form.working = false
      }
    },
    updateStopRules(value) {
      if (value) {
        this.form.study_stop_rules = null
      } else {
        this.form.study_stop_rules = ''
      }
    },
  },
}
</script>
