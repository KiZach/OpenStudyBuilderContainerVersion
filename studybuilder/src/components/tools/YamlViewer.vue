<template>
  <div>
    <div class="d-flex align-end mb-4">
      <v-text-field
        v-model="search"
        :label="$t('YamlViewer.search_content')"
        append-icon="mdi-magnify"
        hide-details
        clearable
        class="search-input mr-6"
        density="compact"
      />
      <v-switch
        :label="$t('YamlViewer.expand_all')"
        hide-details
        class="mr-auto"
        color="primary"
        @change="toggleTreeview"
      />
    </div>

    <v-treeview
      ref="tree"
      :items="yamlTree"
      :search="search"
      density="compact"
      open-on-click
      transition
      :open-all="expanded"
    />
  </div>
</template>

<script>
import YAML from 'yaml'

export default {
  props: {
    content: {
      type: String,
      default: '',
    },
  },
  data() {
    return {
      expanded: false,
      index: 0,
      search: null,
      yamlTree: null,
    }
  },
  watch: {
    content: {
      handler(value) {
        if (value) {
          const parsed = YAML.parse(value)
          this.renderTreeView(parsed)
        }
      },
      immediate: true,
    },
  },
  methods: {
    renderTreeView(obj) {
      const retValue = []

      for (const key in obj) {
        this.index += 1
        if (typeof obj[key] === 'object') {
          retValue.push({
            id: this.index,
            name: key,
            children: this.renderTreeView(obj[key]),
          })
        } else {
          if (!isNaN(key)) {
            retValue.push({ id: this.index, name: obj[key] })
          } else {
            let value = obj[key]
            if (typeof obj[key] === 'boolean') {
              value = !obj[key] ? 'no' : 'yes'
            }
            retValue.push({
              id: this.index,
              name: key,
              children: [{ id: this.index + 1, name: value }],
            })
            this.index += 1
          }
        }
      }
      this.yamlTree = retValue
      return retValue
    },
    toggleTreeview() {
      this.expanded = !this.expanded
      this.$refs.tree.updateAll(this.expanded)
    },
  },
}
</script>

<style lang="scss" scoped>
.search-input {
  min-width: 200px;
  max-width: 400px;
}
</style>
