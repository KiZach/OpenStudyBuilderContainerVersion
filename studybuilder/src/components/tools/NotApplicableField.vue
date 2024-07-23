<template>
  <div>
    <label v-if="label" class="v-label">{{ label }}</label>
    <v-row class="align-center">
      <v-col cols="10">
        <slot name="mainField" :not-applicable="notApplicable" />
      </v-col>
      <v-col cols="2">
        <v-checkbox
          v-model="notApplicable"
          color="primary"
          data-cy="not-applicable-checkbox"
          :label="naLabel"
          hide-details
          :disabled="disabled"
          @change="cleanFunction"
        />
      </v-col>
    </v-row>
  </div>
</template>

<script>
import { i18n } from '@/plugins/i18n'

export default {
  props: {
    label: {
      type: String,
      default: '',
    },
    hint: {
      type: String,
      default: '',
    },
    naLabel: {
      type: String,
      default: () => i18n.t('_global.not_applicable'),
    },
    cleanFunction: {
      type: Function,
      default: undefined,
    },
    checked: Boolean,
    disabled: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      notApplicable: false,
    }
  },
  watch: {
    checked() {
      this.notApplicable = this.checked
    },
  },
  created() {
    this.notApplicable = this.checked
  },
  methods: {
    reset() {
      this.notApplicable = false
    },
  },
}
</script>
