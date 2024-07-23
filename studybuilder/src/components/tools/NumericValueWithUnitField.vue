<template>
  <div>
    <div class="d-flex">
      <v-text-field
        v-model="form.value"
        class="value-selector"
        :label="label"
        type="number"
        hide-details="auto"
        :disabled="disabled"
        density="compact"
        @input="update"
      />
      <v-select
        v-model="form.unit_definition_uid"
        class="unit-selector ml-4"
        :label="$t('DurationField.label')"
        :items="units"
        item-title="name"
        item-value="uid"
        density="compact"
        clearable
        hide-details="auto"
        :disabled="disabled"
        @input="update"
      />
    </div>
    <div class="mt-1 v-messages theme--light">
      <div class="v-messages__message">
        {{ hint }}
      </div>
    </div>
  </div>
</template>

<script>
import units from '@/api/units'

export default {
  props: {
    initialValue: {
      type: Object,
      default: undefined,
    },
    label: {
      type: String,
      default: '',
    },
    hint: {
      type: String,
      default: '',
    },
    subset: {
      type: String,
      default: '',
    },
    errors: {
      type: Array,
      default: () => [],
    },
    disabled: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['input'],
  data() {
    return {
      form: {},
      units: [],
    }
  },
  watch: {
    initialValue(val) {
      this.form = { ...val }
    },
  },
  created() {
    this.form = { ...this.initialValue }
  },
  mounted() {
    units.getBySubset(this.subset).then((resp) => {
      this.units = resp.data.items
    })
  },
  methods: {
    update() {
      this.$emit('input', this.form)
    },
  },
}
</script>

<style>
.value-selector {
  max-width: 100px;
}
.unit-selector {
  max-width: 200px;
}
</style>
