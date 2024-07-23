<template>
  <StudyMetadataSummary
    :metadata="identification"
    :params="params"
    :first-col-label="$t('StudyIdentificationSummary.core_attribute')"
    :fullscreen-form="false"
    form-max-width="1000px"
    component="identification_metadata"
    :with-reason-for-missing="false"
  >
    <template #topActions>
      <v-btn
        v-if="canDeleteSelectedStudy()"
        size="small"
        color="red"
        :title="$t('_global.delete')"
        icon="mdi-delete-outline"
        @click.stop="deleteStudy"
      />
    </template>
    <template #form="{ closeHandler, openHandler }">
      <StudyForm
        :open="openHandler"
        :edited-study="study"
        @close="close(closeHandler)"
        @updated="onIdentificationUpdated"
      />
    </template>
  </StudyMetadataSummary>
  <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
</template>

<script>
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import api from '@/api/study'
import StudyForm from './StudyForm.vue'
import StudyMetadataSummary from './StudyMetadataSummary.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'

export default {
  components: {
    ConfirmDialog,
    StudyForm,
    StudyMetadataSummary,
  },
  inject: ['eventBusEmit'],
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()

    return {
      studiesGeneralStore,
    }
  },
  data() {
    return {
      identification: {},
      params: [
        {
          label: this.$t('Study.clinical_programme'),
          name: 'clinical_programme_name',
        },
        {
          label: this.$t('Study.project_number'),
          name: 'project_number',
        },
        {
          label: this.$t('Study.project_name'),
          name: 'project_name',
        },
        {
          label: this.$t('Study.study_id'),
          name: 'study_id',
        },
        {
          label: this.$t('Study.study_number'),
          name: 'study_number',
        },
        {
          label: this.$t('Study.study_acronym'),
          name: 'study_acronym',
        },
      ],
      study: null,
    }
  },
  mounted() {
    api.getStudy(this.studiesGeneralStore.selectedStudy.uid).then((resp) => {
      this.study = resp.data
      this.identification = resp.data.current_metadata.identification_metadata
    })
  },
  methods: {
    canDeleteSelectedStudy() {
      return (
        this.study &&
        this.study.possible_actions.find((action) => action === 'delete')
      )
    },
    async deleteStudy() {
      const options = { type: 'warning' }
      const study = this.study.current_metadata.identification_metadata.study_id
      if (
        await this.$refs.confirm.open(
          this.$t('StudyStatusTable.confirm_delete', { study }),
          options
        )
      ) {
        await api.deleteStudy(this.studiesGeneralStore.selectedStudy.uid)
        this.eventBusEmit('notification', {
          msg: this.$t('StudyStatusTable.delete_success'),
          type: 'success',
        })
        this.studiesGeneralStore.unselectStudy()
        this.$router.push({ name: 'SelectOrAddStudy' })
      }
    },
    close(closeHandler) {
      closeHandler()
    },
    onIdentificationUpdated(data) {
      this.study = data
      this.identification = data.current_metadata.identification_metadata
    },
  },
}
</script>
