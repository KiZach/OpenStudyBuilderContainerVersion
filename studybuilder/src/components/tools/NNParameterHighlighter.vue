<template>
  <v-tooltip
    v-if="tooltip && name.length > tooltipLength"
    location="top"
    content-class="tooltip"
  >
    <template #activator="{ props }">
      <span v-bind="props">
        <div class="template-readonly" v-html="getShortVersion()" />
      </span>
    </template>
    <span>
      <div class="template-readonly" v-html="getFormatedParts()" />
    </span>
  </v-tooltip>
  <div v-else class="template-readonly" v-html="getFormatedParts()" />
</template>

<script>
export default {
  props: {
    value: {
      type: Array,
      default: () => [],
    },
    // the name including the parameters
    name: {
      type: String,
      default: '',
    },
    prefix: {
      type: String,
      default: '[',
    },
    postfix: {
      type: String,
      default: ']',
    },
    showPrefixAndPostfix: {
      type: Boolean,
      default: true,
    },
    parameters: {
      type: Array,
      default: () => [],
    },
    editionMode: {
      type: Boolean,
      default: false,
    },
    defaultColor: {
      type: String,
      default: 'green',
    },
    tooltip: {
      type: Boolean,
      default: true,
    },
    tooltipLength: {
      type: Number,
      default: 200,
    },
  },
  data: () => ({
    selectedParams: null,
  }),
  computed: {
    computedPostfix() {
      return this.postfix === '' ||
        this.postfix === null ||
        this.postfix === undefined
        ? ' '
        : this.postfix
    },
    nameParts() {
      const nameArray = []
      let parameterIndex = 0

      let chars = ''
      for (const char of this.name) {
        if (char === this.prefix) {
          nameArray.push({
            isParameter: false,
            value: chars,
          })
          if (this.showPrefixAndPostfix) {
            chars = char
          } else {
            chars = ''
          }
        } else if (char === this.computedPostfix) {
          if (this.showPrefixAndPostfix) {
            chars += char
          }
          nameArray.push({
            isParameter: true,
            index: parameterIndex,
            value: chars,
          })
          parameterIndex++
          chars = ''
        } else {
          chars += char
        }
      }
      nameArray.push({
        isParameter: false,
        value: chars,
      })
      return nameArray
    },
  },
  methods: {
    getNamePartClass(namePart) {
      if (!namePart.isParameter) {
        return 'preview-text text-black'
      }
      if (this.editionMode && this.parameters[namePart.index]) {
        if (
          !this.parameters.length ||
          !this.parameters[namePart.index].selectedValues ||
          !this.parameters[namePart.index].selectedValues.length
        ) {
          return 'preview-parameter'
        }
        return 'preview-parameter--selected'
      }
      return `parameter--${this.defaultColor}`
    },
    getFormatedParts() {
      let result = ''
      this.nameParts.forEach((namePart, index) => {
        if (namePart.isParameter) {
          result += `<span class="${this.getNamePartClass(namePart, index)}">${namePart.value.charAt(0).toUpperCase() + namePart.value.slice(1)}</span>`
        } else {
          result += namePart.value
        }
      })
      return result
    },
    getShortVersion() {
      const long = this.getFormatedParts()
      let short = ''
      let length = 0
      while (
        short.replace(/<\/?[^>]+(>|$)/g, '').length <= this.tooltipLength &&
        length < long.length
      ) {
        short += long[length]
        length++
      }
      return short + '<l>...'
    },
  },
}
</script>

<style lang="scss">
.template-readonly {
  min-height: 30px;

  p {
    margin-bottom: 4px;
  }
}
.preview-parameter {
  color: rgb(var(--v-theme-orange));

  &--selected {
    color: rgb(var(--v-theme-green));
  }
}
.parameter {
  &--orange {
    color: rgb(var(--v-theme-orange));
  }
  &--green {
    color: rgb(var(--v-theme-green));
  }
  &--primary {
    color: rgb(var(--v-theme-primary));
  }
}
.param-dropdown {
  width: 160px;
  display: inline-block;
}
.tooltip {
  opacity: 0.95 !important;
  background-color: lightgray !important;
  color: black;
  border: 1px solid #737373;
}
</style>
