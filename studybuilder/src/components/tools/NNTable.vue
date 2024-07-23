<template>
  <div>
    <v-card :elevation="elevation" class="rounded-0">
      <v-card-title
        style="z-index: 3; position: relative"
        class="pt-0 mt-3 d-flex align-center"
      >
        <template v-if="!hideDefaultSwitches">
          <div :title="$t('NNTableTooltips.select_rows')">
            <v-switch
              v-model="showSelectBoxes"
              data-cy="select-rows"
              :label="$t('NNTable.show_select_boxes_label')"
              class="mr-6"
              hide-details
              :title="$t('NNTableTooltips.select_rows')"
              color="primary"
            />
          </div>
        </template>
        <slot name="afterSwitches" />
        <v-spacer />
        <slot name="headerCenter" />
        <v-spacer />
        <slot name="beforeActions" />
        <v-radio-group
          v-if="showColumnNamesToggleButton"
          v-model="showColumnNames"
          inline
          density="compact"
          color="primary"
          hide-details
        >
          <v-radio :label="$t('NNTable.column_labels')" :value="false" />
          <v-radio :label="$t('NNTable.column_names')" :value="true" />
        </v-radio-group>
        <v-spacer />
        <div v-if="!hideActionsMenu" class="mt-3">
          <slot
            name="actions"
            :show-select-boxes="showSelectBoxes"
            :selected="selected"
          />
          <v-btn
            v-if="!disableFiltering && !onlyTextSearch"
            class="ml-2 text-white"
            size="small"
            color="light-blue darken-4"
            :title="$t('NNTableTooltips.filters')"
            data-cy="filters-button"
            icon="mdi-filter-outline"
            @click="showColumnsToFilterDialog = true"
          />
          <v-btn
            v-if="modifiableTable && !onlyTextSearch"
            class="ml-2 text-white"
            size="small"
            color="grey darken-3"
            :title="$t('NNTableTooltips.columns_layout')"
            data-cy="columns-layout-button"
            icon="mdi-table-column"
            @click="openColumnsDialog()"
          />
          <DataTableExportButton
            v-if="!hideExportButton"
            class="ml-2"
            :object-label="exportObjectLabel"
            :data-url="exportDataUrl"
            :data-url-params="exportDataUrlParams"
            :headers="headers"
            :items="selected.length ? selected : []"
            data-cy="export-data-button"
            @export="confirmExport"
          />
          <v-btn
            v-if="historyDataFetcher"
            class="ml-2"
            color="secondary"
            size="small"
            :title="$t('NNTableTooltips.history')"
            icon="mdi-history"
            @click="openHistory"
          />
        </div>
        <slot name="beforeTable" />
      </v-card-title>
      <v-card-text>
        <v-toolbar
          v-if="!disableFiltering"
          flat
          :class="additionalMargin ? 'pt-1 mt-3' : 'pt-1'"
          color="tableGray"
          style="height: 55px"
        >
          <v-text-field
            v-if="!hideSearchField || onlyTextSearch"
            v-model="search"
            density="compact"
            append-icon="mdi-magnify"
            :label="$t('_global.search')"
            single-line
            hide-details
            style="min-width: 200px; max-width: 300px"
            class="mr-4 mt-2 pt-0 mb-3 searchFieldLabel"
            data-cy="search-field"
          />
          <slot name="afterFilter" />
          <v-spacer />
          <div v-if="onlyTextSearch" class="mb-4">
            {{ $t('_global.filtering_to_add') }}
          </div>
          <v-slide-group show-arrows>
            <FilterAutocomplete
              v-for="item in itemsToFilter"
              :key="item.text"
              :clear-input="trigger"
              :item="item"
              :filters="savedFilters"
              :library="library"
              :resource="[columnDataResource, codelistUid]"
              :parameters="columnDataParameters"
              :initial-data="getColumnInitialData(item)"
              :selected-data="getColumnSelectedData(item)"
              :filters-modify-function="filtersModifyFunction"
              :table-items="items"
              @filter="columnFilter"
            />

            <v-btn
              icon="mdi-delete-outline"
              :title="$t('NNTableTooltips.clear_filters_content')"
              class="mb-3"
              @click="clearFilters()"
            />
          </v-slide-group>
        </v-toolbar>
        <ResizingDiv>
          <template #resizing-area="areaProps">
            <v-data-table-server
              v-model="selected"
              v-model:sort-by="sortBy"
              data-cy="data-table"
              :item-value="itemValue"
              return-object
              :show-select="showSelectBoxes"
              :items-per-page="computedItemsPerPage"
              :items-per-page-options="computedItemsPerPageOptions"
              :items-per-page-text="$t('Settings.rows')"
              class="py-4 mr-0"
              :row-props="rowProps"
              :loading="loading"
              :height="tableHeight || areaProps.areaHeight"
              :items="items"
              :search="search"
              :headers="shownColumns"
              :single-expand="singleExpand"
              :fixed-header="fixedHeader"
              :no-data-text="noDataText"
              disable-sort
              v-bind="$attrs"
              @update:options="filterTable"
            >
              <template
                v-for="header in shownColumns"
                :key="header.key"
                #[getHeaderSlotName(header)]
              >
                <div class="d-flex headerRow align-center">
                  <v-chip
                    v-if="header.color"
                    size="small"
                    :color="header.color"
                    class="mt-1 mr-1"
                  />
                  <div v-if="!showColumnNames">
                    {{ header.title }}
                  </div>
                  <div v-else class="mt-1">
                    {{ header.key }}
                  </div>
                  <v-icon v-if="sortBy.length && sortBy[0].key === header.key">
                    <template v-if="sortBy[0].order === 'asc'">
                      mdi-arrow-up-thin
                    </template>
                    <template v-else> mdi-arrow-down-thin </template>
                  </v-icon>
                  <v-menu
                    v-if="
                      header.title !== '' && modifiableTable && !onlyTextSearch
                    "
                    offset-y
                  >
                    <template #activator="{ props }">
                      <v-btn
                        icon
                        v-bind="props"
                        variant="plain"
                        class="pb-1"
                        @mouseover="columnValueIndex = header.key"
                      >
                        <v-icon v-show="header.key == columnValueIndex">
                          mdi-dots-vertical
                        </v-icon>
                      </v-btn>
                    </template>
                    <v-list v-if="modifiableTable && !onlyTextSearch">
                      <template v-for="(item, index) in headerActions">
                        <v-list-item
                          v-if="item.available"
                          :key="index"
                          @mouseover="columnValueIndex = header.key"
                          @mouseleave="columnValueIndex = ''"
                        >
                          <v-btn
                            variant="text"
                            class="disableUpperCase"
                            @click="item.click(header)"
                          >
                            {{
                              itemsToFilter[
                                itemsToFilter.findIndex(
                                  (el) => el.key === header.key
                                )
                              ] && item.label === $t('NNTable.add_to_filter')
                                ? $t('NNTable.remove_from_filter')
                                : item.label
                            }}
                          </v-btn>
                        </v-list-item>
                      </template>
                    </v-list>
                  </v-menu>
                </div>
              </template>
              <template
                v-for="(header, index) in shownColumns"
                #[`item.${header.key}`]="{ item }"
              >
                <v-tooltip
                  v-if="
                    getValueByColumn(item, header.key) &&
                    getValueByColumn(item, header.key).length > 60
                  "
                  :key="`tooltip-${index}`"
                  location="top"
                >
                  <template #activator="{ props }">
                    <span v-bind="props">{{
                      getValueByColumn(item, header.key).substring(0, 60) +
                      '...'
                    }}</span>
                  </template>
                  <span>{{ getValueByColumn(item, header.key) }}</span>
                </v-tooltip>
                <div v-else :key="`div-${index}`">
                  {{ getValueByColumn(item, header.key) }}
                </div>
              </template>
              <template v-for="(_, slot) of $slots" #[slot]="scope">
                <slot
                  :name="slot"
                  v-bind="scope"
                  :show-select-boxes="showSelectBoxes"
                />
              </template>
            </v-data-table-server>
          </template>
        </ResizingDiv>
      </v-card-text>
    </v-card>

    <v-dialog
      v-model="showColumnsDialog"
      max-width="550"
      persistent
      content-class="upperRight"
      tile
      @keydown.esc="showColumnsDialog = false"
    >
      <ColumnChoosingForm
        key="columnsForm"
        data-cy="show-columns-form"
        :opened="columnsOpened"
        :available-columns="headers"
        :table-name="$route.fullPath"
        :title="$t('ColumnChoosingForm.columnsTitle')"
        :restore-label="$t('ColumnChoosingForm.show_all_label')"
        @save="saveSelectedColumns"
        @close="closeColumnsDialog"
      />
    </v-dialog>

    <v-dialog
      v-model="showColumnsToFilterDialog"
      max-width="550"
      persistent
      content-class="upperRight"
      tile
      @keydown.esc="showColumnsToFilterDialog = false"
    >
      <ColumnChoosingForm
        key="filtersForm"
        data-cy="filters-select-form"
        :available-columns="headers"
        :already-in-filter="itemsToFilter"
        filtering
        :table-name="''"
        :title="$t('ColumnChoosingForm.filtersTitle')"
        :restore-label="$t('ColumnChoosingForm.clear_label')"
        @save="saveSelectedColumnsToFilter"
        @clear="clearData()"
        @close="showColumnsToFilterDialog = false"
      />
    </v-dialog>
    <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />

    <v-dialog
      v-model="showHistory"
      :fullscreen="$globals.historyDialogFullscreen"
      persistent
      @keydown.esc="closeHistory"
    >
      <HistoryTable
        :headers="historyHeaders"
        :items="historyItems"
        :items-total="historyItemsTotal"
        :title="historyTitle"
        :html-fields="historyHtmlFields"
        :simple-styling="historySimpleStyling"
        :change-field="historyChangeField"
        :change-field-label="historyChangeFieldLabel"
        :excluded-headers="historyExcludedHeaders"
        @close="closeHistory"
        @refresh="(options) => getHistoryData(options)"
      />
    </v-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, onUpdated, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAppStore } from '@/stores/app'
