<template>
  <SimpleFormDialog
    ref="form"
    :title="$t('ClinicalProgrammeForm.title')"
    :help-text="$t('_help.ClinicalProgrammeForm.general')"
    :help-items="helpItems"
    :open="open"
    @close="close"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <v-row>
          <v-col cols="12">
            <v-text-field
              id="name"
              v-model="form.name"
              :label="$t('ClinicalProgrammeForm.name')"
              density="compact"
              clearable
              data-cy="clinical-programme-name"
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

export default {
  components: {
    SimpleFormDialog,
  },
  inject: ['eventBusEmit', 'formRules'],
  props: {
    editedStudy: {
      type: Object,
      default: null,
    },
    open: Boolean,
  },
  emits: ['close', 'created'],
  data() {
    return {
      form: {},
      helpItems: ['ClinicalProgrammeForm.name'],
    }
  },
  watch: {},
  mounted() {
    this.initForm()
  },
  methods: {
    async close() {
      if (this.form.name) {
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
    },
    initForm() {
      this.form = {
        name: '',
      }
    },
    async addProgramme() {
      const data = JSON.parse(JSON.stringify(this.form))
      const resp = await programmes.create(data)
      this.eventBusEmit('notification', {
        msg: this.$t('ClinicalProgrammes.add_success'),
      })
      this.$emit('created', resp.data)
    },

    async submit() {
      try {
        await this.addProgramme()
        this.$emit('close')
      } finally {
        this.$refs.form.working = false
      }
    },
  },
}
</script>
