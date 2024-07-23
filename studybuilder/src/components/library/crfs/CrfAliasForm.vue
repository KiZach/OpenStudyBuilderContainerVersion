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
          <v-col>
            <v-text-field
              v-model="form.context"
              :label="$t('CrfAliases.context')"
              density="compact"
              clearable
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.name"
              :label="$t('CrfAliases.name')"
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
import { useFormStore } from '@/stores/form'

export default {
  components: {
    SimpleFormDialog,
  },
  inject: ['eventBusEmit', 'formRules'],
  props: {
    editedItem: {
      type: Object,
      default: null,
    },
    open: Boolean,
  },
  emits: ['close'],
  setup() {
    const formStore = useFormStore()
    return {
      formStore,
    }
  },
  data() {
    return {
      form: {},
      helpItems: ['CrfAliases.context', 'CrfAliases.name'],
    }
  },
  computed: {
    title() {
      return Object.keys(this.editedItem).length !== 0
        ? this.$t('CrfAliases.edit_alias')
        : this.$t('CrfAliases.add_alias')
    },
  },
  watch: {
    editedItem(value) {
      if (Object.keys(value).length !== 0) {
        this.form = value
        this.formStore.save(this.form)
      }
    },
  },
  mounted() {
    if (Object.keys(this.editedItem).length !== 0) {
      this.form = this.editedItem
      this.formStore.save(this.form)
    }
  },
  methods: {
    async cancel() {
      if (this.formStore.isEmpty || this.formStore.isEqual(this.form)) {
        this.close()
      } else {
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
      }
    },
    close() {
      this.$emit('close')
      this.form = {}
      this.formStore.reset()
      this.$refs.observer.reset()
    },
    async submit() {
      this.form.library_name = 'Sponsor'
      if (Object.keys(this.editedItem).length !== 0) {
        crfs.editAlias(this.editedItem.uid, this.form).then(
          () => {
            this.eventBusEmit('notification', {
              msg: this.$t('CrfAliases.alias_edited'),
            })
            this.close()
          },
          () => {
            this.$refs.form.working = false
          }
        )
      } else {
        crfs.addAlias(this.form).then(
          () => {
            this.eventBusEmit('notification', {
              msg: this.$t('CrfAliases.alias_created'),
            })
            this.close()
          },
          () => {
            this.$refs.form.working = false
          }
        )
      }
    },
  },
}
</script>