import { useFilteringParamsStore } from '@/stores/filtering-params'
import { useTablesLayoutStore } from '@/stores/library-tableslayout'
import ColumnChoosingForm from '@/components/tools/ColumnChoosingForm.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import DataTableExportButton from '@/components/tools/DataTableExportButton.vue'
import FilterAutocomplete from '../tools/FilterAutocomplete.vue'
import HistoryTable from './HistoryTable.vue'
import ResizingDiv from './ResizingDiv.vue'
import { i18n } from '@/plugins/i18n'
import { useRoute } from "vue-router"

const props = defineProps({
  headers: {
    type: Array,
    default: () => [],
  },
  defaultHeaders: {
    type: Array,
    default: () => [],
  },
  items: {
    type: Array,
    default: () => [],
  },
  itemValue: {
    type: String,
    default: '',
  },
  hideDefaultSwitches: {
    type: Boolean,
    default: false,
  },
  hideActionsMenu: {
    type: Boolean,
    default: false,
  },
  hideExportButton: {
    type: Boolean,
    default: false,
  },
  exportObjectLabel: {
    type: String,
    required: false,
    default: '',
  },
  exportDataUrl: {
    type: String,
    required: false,
    default: '',
  },
  exportDataUrlParams: {
    type: Object,
    required: false,
    default: undefined,
  },
  hideSearchField: {
    type: Boolean,
    default: false,
  },
  elevation: {
    type: String,
    default: '0',
  },
  showSelect: {
    type: Boolean,
    default: false,
  },
  showFilterBarByDefault: {
    type: Boolean,
    default: false,
  },
  defaultFilters: {
    type: Array,
    required: false,
    default: null,
  },
  initialFilters: {
    type: Object,
    required: false,
    default: undefined,
  },
  itemsPerPage: {
    type: Number,
    required: false,
    default: 10,
  },
  itemsPerPageOptions: {
    type: Array,
    required: false,
    default: null,
  },
  columnDataResource: {
    type: String,
    default: '',
  },
  columnDataParameters: {
    type: Object,
    default: undefined,
  },
  initialColumnData: {
    type: Object,
    default: undefined,
  },
  codelistUid: {
    type: String,
    default: '',
  },
  subTables: {
    type: Boolean,
    default: false,
  },
  historyDataFetcher: {
    type: Function,
    required: false,
    default: undefined,
  },
  historyTitle: {
    type: String,
    required: false,
    default: '',
  },
  historyHtmlFields: {
    type: Array,
    required: false,
    default: () => [],
  },
  historySimpleStyling: {
    type: Boolean,
    default: false,
  },
  historyChangeField: {
    type: String,
    required: false,
    default: '',
  },
  historyChangeFieldLabel: {
    type: String,
    required: false,
    default: '',
  },
  historyExcludedHeaders: {
    type: Array,
    required: false,
    default: () => [],
  },
  disableFiltering: {
    type: Boolean,
    default: false,
  },
  library: {
    type: String,
    default: '',
  },
  noDataText: {
    type: String,
    default: () => i18n.t('NNTable.no_data'),
  },
  filtersModifyFunction: {
    type: Function,
    required: false,
    default: undefined,
  },
  additionalMargin: {
    type: Boolean,
    default: false,
  },
  modifiableTable: {
    type: Boolean,
    default: true,
  },
  fixedHeader: {
    type: Boolean,
    default: true,
  },
  onlyTextSearch: {
    type: Boolean,
    default: false,
  },
  singleExpand: {
    type: Boolean,
    default: false,
  },
  showColumnNamesToggleButton: {
    type: Boolean,
    default: false,
  },
  extraItemClass: {
    type: Function,
    required: false,
    default: undefined,
  },
  loadingWatcher: {
    type: Boolean,
    required: false,
  },
  tableHeight: {
    type: String,
    default: null,
  },
  historyExternalHeaders: {
    type: Array,
    default: null,
  },
})
const emit = defineEmits(['filter'])

