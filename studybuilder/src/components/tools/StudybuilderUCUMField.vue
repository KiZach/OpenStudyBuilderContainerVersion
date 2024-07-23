<template>
  <div>
    <v-autocomplete
      :label="$t('UCUMUnitField.label')"
      :model-value="value"
      :items="ucumUnits"
      item-value="term_uid"
      item-title="name"
      return-object
      density="compact"
      clearable
      v-bind="$attrs"
      @update:model-value="update"
    />
  </div>
</template>

<script>
import dictionaries from '@/api/dictionaries'

export default {
  props: {
    modelValue: {
      type: Object,
      default: undefined,
    },
  },
  emits: ['update:modelValue'],
  data() {
    return {
      ucumUnits: [],
    }
  },
  mounted() {
    dictionaries.getCodelists('UCUM').then((resp) => {
      const params = {
        codelist_uid: resp.data.items[0].codelist_uid,
        page_size: 0,
      }
      dictionaries.getTerms(params).then((resp) => {
        this.ucumUnits = resp.data.items
        this.value = this.ucumUnits.find(
          (ucum) => ucum.term_uid === this.modelValue
        )
      })
    })
  },
  methods: {
    update(value) {
      this.$emit('update:modelValue', value)
    },
  },
}
</script>
