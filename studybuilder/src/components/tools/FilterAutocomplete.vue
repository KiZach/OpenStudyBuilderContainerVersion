<template>
  <v-slide-group-item>
    <div class="mr-4">
      <v-menu v-if="isDate(item.key)" :close-on-content-click="false">
        <template #activator="{ props }">
          <v-text-field
            :label="
              data.length === 0
                ? item.title
                : data.length === 1
                  ? data[0]
                  : `${data[0]} - ${data[1]}`
            "
            append-icon="mdi-calendar-outline"
            readonly
            rounded
            class="mt-1 calendar filterAutocompleteLabel"
            density="compact"
            hide-details
            variant="plain"
            v-bind="props"
          />
        </template>
        <v-date-picker
          v-show="!monthPicker"
          v-model="data"
          :selected-items-text="$t('FilterAutocomplete.range_selected')"
          @input="filterDate()"
        >
          <v-btn variant="text" color="primary" @click="clear()">
            {{ $t('FilterAutocomplete.clear') }}
          </v-btn>
          <v-btn variant="text" color="primary" @click="switchCalendar()">
            {{ $t('FilterAutocomplete.month_picker') }}
          </v-btn>
        </v-date-picker>
        <v-date-picker
          v-show="monthPicker"
          v-model="data"
          month
          range
          :selected-items-text="$t('FilterAutocomplete.range_selected')"
          @input="filterDate()"
        >
          <v-btn variant="text" color="primary" @click="clear()">
            {{ $t('FilterAutocomplete.clear') }}
          </v-btn>
          <v-btn variant="text" color="primary" @click="switchCalendar()">
            {{ $t('FilterAutocomplete.day_picker') }}
          </v-btn>
        </v-date-picker>
      </v-menu>
      <v-select
        v-else
        ref="select"
        v-model="data"
        density="compact"
        clearable
        multiple
        variant="plain"
        :label="item.title"
        :class="isEmpty(item.key) ? 'autocomplete empty' : 'autocomplete full'"
        item-title=""
        :items="items"
        hide-details
        class="mt-4 select filterAutocompleteLabel"
        @input="getColumnData(item.key)"
        @update:model-value="filterTable"
      >
        <template #item="{ props }">
          <v-list-item
            class="fixed-width"
            v-bind="props"
            @click="props.onClick"
          >
            <template #prepend="{ isActive }">
              <v-list-item-action start>
                <v-checkbox-btn :model-value="isActive" />
              </v-list-item-action>
            </template>
            <template #title>
              {{ props.title.replace(/<\/?[^>]+(>)/g, '') }}
            </template>
            <v-tooltip activator="parent" location="bottom">
              {{ props.title.replace(/<\/?[^>]+(>)/g, '') }}
            </v-tooltip>
          </v-list-item>
        </template>
        <template #prepend-item>
          <v-row>
            <v-text-field
              v-model="searchString"
              class="pl-6"
              :placeholder="$t('FilterAutocomplete.search')"
            />
            <v-btn
              variant="text"
              size="small"
              icon="mdi-close"
              class="mr-3 mt-2"
              @click="close()"
            />
          </v-row>
        </template>
        <template #selection="{ index }">
          <div v-if="index === 0">
            <span class="items-font-size">{{
              typeof data[0] !== 'boolean'
                ? data[0].substring(0, 12) + '...'
                : data[0]
            }}</span>
          </div>
          <span v-if="index === 1" class="text-grey text-caption mr-1">
            (+{{ data.length - 1 }})
          </span>
        </template>
      </v-select>
    </div>
  </v-slide-group-item>
</template>

<script setup>
import { ref, watch } from 'vue'
import _isEmpty from 'lodash/isEmpty'
import columnData from '@/api/columnData'

const props = defineProps({
  item: {
    type: Object,
    default: null,
  },
  clearInput: {
    type: Number,
    default: 0,
  },
  conditional: {
    type: Boolean,
    default: false,
  },
  filters: {
    type: String,
    default: '',
  },
  resource: {
    type: Array,
    default: null,
  },
  library: {
    type: String,
    default: '',
  },
  parameters: {
    type: Object,
    default: undefined,
  },
  filtersModifyFunction: {
    type: Function,
    required: false,
    default: undefined,
  },
  initialData: {
    type: Array,
    required: false,
    default: null,
  },
  selectedData: {
    type: Array,
    required: false,
    default: null,
  },
  tableItems: {
    type: Array,
    required: true,
    default: null,
  },
})
const emit = defineEmits(['filter'])

const data = ref([])
const items = ref([])
const searchString = ref('')
const monthPicker = ref(false)
const select = ref()
const timeout = ref(null)

watch(searchString, () => {
  if (timeout.value) clearTimeout(timeout.value)
  timeout.value = setTimeout(() => {
    getColumnData(props.item.key)
  }, 500)
})
watch(
  () => props.clearInput,
  () => {
    clear()
  }
)
watch(
  () => props.tableItems,
  (newValue, oldValue) => {
    if (_isEmpty(oldValue)) {
      getColumnData(props.item.key)
    }
  }
)

