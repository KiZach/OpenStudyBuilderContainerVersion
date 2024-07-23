<template>
  <SimpleFormDialog
    ref="form"
    :title="title"
    :help-items="helpItems"
    :open="open"
    :form-url="formUrl"
    @close="cancel"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.name"
              :label="$t('CrfTemplates.name') + '*'"
              data-cy="crf-template-name"
              density="compact"
              clearable
              class="mt-3"
              :readonly="readOnly"
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.oid"
              :label="$t('CrfTemplates.oid')"
              data-cy="crf-template-oid"
              density="compact"
              clearable
              :readonly="readOnly"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="6">
            <v-menu
              v-model="effectiveDateMenu"
              :close-on-content-click="false"
              offset-y
              max-width="290px"
              min-width="290px"
            >
              <template #activator="{ props }">
                <v-text-field
                  :label="$t('CrfTemplates.effective_date')"
                  data-cy="crf-template-effective-date"
                  readonly
                  :model-value="effectiveDateDisp"
                  v-bind="props"
                />
              </template>
              <v-date-picker
                v-model="form.effective_date"
                locale="en-in"
                no-title
                data-cy="crf-template-effective-date-picker"
                :readonly="readOnly"
                @input="effectiveDateMenu = false"
              />
            </v-menu>
          </v-col>
          <v-col cols="6">
            <v-menu
              v-model="retiredDateMenu"
              :close-on-content-click="false"
              offset-y
              max-width="290px"
              min-width="290px"
            >
              <template #activator="{ props }">
                <v-text-field
                  :label="$t('CrfTemplates.retired_date')"
                  data-cy="crf-template-retired-date"
                  readonly
                  :model-value="retiredDateDisp"
                  v-bind="props"
                />
              </template>
              <v-date-picker
                v-model="form.retired_date"
                locale="en-in"
                no-title
                data-cy="crf-template-retired-date-picker"
                :readonly="readOnly"
                @input="retiredDateMenu = false"
              />
            </v-menu>
          </v-col>
        </v-row>
      </v-form>
    </template>
    <template #actions>
      <v-btn v-if="readOnly" class="primary mr-2" @click="newVersion">
        {{ $t('_global.new_version') }}
      </v-btn>
      <v-btn
        v-else-if="
          selectedTemplate && selectedTemplate.status === statuses.DRAFT
        "
        class="primary mr-2"
        @click="approve"
      >
        {{ $t('_global.approve') }}
      </v-btn>
    </template>
  </SimpleFormDialog>
</template>

<script>
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import crfs from '@/api/crfs'
import _isEqual from 'lodash/isEqual'
import statuses from '@/constants/statuses'
import { useFormStore } from '@/stores/form'

export default {
  components: {
    SimpleFormDialog,
  },
  inject: ['eventBusEmit', 'formRules'],
  props: {
    selectedTemplate: {
      type: Object,
      default: null,
    },
    open: Boolean,
    readOnlyProp: Boolean,
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
      helpItems: [
        'CrfTemplates.name',
        'CrfTemplates.oid',
        'CrfTemplates.effective_date',
        'CrfTemplates.retired_date',
      ],
      effectiveDateMenu: false,
      retiredDateMenu: false,
      readOnly: this.readOnlyProp,
    }
  },
  computed: {
    title() {
      return this.isEdit()
        ? this.$t('CrfTemplates.edit_template') + ' - ' + this.form.name
        : this.$t('CrfTemplates.add_template')
    },
    effectiveDateDisp() {
      if (this.form.effective_date) {
        return this.formatDate(this.form.effective_date)
      }
      return ''
    },
    retiredDateDisp() {
      if (this.form.retired_date) {
        return this.formatDate(this.form.retired_date)
      }
      return ''
    },
    formUrl() {
      if (this.isEdit()) {
        return `${window.location.href.replace('crf-tree', 'templates')}/template/${this.selectedTemplate.uid}`
      }
      return null
    },
  },
  watch: {
    selectedTemplate(value) {
      if (value) {
        this.form = { ...value }
        this.form.effective_date = new Date(this.form.effective_date)
        this.form.retired_date = new Date(this.form.retired_date)
        this.formStore.save(this.form)
      }
    },
    readOnlyProp(value) {
      this.readOnly = value
    },
  },
  created() {
    this.statuses = statuses
  },
  mounted() {
    if (this.isEdit()) {
      this.form = { ...this.selectedTemplate }
      this.form.effective_date = new Date(this.form.effective_date)
      this.form.retired_date = new Date(this.form.retired_date)
      this.formStore.save(this.form)
    }
  },
  methods: {
    formatDate(value) {
      if (value.length <= 10) {
        return value
      }
      let month = 1 + value.getMonth()
      if (month < 10) {
        month = `0${month}`
      }
      let day = value.getDate()
      if (day < 10) {
        day = `0${day}`
      }
      const date = `${value.getFullYear()}-${month}-${day}`
      if (date === '1970-01-01') {
        return null
      }
      return `${value.getFullYear()}-${month}-${day}`
    },
    newVersion() {
      crfs.newVersion('study-events', this.selectedTemplate.uid).then(() => {
        this.readOnly = false
      })
    },
    approve() {
      crfs.approve('study-events', this.selectedTemplate.uid).then(() => {
        this.readOnly = true
        this.close()
      })
    },
    async submit() {
      const { valid } = await this.$refs.observer.validate()
      if (!valid) return
      if (this.form.effective_date) {
        this.form.effective_date = this.formatDate(this.form.effective_date)
      }
      if (this.form.retired_date) {
        this.form.retired_date = this.formatDate(this.form.retired_date)
      }
      if (this.isEdit()) {
        crfs.updateTemplate(this.form, this.selectedTemplate.uid).then(
          () => {
            this.eventBusEmit('notification', {
              msg: this.$t('CrfTemplates.template_updated'),
            })
            this.close()
          },
          () => {
            this.$refs.form.working = false
          }
        )
      } else {
        crfs.createTemplate(this.form).then(
          () => {
            this.eventBusEmit('notification', {
              msg: this.$t('CrfTemplates.template_created'),
            })
            this.close()
          },
          () => {
            this.$refs.form.working = false
          }
        )
      }
    },
    async cancel() {
      if (
        this.storedForm === '' ||
        _isEqual(this.storedForm, JSON.stringify(this.form))
      ) {
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
      this.form = {}
      this.$refs.observer.reset()
      this.$emit('close')
    },
    isEdit() {
      if (this.selectedTemplate) {
        return Object.keys(this.selectedTemplate).length !== 0
      }
      return false
    },
  },
}
</script>
