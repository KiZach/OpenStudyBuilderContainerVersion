<template>
  <v-tooltip v-if="valueExist()" bottom>
    <template #activator="{ props }">
      <v-icon color="darkGrey" v-bind="props">
        {{ getIcon() }}
      </v-icon>
    </template>
    <span>{{ getTooltip() }}</span>
  </v-tooltip>
</template>

<script>
export default {
  props: {
    item: {
      type: Object,
      default: null,
    },
    value: {
      type: String,
      default: null,
    },
  },
  methods: {
    valueExist() {
      if (this.item[this.value] === 'Yes') {
        return true
      } else if (this.value === 'refAttrs') {
        return this.item.vendor.attributes.length > 0
      } else if (this.value === 'dataType') {
        return this.item.datatype
      } else if (this.value === 'vendor') {
        return (
          this.item.vendor_attributes &&
          this.item.vendor_attributes.length +
            this.item.vendor_element_attributes.length +
            this.item.vendor_elements.length >
            0
        )
      }
      return false
    },
    getTooltip() {
      if (this.valueExist()) {
        switch (this.value) {
          case 'repeating':
            return this.$t('CrfTree.repeating')
          case 'locked':
            return this.$t('CrfTree.locked')
          case 'mandatory':
            return this.$t('CrfTree.mandatory')
          case 'is_reference_data':
            return this.$t('CrfTree.ref_data')
          case 'refAttrs':
            return this.$t('CrfTree.ref_vendor_extension_applied')
          case 'dataType':
            return this.item.datatype + this.$t('CrfTree.data_type')
          case 'vendor':
            return this.$t('CrfTree.vendor_extension_applied')
        }
      }
    },
    getIcon() {
      if (this.valueExist()) {
        switch (this.value) {
          case 'dataType':
            return this.getDataTypeIcon()
          case 'repeating':
            return 'mdi-repeat'
          case 'locked':
            return 'mdi-lock-outline'
          case 'mandatory':
            return 'mdi-database-lock'
          case 'is_reference_data':
            return 'mdi-arrow-decision-outline'
          case 'refAttrs':
            return 'mdi-toy-brick-plus-outline'
          case 'vendor':
            return 'mdi-toy-brick-plus-outline'
        }
      }
    },
    getDataTypeIcon() {
      switch (this.item.datatype.toUpperCase()) {
        case 'URI':
          return 'mdi-web'
        case 'STRING':
          return 'mdi-format-list-bulleted-square'
        case 'COMMENT':
        case 'TEXT':
          return 'mdi-alphabetical'
        case 'BOOLEAN':
        case 'HEXBINARY':
        case 'BASE64BINARY':
          return 'mdi-order-bool-ascending'
        case 'INTEGER':
        case 'FLOAT':
        case 'DOUBLE':
        case 'HEXFLOAT':
        case 'BASE64FLOAT':
          return 'mdi-numeric'
      }
      return 'mdi-calendar-clock'
    },
  },
}
</script>
