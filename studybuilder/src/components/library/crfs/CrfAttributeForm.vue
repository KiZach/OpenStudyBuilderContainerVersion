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
              :label="$t('CrfExtensions.attr_name')"
              density="compact"
              clearable
              :rules="[formRules.required]"
            />
          </v-col>
          <v-col cols="6">
            <v-select
              v-model="form.data_type"
              :label="$t('CrfExtensions.data_type')"
              :items="dataTypes"
              item-title="code_submission_value"
              item-value="code_submission_value"
              :rules="[formRules.required]"
              density="compact"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col v-if="parentType === crfTypes.NAMESPACE" cols="6">
            <v-select
              v-model="form.compatible_types"
              :label="$t('CrfExtensions.compatible_types')"
              :items="compatibleTypes"
              density="compact"
              multiple
              clearable
            />
          </v-col>
          <v-col cols="6">
            <v-text-field
              v-model="form.value_regex"
              :label="$t('CrfExtensions.regex_expression')"
              density="compact"
              clearable
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
import terms from '@/api/controlledTerminology/terms'
import crfTypes from '@/constants/crfTypes'

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
    parentUid: {
      type: String,
      default: null,
    },
    parentType: {
      type: String,
      default: null,
    },
  },
  emits: ['close'],
  data() {
    return {
      form: {},
      helpItems: [],
      dataTypes: [],
      compatibleTypes: [
        'FormDef',
        'ItemGroupDef',
        'ItemDef',
        'ItemGroupRef',
        'ItemRef',
      ],
    }
  },
  computed: {
    title() {
      return this.editItem.uid
        ? this.$t('CrfExtensions.edit_attr')
        : this.$t('CrfExtensions.new_attr')
    },
  },
  watch: {
    editItem(value) {
      this.initForm(value)
    },
  },
  created() {
    this.crfTypes = crfTypes
  },
  mounted() {
    terms.getAttributesByCodelist('dataType').then((resp) => {
      this.dataTypes = resp.data.items
    })
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
      if (this.parentType === crfTypes.NAMESPACE) {
        this.form.vendor_namespace_uid = this.parentUid
      } else {
        this.form.vendor_element_uid = this.parentUid
      }
      if (this.editItem.uid) {
        await crfs.editAttribute(this.editItem.uid, this.form).then(
          () => {
            this.close()
          },
          () => {
            this.$refs.form.working = false
          }
        )
      } else {
        await crfs.createAttribute(this.form).then(
          () => {
            this.close()
          },
          () => {
            this.$refs.form.working = false
          }
        )
      }
      this.close()
    },
    initForm(item) {
      this.form = item
    },
  },
}
</script>
