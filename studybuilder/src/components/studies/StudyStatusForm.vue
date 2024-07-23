<template>
  <SimpleFormDialog
    ref="form"
    :title="title"
    :help-items="helpItems"
    :open="open"
    max-width="1200px"
    :scrollable="false"
    @close="close"
    @submit="submit"
  >
    <template #body>
      <v-data-table :headers="headers" :items="items" class="mb-10">
        <template #bottom />
      </v-data-table>

      <v-form ref="observer">
        <v-row>
          <v-col cols="12">
            <v-textarea
              v-model="form.change_description"
              :label="$t('Study.release_description')"
              data-cy="release-description"
              :rules="[formRules.required]"
              hide-details
              class="mt-10"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script>
import api from '@/api/study'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'

export default {
  components: {
    SimpleFormDialog,
  },
  inject: ['eventBusEmit', 'formRules'],
  props: {
    action: {
      type: String,
      default: '',
    },
    helpItems: {
      type: Array,
      default: () => [],
    },
    open: Boolean,
  },
  emits: ['close', 'statusChanged'],
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()

    return {
      studiesGeneralStore,
    }
  },
  data() {
    return {
      form: {},
      headers: [
        {
          title: this.$t('Study.status'),
          key: 'current_metadata.version_metadata.study_status',
        },
        {
          title: this.$t('Study.clinical_programme'),
          key: 'current_metadata.identification_metadata.clinical_programme_name',
        },
        {
          title: this.$t('Study.project_number'),
          key: 'current_metadata.identification_metadata.project_number',
        },
        {
          title: this.$t('Study.project_name'),
          key: 'current_metadata.identification_metadata.project_name',
        },
        {
          title: this.$t('Study.study_number'),
          key: 'current_metadata.identification_metadata.study_number',
        },
        {
          title: this.$t('Study.acronym'),
          key: 'current_metadata.identification_metadata.study_acronym',
        },
      ],
    }
  },
  computed: {
    title() {
      return this.action === 'release'
        ? this.$t('StudyStatusForm.release_title')
        : this.$t('StudyStatusForm.lock_title')
    },
    items() {
      return [this.studiesGeneralStore.selectedStudy]
    },
  },
  methods: {
    close() {
      this.form = {}
      this.$refs.observer.reset()
      this.$emit('close')
    },
    async submit() {
      try {
        if (this.action === 'release') {
          await api.releaseStudy(
            this.studiesGeneralStore.selectedStudy.uid,
            this.form
          )
          this.eventBusEmit('notification', {
            msg: this.$t('StudyStatusForm.release_success'),
            type: 'success',
          })
        } else {
          const resp = await api.lockStudy(
            this.studiesGeneralStore.selectedStudy.uid,
            this.form
          )
          this.studiesGeneralStore.selectStudy(resp.data)
          this.eventBusEmit('notification', {
            msg: this.$t('StudyStatusForm.lock_success'),
            type: 'success',
          })
        }
        this.$emit('statusChanged')
        this.close()
      } finally {
        this.$refs.form.working = false
      }
    },
  },
}
</script>
