<template>
  <SimpleFormDialog
    ref="form"
    :title="title"
    :help-items="helpItems"
    :open="open"
    @close="cancel"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <v-row>
          <v-col cols="6">
            <v-text-field
              v-model="form.name"
              :label="$t('_global.name')"
              density="compact"
              clearable
              :rules="[formRules.required]"
            />
          </v-col>
          <v-col cols="6">
            <v-text-field
              v-model="form.prefix"
              :label="$t('CrfExtensions.prefix')"
              density="compact"
              clearable
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.url"
              :label="$t('CrfExtensions.url')"
              density="compact"
              clearable
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
import crfs from '@/api/crfs'

export default {
  components: {
    SimpleFormDialog,
  },
  inject: ['formRules'],
  props: {
    open: Boolean,
    editItem: {
      type: Object,
      default: null,
    },
  },
  emits: ['close'],
  data() {
    return {
      form: {},
      helpItems: [],
    }
  },
  computed: {
    title() {
      return this.editItem.uid
        ? this.$t('CrfExtensions.edit_namespace')
        : this.$t('CrfExtensions.new_namespace')
    },
  },
  watch: {
    editItem(value) {
      this.initForm(value)
    },
  },
  methods: {
    async cancel() {
      this.close()
    },
    close() {
      this.$refs.observer.reset()
      this.$emit('close')
    },
    async submit() {
      if (this.editItem.uid) {
        crfs.editNamespace(this.editItem.uid, this.form).then(
          () => {
            this.close()
          },
          () => {
            this.$refs.form.working = false
          }
        )
      } else {
        crfs.createNamespace(this.form).then(
          () => {
            this.close()
          },
          () => {
            this.$refs.form.working = false
          }
        )
      }
    },
    initForm(item) {
      this.form = item
    },
  },
}
</script>
