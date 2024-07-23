<template>
  <StudyMetadataSummary
    :metadata="metadata"
    :params="params"
    :first-col-label="$t('StudyTypeSummary.info_column')"
    persistent-dialog
    copy-from-study
    component="high_level_study_design"
  >
    <template #form="{ closeHandler, dataToCopy, openHandler }">
      <StudyDefineForm
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
import StudyDefineForm from './StudyDefineForm.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'

export default {
  components: {
    StudyMetadataSummary,
    StudyDefineForm,
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
          label: this.$t('StudyDefineForm.studytype'),
          name: 'study_type_code',
          valuesDisplay: 'term',
        },
        {
          label: this.$t('StudyDefineForm.trialtype'),
          name: 'trial_type_codes',
          valuesDisplay: 'terms',
        },
        {
          label: this.$t('StudyDefineForm.trialphase'),
          name: 'trial_phase_code',
          valuesDisplay: 'term',
        },
        {
          label: this.$t('StudyDefineForm.extensiontrial'),
          name: 'is_extension_trial',
          valuesDisplay: 'yesno',
        },
        {
          label: this.$t('StudyDefineForm.adaptivedesign'),
          name: 'is_adaptive_design',
          valuesDisplay: 'yesno',
        },
        {
          label: this.$t('StudyDefineForm.studystoprule'),
          name: 'study_stop_rules',
        },
        {
          label: this.$t('StudyDefineForm.confirmed_resp_min_duration'),
          name: 'confirmed_response_minimum_duration',
          valuesDisplay: 'duration',
        },
        {
          label: this.$t('StudyDefineForm.post_auth_safety_indicator'),
          name: 'post_auth_indicator',
          valuesDisplay: 'yesno',
        },
      ],
    }
  },
  mounted() {
    this.studiesGeneralStore.fetchUnits()
    this.studiesGeneralStore.fetchStudyTypes()
    this.studiesGeneralStore.fetchTrialIntentTypes()
    this.studiesGeneralStore.fetchTrialPhases()
    this.studiesGeneralStore.fetchTrialTypes()
    this.studiesGeneralStore.fetchNullValues()
    study
      .getHighLevelStudyDesignMetadata(
        this.studiesGeneralStore.selectedStudy.uid
      )
      .then((resp) => {
        this.metadata = resp.data.current_metadata.high_level_study_design
      })
  },
  methods: {
    onMetadataUpdated(metadata) {
      this.metadata = metadata
    },
  },
}
</script>
