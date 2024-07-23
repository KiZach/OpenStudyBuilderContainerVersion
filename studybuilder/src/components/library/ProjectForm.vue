<template>
  <SimpleFormDialog
    ref="form"
    :title="$t('ProjectForm.title')"
    :help-items="helpItems"
    :help-text="$t('_help.ClinicalProgrammeForm.general')"
    :open="open"
    @close="close"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <v-row>
          <v-col cols="11">
            <v-autocomplete
              v-model="form.clinical_programme_uid"
              :label="$t('ProjectForm.clinical_programme')"
              data-cy="template-activity-group"
              :items="programmes"
              item-title="name"
              item-value="uid"
              density="compact"
              clearable
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              id="name"
              v-model="form.name"
              :label="$t('ProjectForm.name')"
              density="compact"
              clearable
              data-cy="project-name"
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              id="project-number"
              v-model="form.project_number"
              :label="$t('ProjectForm.project_number')"
              density="compact"
              clearable
              data-cy="project-number"
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              id="description"
              v-model="form.description"
              :label="$t('ProjectForm.description')"
              density="compact"
              clearable
              data-cy="project-description"
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script>
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import programmes from '@/api/clinicalProgrammes'
import projects from '@/api/projects'

export default {
  components: {
    SimpleFormDialog,
  },
  inject: ['formRules', 'eventBusEmit'],
  props: {
    editedStudy: {
      type: Object,
      default: null,
    },
    open: Boolean,
  },
  emits: ['created', 'close'],
  data() {
    return {
      form: {},
      helpItems: [
        'ProjectForm.clinical_programme',
        'ProjectForm.name',
        'ProjectForm.project_number',
        'ProjectForm.description',
      ],
    }
  },
  watch: {},
  mounted() {
    this.fetchProgrammes()
    this.initForm()
  },
  methods: {
    async close() {
      if (
        this.form.name ||
        this.form.clinical_programme_uid ||
        this.form.description ||
        this.form.project_number
      ) {
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
          this.$emit('close')
        }
      } else {
        this.$emit('close')
      }
      this.initForm()
    },
    initForm() {
      this.form = {}
    },
    async addProject() {
      const data = JSON.parse(JSON.stringify(this.form))
      const resp = await projects.create(data)
      this.eventBusEmit('notification', {
        msg: this.$t('Projects.add_success'),
      })
      this.$emit('created', resp.data)
    },
    async submit() {
      try {
        await this.addProject()
        this.$emit('close')
      } finally {
        this.$refs.form.working = false
      }
      this.initForm()
    },
    fetchProgrammes() {
      programmes.get({ page_size: 0 }).then((resp) => {
        this.programmes = resp.data.items
      })
    },
  },
}
</script>
