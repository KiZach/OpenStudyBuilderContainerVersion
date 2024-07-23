<template>
  <SimpleFormDialog
    ref="form"
    :title="$t('UCUMCodeForm.title')"
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
              v-model="form.name"
              :label="$t('_global.name')"
              :rules="[formRules.required]"
              density="compact"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-textarea
              v-model="form.definition"
              :label="$t('UCUM.description')"
              :rules="[formRules.required]"
              density="compact"
              clearable
              auto-grow
              rows="1"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script>
import dictionaries from '@/api/dictionaries'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import constants from '@/constants/libraries'

export default {
  components: {
    SimpleFormDialog,
  },
  inject: ['eventBusEmit', 'formRules'],
  props: {
    codelistUid: {
      type: String,
      default: null,
    },
    open: Boolean,
  },
  emits: ['save', 'close'],
  data() {
    return {
      helpItems: ['UCUM.code', 'UCUM.description'],
      form: {},
    }
  },
  watch: {
    codelistUid() {
      this.form.codelist_uid = this.codelistUid
    },
  },
  methods: {
    close() {
      this.$refs.form.working = false
      this.form = {}
      this.$emit('close')
    },
    async submit() {
      this.form.library_name = constants.LIBRARY_UCUM
      this.form.name_sentence_case = this.form.name
      this.form.dictionary_id = this.form.name
      dictionaries.create(this.form).then(
        () => {
          this.eventBusEmit('notification', {
            msg: this.$t('DictionaryTermForm.create_success'),
          })
          this.$emit('save')
          this.close()
        },
        () => {
          this.$refs.form.working = false
        }
      )
    },
  },
}
</script>
