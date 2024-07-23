<template>
  <v-radio-group
    :key="radioKey"
    v-model="value"
    density="compact"
    v-bind="$attrs"
  >
    <v-radio
      v-for="booleanValue in booleanValues"
      ref="radio"
      :key="booleanValue.id"
      :data-cy="'radio-' + booleanValue.label"
      :label="booleanValue.label"
      :value="booleanValue.value"
      color="primary"
      @mouseup="clearCurrentRadioValue(booleanValue)"
    />
  </v-radio-group>
</template>

<script>
export default {
  props: {
    modelValue: Boolean,
  },
  emits: ['update:modelValue'],
  data() {
    return {
      booleanValues: [
        { id: 1, label: this.$t('_global.yes'), value: true },
        { id: 2, label: this.$t('_global.no'), value: false },
      ],
      radioKey: 0,
    }
  },
  computed: {
    value: {
      get() {
        return this.modelValue
      },
      set(value) {
        this.$emit('update:modelValue', value)
      },
    },
  },
  methods: {
    clearCurrentRadioValue(value) {
      if (this.value !== null && value.value === this.value) {
        this.$emit('update:modelValue', null)
        this.radioKey += 1
      }
    },
  },
}
</script>
