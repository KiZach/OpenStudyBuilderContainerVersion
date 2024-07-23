<template>
  <StudyMetadataSummary
    :metadata="metadata"
    :params="params"
    :first-col-label="$t('StudyInterventionTypeSummary.intervention_type_info')"
    persistent-dialog
    copy-from-study
    component="study_intervention"
  >
    <template #form="{ closeHandler, dataToCopy, openHandler }">
      <InterventionTypeForm
        :open="openHandler"
        :metadata="Object.keys(dataToCopy).length !== 0 ? dataToCopy : metadata"
        @updated="onMetadataUpdated"
        @close="closeHandler"
      />
    </template>
  </StudyMetadataSummary>
</template>

<script>
import study from '@/api/study'
import InterventionTypeForm from './InterventionTypeForm.vue'
import StudyMetadataSummary from './StudyMetadataSummary.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'

export default {
  components: {
    InterventionTypeForm,
    StudyMetadataSummary,
  },
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    return {
      studiesGeneralStore,
    }
  },
  data() {
    return {
      metadata: {},
      params: [
        {
          label: this.$t('StudyInterventionTypeForm.intervention_type'),
          name: 'intervention_type_code',
          valuesDisplay: 'term',
        },
        {
          label: this.$t('StudyDefineForm.studyintent'),
          name: 'trial_intent_types_codes',
          valuesDisplay: 'terms',
        },
        {
          label: this.$t('StudyInterventionTypeForm.added_to_et'),
          name: 'add_on_to_existing_treatments',
          valuesDisplay: 'yesno',
        },
        {
          label: this.$t('StudyInterventionTypeForm.control_type'),
          name: 'control_type_code',
          valuesDisplay: 'term',
        },
        {
          label: this.$t('StudyInterventionTypeForm.intervention_model'),
          name: 'intervention_model_code',
          valuesDisplay: 'term',
        },
        {
          label: this.$t('StudyInterventionTypeForm.randomised'),
          name: 'is_trial_randomised',
          valuesDisplay: 'yesno',
        },
        {
          label: this.$t('StudyInterventionTypeForm.strfactor'),
          name: 'stratification_factor',
        },
        {
          label: this.$t('StudyInterventionTypeForm.blinding_schema'),
          name: 'trial_blinding_schema_code',
          valuesDisplay: 'term',
        },
        {
          label: this.$t('StudyInterventionTypeForm.planned_st_length'),
          name: 'planned_study_length',
          valuesDisplay: 'duration',
        },
      ],
    }
  },
  mounted() {
    this.studiesGeneralStore.fetchUnits()
    this.studiesGeneralStore.fetchTrialBlindingSchemas()
    this.studiesGeneralStore.fetchControlTypes()
    this.studiesGeneralStore.fetchInterventionModels()
    this.studiesGeneralStore.fetchTrialIntentTypes()
    this.studiesGeneralStore.fetchInterventionTypes()
    study
      .getStudyInterventionMetadata(
        this.studiesGeneralStore.selectedStudy.uid
      )
      .then((resp) => {
        this.metadata = resp.data.current_metadata.study_intervention
      })
  },
  methods: {
    onMetadataUpdated(metadata) {
      this.metadata = metadata
    },
  },
}
</script>