const { t } = useI18n()
const appStore = useAppStore()
const filteringParamsStore = useFilteringParamsStore()
const tablesLayoutStore = useTablesLayoutStore()
const route = useRoute()

const columnValueIndex = ref('')
const loading = ref(true)
const showSelectBoxes = ref(false)
const showFilterBar = ref(false)
const showColumnsDialog = ref(false)
const shownColumns = ref([])
const selected = ref([])
const search = ref('')
const itemsToFilter = ref([])
const historyItems = ref([])
const historyItemsTotal = ref(0)
const apiParams = new Map()
const trigger = ref(0)
const showColumnNames = ref(false)
const showColumnsToFilterDialog = ref(false)
const showHistory = ref(false)
const columnsOpened = ref(false)
const sortBy = ref([])
const selectedColumnData = ref({})
const confirm = ref()

const headerActions = [
  {
    label: t('NNTable.sort_asc'),
    click: sortAscending,
    available: true,
  },
  {
    label: t('NNTable.sort_desc'),
    click: sortDescending,
    available: true,
  },
  {
    label: t('NNTable.add_to_filter'),
    click: addToFilter,
    available: Boolean(!props.disableFiltering),
  },
  {
    label: t('NNTable.hide_column'),
    click: hideColumn,
    available: true,
  },
]
let timeout
let savedOptions
let savedFilters = '{}'

