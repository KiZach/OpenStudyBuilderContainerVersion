<template>
  <StudyMetadataSummary
    :metadata="metadata"
    :params="params"
    :first-col-label="$t('StudyPopulationSummary.info_column')"
    persistent-dialog
    copy-from-study
    component="study_population"
  >
    <template #form="{ closeHandler, dataToCopy, openHandler }">
      <StudyPopulationForm
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
import StudyMetadataSummary from './StudyMetadataSummary.vue'
import StudyPopulationForm from './StudyPopulationForm.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'

export default {
  components: {
    StudyMetadataSummary,
    StudyPopulationForm,
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
          label: this.$t('StudyPopulationForm.therapeuticarea'),
          name: 'therapeutic_area_codes',
          valuesDisplay: 'terms',
        },
        {
          label: this.$t('StudyPopulationForm.disease_condition'),
          name: 'disease_condition_or_indication_codes',
          valuesDisplay: 'terms',
        },
        {
          label: this.$t('StudyPopulationForm.stable_disease_min_duration'),
          name: 'stable_disease_minimum_duration',
          valuesDisplay: 'duration',
        },
        {
          label: this.$t('StudyPopulationForm.healthy_subjects'),
          name: 'healthy_subject_indicator',
          valuesDisplay: 'yesno',
        },
        {
          label: this.$t('StudyPopulationForm.diagnosis_group'),
          name: 'diagnosis_group_codes',
          valuesDisplay: 'terms',
        },
        {
          label: this.$t('StudyPopulationForm.relapse_criteria'),
          name: 'relapse_criteria',
        },
        {
          label: this.$t('StudyPopulationForm.number_of_expected_subjects'),
          name: 'number_of_expected_subjects',
        },
        {
          label: this.$t('StudyPopulationForm.rare_disease_indicator'),
          name: 'rare_disease_indicator',
          valuesDisplay: 'yesno',
        },
        {
          label: this.$t('StudyPopulationForm.sex_of_study_participants'),
          name: 'sex_of_participants_code',
          valuesDisplay: 'terms',
        },
        {
          label: this.$t('StudyPopulationForm.planned_min_age'),
          name: 'planned_minimum_age_of_subjects',
          valuesDisplay: 'duration',
        },
        {
          label: this.$t('StudyPopulationForm.planned_max_age'),
          name: 'planned_maximum_age_of_subjects',
          valuesDisplay: 'duration',
        },
        {
          label: this.$t('StudyPopulationForm.pediatric_study_indicator'),
          name: 'pediatric_study_indicator',
          valuesDisplay: 'yesno',
        },
        {
          label: this.$t(
            'StudyPopulationForm.pediatric_investigation_plan_indicator'
          ),
          name: 'pediatric_investigation_plan_indicator',
          valuesDisplay: 'yesno',
        },
        {
          label: this.$t(
            'StudyPopulationForm.pediatric_postmarket_study_indicator'
          ),
          name: 'pediatric_postmarket_study_indicator',
          valuesDisplay: 'yesno',
        },
      ],
    }
  },
  created() {
    this.studiesGeneralStore.fetchUnits()
    this.studiesGeneralStore.fetchSnomedTerms()
    this.studiesGeneralStore.fetchSexOfParticipants()
    study
      .getStudyPopulationMetadata(
        this.studiesGeneralStore.selectedStudy.uid
      )
      .then((resp) => {
        this.metadata = resp.data.current_metadata.study_population
      })
  },
  methods: {
    onMetadataUpdated(metadata) {
      this.metadata = metadata
    },
  },
}
</script>
