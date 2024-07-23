<template>
  <v-card>
    <v-card-title class="pt-6 pb-0">
      <span class="headline">
        {{ title }}
      </span>
    </v-card-title>

    <v-card-text>
      <v-container>
        <v-row>
          <v-col cols="12" class="pl-0">
            <v-text-field
              v-model="search"
              :label="$t('ColumnChoosingForm.filtersSearch')"
              hide-details
              class="mb-3"
            />
            <v-switch
              v-for="item in filteredList"
              :key="item.key"
              v-model="displayedColumns"
              :label="item.title"
              :value="item"
              data-cy="toggle-button"
              color="primary"
              hide-details
            />
          </v-col>
        </v-row>
      </v-container>
    </v-card-text>
    <v-card-actions class="pb-6">
      <v-btn color="primary" @click="restoreDefaultsAndSave">
        {{ restoreLabel }}
      </v-btn>
      <v-spacer />
      <v-btn class="secondary-btn" color="white" @click="cancel">
        {{ $t('_global.cancel') }}
      </v-btn>
      <v-btn color="secondary" @click="save">
        {{ $t('_global.apply') }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
import _isEqual from 'lodash/isEqual'
import { computed } from 'vue'
import { useTablesLayoutStore } from '@/stores/library-tableslayout'

export default {
  props: {
    availableColumns: {
      type: Array,
      default: () => [],
    },
    tableName: {
      type: String,
      default: '',
    },
    title: {
      type: String,
      default: '',
    },
    restoreLabel: {
      type: String,
      default: '',
    },
    filtering: {
      type: Boolean,
      default: false,
    },
    alreadyInFilter: {
      type: Array,
      default: null,
    },
    opened: Boolean,
  },
  emits: ['clear', 'close', 'save'],
  setup() {
    const tablesLayoutStore = useTablesLayoutStore()

    return {
      columns: computed(() => tablesLayoutStore.columns),
      setColumns: tablesLayoutStore.setColumns,
    }
  },
  data() {
    return {
      displayedColumns: [],
      search: '',
      initialData: [],
    }
  },
  computed: {
    filteredList() {
      return this.availableColumns.filter((column) => {
        return (
          column.title.toLowerCase().includes(this.search.toLowerCase()) &&
          column.title !== ''
        )
      })
    },
  },
  watch: {
    opened(value) {
      if (value) {
        this.initialData = this.displayedColumns = this.columns[this.tableName]
        if (!this.initialData) {
          this.initialData = this.displayedColumns = this.availableColumns
        }
      }
    },
    columns(value) {
      if (!_isEqual(value[this.tableName], this.initialData)) {
        this.initialData = this.displayedColumns = value[this.tableName]
      }
    },
  },
  mounted() {
    this.initialData = this.displayedColumns = this.columns[this.tableName]
    if (this.isFiltering()) {
      this.initialData = this.displayedColumns = this.alreadyInFilter
    } else if (!this.initialData || this.initialData.length === 0) {
      this.initialData = this.displayedColumns = this.availableColumns
    }
  },
  methods: {
    restoreDefaultsAndSave() {
      this.displayedColumns = this.isFiltering() ? [] : this.availableColumns
      this.$emit('clear')
      this.save()
    },
    save() {
      if (!this.filtering) {
        const orderedColumns = this.availableColumns.filter((el) => {
          return this.displayedColumns.some((del) => el.key === del.key)
        })
        this.displayedColumns = orderedColumns
      }
      const actionsIndex = this.displayedColumns.findIndex(
        (i) => i.title === ''
      )
      if (actionsIndex !== -1) {
        this.displayedColumns.unshift(
          this.displayedColumns.splice(actionsIndex, 1)[0]
        )
      }
      this.$emit('save', this.displayedColumns)
      if (this.tableName !== '') {
        const layoutMap = new Map()
        layoutMap.set(this.tableName, this.displayedColumns)
        this.setColumns(layoutMap)
        this.initialData = this.displayedColumns
      }
      this.close()
    },
    close() {
      this.search = ''
      this.initialData = []
      this.$emit('close')
    },
    cancel() {
      this.displayedColumns = this.isFiltering()
        ? this.alreadyInFilter
        : this.initialData
      this.close()
    },
    isFiltering() {
      return this.filtering
    },
  },
}
</script>