const filteringParams = computed(() => filteringParamsStore.filteringParams)
const computedItemsPerPage = computed(() => {
  return props.itemsPerPage ? props.itemsPerPage : appStore.userData.rows
})
const computedItemsPerPageOptions = computed(() => {
  return props.itemsPerPageOptions
    ? props.itemsPerPageOptions
    : [100, 15, 10, 5]
})
const historyHeaders = computed(() => {
  if (props.historyExternalHeaders) {
    return props.historyExternalHeaders
  }
  const result = [...props.headers]
  result.unshift({
    title: t('_global.uid'),
    key: props.itemValue,
  })
  return result
})

watch(
  route,
  () => {
    updateColumns()
  }
)
watch(
  () => props.loadingWatcher,
  (value) => {
    loading.value = value
  }
)
watch(
  () => props.headers,
  (value) => {
    shownColumns.value = value
  }
)
watch(
  () => props.items,
  (val) => {
    if (val) {
      loading.value = false
    }
  }
)
watch(showSelectBoxes, (val) => {
  if (!val) {
    selected.value = []
  }
})
watch(
  () => props.showSelect,
  (value) => {
    showSelectBoxes.value = value
  }
)
watch(itemsToFilter, () => {
  apiParams.forEach((value, key) => {
    const check = (obj) => obj.key === key
    if (!itemsToFilter.value.some(check)) {
      apiParams.delete(key)
    }
  })
})

onMounted(() => {
  showSelectBoxes.value = props.showSelect
  tablesLayoutStore.initiateColumns()
  filteringParamsStore.initiateFilteringParams()
  updateColumns()
  if (props.showFilterBarByDefault) {
    itemsToFilter.value = props.headers.filter(
      (header) => header.key !== 'actions' && !header.noFilter
    )
  } else if (props.defaultFilters) {
    itemsToFilter.value = props.defaultFilters
  }
  if (props.items && props.items.length) {
    loading.value = false
  }
  // For now we will implement saving of latest filtering only for Library Activities, it might change in the future
  if (
    filteringParams.value.tableName === window.location.pathname &&
    window.location.pathname.indexOf('library/activities') > 0
  ) {
    const map = JSON.parse(filteringParams.value.apiParams)
    for (const key in map) {
      if (key !== '*') {
        const newItem = shownColumns.value.find(
          (column) => column.value === key
        )
        if (
          newItem !== undefined &&
          !itemsToFilter.value.find((item) => item.text === newItem.text)
        ) {
          itemsToFilter.value.push(newItem)
        }
      } else {
        search.value = map[key][0]
      }
    }
    selectedColumnData.value = map
  }
  if (props.initialFilters !== undefined) {
    selectedColumnData.value = props.initialFilters
    const filters = {}
    for (const key in props.initialFilters) {
      filters[key] = { v: props.initialFilters[key] }
      apiParams.set(key, props.initialFilters[key])
    }
    filters.value = JSON.stringify(filters)
  }
})