function close() {
  searchString.value = ''
  select.value.blur()
}
function switchCalendar() {
  monthPicker.value = !monthPicker.value
}

function clear() {
  data.value = []
  filterTable()
}

function isDate() {
  if (Date.parse(new Date(items.value[0])) && items.value[0].length > 20) {
    return true
  } else {
    return false
  }
}

function isEmpty() {
  if (data.value.length > 0) {
    return false
  }
  return true
}

function getColumnData(value) {
  if (value === 'actions') {
    return []
  }
  let jsonFilter = JSON.parse(props.filters)
  delete jsonFilter[value]
  if (props.item.exludeFromHeader) {
    props.item.exludeFromHeader.forEach((header) => {
      delete jsonFilter[header]
    })
  }
  let params = {
    field_name: props.item.externalFilterSource
      ? props.item.externalFilterSource.substring(
          props.item.externalFilterSource.indexOf('$') + 1
        )
      : props.item.filteringName
        ? props.item.filteringName
        : value,
    search_string: searchString.value,
    result_count: 20,
  }
  if (props.parameters) {
    params = Object.assign(params, props.parameters)
  }
  if (props.filtersModifyFunction) {
    const filters = props.filtersModifyFunction(jsonFilter, params)
    jsonFilter = filters.jsonFilter
    params = filters.params
  }
  if (!_isEmpty(jsonFilter)) {
    params.filters = jsonFilter
  }
  if (props.resource[1] !== undefined) {
    params.codelist_uid = props.resource[1]
  }
  if (props.library) {
    params.library = props.library
  }
  let externalFilter = props.resource[0]
  if (props.item.externalFilterSource) {
    externalFilter = props.item.externalFilterSource.substring(
      0,
      props.item.externalFilterSource.indexOf('$')
    )
  }
  if (props.item.disableColumnFilters) {
    params.filters = {}
  }
  columnData.getHeaderData(params, externalFilter).then((resp) => {
    items.value = booleanValidator(resp.data)
    items.value = items.value.filter((element) => {
      return element !== ''
    })
    if (typeof items.value[0] === 'object') {
      const deconstructedItems = []
      items.value.forEach((item) => {
        if (item.length > 1) {
          item.forEach((i) => {
            deconstructedItems.push(i.name)
          })
        } else if (item.length !== 0) {
          deconstructedItems.push(item[0].name)
        }
      })
      items.value = Array.from(new Set(deconstructedItems))
    }
    if (props.initialData) {
      items.value = items.value.filter(
        (item) => props.initialData.indexOf(item) !== -1
      )
    }
  })
}

function filterDate() {
  let dateData = []
  if (data.value[0].length === 7) {
    if (data.value.length === 1) {
      dateData = [data.value[0] + '-01', getSecondDay(data.value[0], 30)]
    } else {
      dateData = [data.value[0] + '-01', getSecondDay(data.value[1], 30)]
    }
  } else {
    if (data.value.length === 1) {
      dateData = [data.value[0], getSecondDay(data.value[0], 1)]
    } else {
      dateData = [data.value[0], getSecondDay(data.value[1], 1)]
    }
  }
  emit('filter', { column: props.item.key, data: dateData })
}

function booleanConverter(value) {
  if (value === 'No' || value === false) {
    return value === 'No' ? false : 'No'
  } else {
    return value === 'Yes' ? true : 'Yes'
  }
}

function booleanValidator(array) {
  if (array.length <= 2 && (array[0] === false || array[0] === true)) {
    array.forEach((el) => {
      const index = array.indexOf(el)
      array[index] = booleanConverter(array[index])
    })
  }
  return array
}

function filterTable() {
  if (
    data.value.length <= 2 &&
    (data.value[0] === 'Yes' || data.value[0] === 'No')
  ) {
    const requestData = []
    data.value.forEach((el) => {
      const index = data.value.indexOf(el)
      requestData.push(booleanConverter(data.value[index]))
    })
    emit('filter', {
      column: props.item.filteringName
        ? props.item.filteringName
        : props.item.key,
      data: requestData,
    })
  } else {
    emit('filter', {
      column: props.item.filteringName
        ? props.item.filteringName
        : props.item.key,
      data: data.value,
    })
  }
}

function getSecondDay(day, days) {
  const date = new Date(Date.parse(day))
  return new Date(date.setDate(date.getDate() + days))
    .toISOString()
    .split('T')[0]
}

if (!props.initialData && props.tableItems && props.tableItems.length) {
  getColumnData(props.item.key)
} else if (props.initialData) {
  items.value = [...props.initialData]
}

if (props.selectedData) {
  data.value = props.selectedData
}
</script>

<style scoped lang="scss">
.v-list {
  max-width: 300px !important;
}
.select {
  width: 300px !important;
}
.fixed-width {
  max-width: 250px !important;
}
.items-font-size {
  font-size: 14px;
}
.v-select__content {
  max-width: 250px;
}
</style>