onUpdated(() => {
  const headers = document.querySelectorAll(
    'div[class*="v-window-item--active"] th'
  )
  for (let index = 0; index < shownColumns.value.length; index++) {
    const header = headers[index]
    if (!header) {
      continue
    }
    header.addEventListener('mouseover', () => {
      columnValueIndex.value = shownColumns.value[index].key
    })
    header.addEventListener('mouseleave', () => {
      columnValueIndex.value = ''
    })
  }
})

function updateColumns() {
  if (!props.modifiableTable) {
    if (props.defaultHeaders && props.defaultHeaders.length !== 0) {
      shownColumns.value = props.defaultHeaders
    } else {
      shownColumns.value = JSON.parse(JSON.stringify(props.headers))
    }
    return
  }
  if (
    !tablesLayoutStore.columns[window.location.pathname] ||
    tablesLayoutStore.columns[window.location.pathname].length === 0
  ) {
    if (props.defaultHeaders && props.defaultHeaders.length !== 0) {
      shownColumns.value = props.defaultHeaders
    } else {
      shownColumns.value = JSON.parse(JSON.stringify(props.headers))
    }
  } else {
    shownColumns.value = tablesLayoutStore.columns[window.location.pathname]
    const check = new Set()
    shownColumns.value = shownColumns.value.filter(
      (obj) => !check.has(obj.key) && check.add(obj.key)
    )
  }
}
function openColumnsDialog() {
  columnsOpened.value = true
  showColumnsDialog.value = true
}
function closeColumnsDialog() {
  columnsOpened.value = false
  showColumnsDialog.value = false
}
function getValueByColumn(item, columnName) {
  const keys = columnName.split('.')
  return keys.reduce((acc, key) => (acc ? acc[key] : undefined), item)
}
function getHeaderSlotName(header) {
  return `header.${header.key}`
}
function getColumnInitialData(column) {
  return props.initialColumnData
    ? props.initialColumnData[column.key]
    : undefined
}
function getColumnSelectedData(column) {
  return selectedColumnData.value
    ? selectedColumnData.value[column.key]
    : undefined
}
function sortAscending(header) {
  sortBy.value = [{ key: header.key, order: 'asc' }]
  filterTable()
}
function sortDescending(header) {
  sortBy.value = [{ key: header.key, order: 'desc' }]
  filterTable()
}
function addToFilter(header) {
  if (
    itemsToFilter.value[
      itemsToFilter.value.findIndex((el) => el.key === header.key)
    ]
  ) {
    itemsToFilter.value.splice(
      itemsToFilter.value.findIndex((el) => el.key === header.key),
      1
    )
  } else {
    itemsToFilter.value.push(header)
  }
  filterBarDisplay()
}
function hideColumn(header) {
  shownColumns.value.splice(
    shownColumns.value.findIndex((el) => el.key === header.key),
    1
  )
  const layoutMap = new Map()
  layoutMap.set(window.location.pathname, shownColumns.value)
  tablesLayoutStore.setColumns(layoutMap)
}
function rowProps(data) {
  let result = props.subTables ? 'subRowsTable' : ''
  if (props.extraItemClass) {
    result += props.extraItemClass(data.item)
  }
  return {
    class: result,
  }
}
function saveSelectedColumns(columns) {
  shownColumns.value = columns
  if (shownColumns.value.length === 0) {
    shownColumns.value = props.headers
  }
  props.headers.some(hasAction)
  const check = new Set()
  shownColumns.value = shownColumns.value.filter(
    (obj) => !check.has(obj.key) && check.add(obj.key)
  )
}
function hasAction(element) {
  if (element.key === 'actions' && !shownColumns.value.includes('actions')) {
    shownColumns.value.push(element)
  }
}
function saveSelectedColumnsToFilter(columns) {
  if (columns.length === 0) {
    clearFilters()
    clearData()
  }
  itemsToFilter.value = columns
  filterBarDisplay()
}
function filterBarDisplay() {
  itemsToFilter.value = itemsToFilter.value.filter(function (element) {
    return element !== undefined
  })
  showFilterBar.value = true
}
function clearData() {
  clearFilters()
}
function clearFilters() {
  apiParams.clear()
  trigger.value += 1
  emit('filter')
}
function columnFilter(params) {
  apiParams.set(params.column, params.data)
  filterTable()
}
function filterTable(options) {
  loading.value = true
  if (timeout) clearTimeout(timeout)
  if (options) {
    savedOptions = options
  } else {
    options = savedOptions
  }
  if (options.search) {
    apiParams.set('*', [options.search])
  }
  timeout = setTimeout(() => {
    if (options.sortBy === undefined) {
      options.sortBy = sortBy.value
    }
    for (const elem of apiParams.entries()) {
      if (elem[1].length === 0) {
        apiParams.delete(elem[0])
      }
    }
    const newFilters = JSON.stringify(Object.fromEntries(apiParams))
      .replaceAll(':[', ':{"v":[')
      .replaceAll(']}', ']}}')
      .replaceAll('],', ']},')
    const filtersUpdated = savedFilters && newFilters !== savedFilters
    savedFilters = newFilters
    let index = savedFilters.indexOf('start_date')
    if (index === -1 && savedFilters.indexOf('Timestamp') !== -1) {
      index = savedFilters.indexOf('Timestamp')
    }
    if (index > -1) {
      const bracketIndex = savedFilters.indexOf(']', index) + 1
      savedFilters =
        savedFilters.substring(0, bracketIndex) +
        ', "op": "bw"' +
        savedFilters.substring(bracketIndex)
    }
    // For now we will implement saving of latest filtering only for Library Activities, it might change in the future
    if (window.location.pathname.indexOf('library/activities') >= 0) {
      filteringParamsStore.setFilteringParams({
        filters: savedFilters,
        tableName: window.location.pathname,
        apiParams: JSON.stringify(Object.fromEntries(apiParams)),
      })
    }
    emit('filter', savedFilters, options, filtersUpdated)
  }, 500)
}
async function confirmExport(resolve) {
  if (!selected.value.length) {
    const msg = t('NNTable.export_confirmation')
    if (!(await confirm.value.open(msg, { type: 'warning' }))) {
      resolve(false)
    }
  }
  resolve(true)
}
async function getHistoryData(options) {
  const resp = await props.historyDataFetcher(options)
  if (resp.items) {
    historyItems.value = resp.items
    historyItemsTotal.value = resp.total
  } else {
    historyItems.value = resp
    historyItemsTotal.value = resp.length
  }
}
async function openHistory() {
  await getHistoryData({ page: 1, itemsPerPage: 10 })
  showHistory.value = true
}
function closeHistory() {
  showHistory.value = false
}

defineExpose({
  filterTable,
})
</script>

<style>
.disableUpperCase {
  text-transform: capitalize;
}
.headerRow {
  flex-wrap: unset;
  max-height: 16px;
}
.upperRight {
  position: absolute;
  top: 50px;
  right: 0;
  border-radius: 0px;
}

.v-text-field .v-input__control .v-input__slot .v-text-field__slot {
  display: flex !important;
  min-height: 30px;
}

.v-text-field:not(.v-select--is-multi):not(.v-textarea--auto-grow)
  .v-input__control
  .v-input__slot {
  height: 30px !important;
}

.v-data-table__thead tr {
  white-space: nowrap;
}

.v-data-table__th {
  white-space: inherit;
  vertical-align: middle;
  padding-top: 20px !important;
  padding-bottom: 16px !important;
  background-color: rgb(var(--v-theme-tableGray)) !important;
  color: rgba(26, 26, 26, 0.6) !important;
  text-align: start;
  font-weight: 500;
  font-size: 14px;
}

.autocomplete {
  width: auto !important;
  margin-top: 5px !important;
}

.autocomplete .v-select__menu-icon {
  margin-top: 2px !important;
}

.full.v-autocomplete.v-select.v-text-field input {
  max-width: fit-content;
}

.empty.v-autocomplete.v-select.v-text-field input {
  max-width: 100px;
}
.calendar .v-field__field {
  padding-right: 10px !important;
  margin-top: 5px;
}

.calendar {
  margin-top: 0px !important;
  width: 180px;
  max-width: 180px;
}

.subRowsTable {
  background-color: #e3f2fd;
}

.searchFieldLabel.v-text-field label {
  font-size: 14px;
}
.warning {
  background-color: #eaab00;
}
.yellow {
  background-color: yellow;
}
</style>
