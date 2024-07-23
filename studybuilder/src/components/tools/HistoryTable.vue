<template>
  <v-card data-cy="version-history-window">
    <v-card-title class="d-flex align-center">
      <span class="dialog-title">{{ title }}</span>
      <v-spacer />
      <DataTableExportButton
        v-if="withExport"
        :headers="cleanedHeaders"
        :items="items"
        :object-label="exportFullName"
        @export="(resolve) => resolve(true)"
      />
    </v-card-title>
    <v-card-text>
      <v-data-table-server
        :headers="cleanedHeaders"
        :items="items"
        :items-length="itemsTotal"
        density="compact"
        @update:options="(options) => emit('refresh', options)"
      >
        <template #item="{ item }">
          <tr>
            <td
              v-for="(header, index) in cleanedHeaders"
              :key="index"
              :class="getTextClass(item)"
            >
              <div :class="getCellClasses(header, item)">
                <span
                  v-if="htmlFields && htmlFields.indexOf(header.key) !== -1"
                  v-html="getDisplay(item, header.key)"
                />
                <span v-else>{{ getDisplay(item, header.key) }}</span>
              </div>
            </td>
          </tr>
        </template>
      </v-data-table-server>
    </v-card-text>
    <v-card-actions v-if="!simpleStyling">
      <v-row>
        <v-col>
          <div>{{ $t('HistoryTable.legend') }}</div>
          <div class="ml-2 font-weight-black">
            {{ $t('HistoryTable.current_version') }}
          </div>
          <div class="ml-2">
            {{ $t('HistoryTable.older_version') }}
          </div>
          <div class="ml-2 text-red">
            {{ $t('HistoryTable.deleted_version') }}
          </div>
          <div class="ml-2 bg-blue-lighten-4 difference">
            {{ $t('HistoryTable.changed_value') }}
          </div>
        </v-col>
      </v-row>
    </v-card-actions>
    <v-card-actions>
      <v-spacer />
      <v-btn
        color="secondary"
        data-cy="close-button"
        variant="flat"
        @click="emit('close')"
      >
        {{ $t('_global.close') }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import DataTableExportButton from '@/components/tools/DataTableExportButton.vue'
import { DateTime } from 'luxon'

const { t } = useI18n()
const props = defineProps({
  headers: {
    type: Array,
    default: () => [],
  },
  excludedHeaders: {
    type: Array,
    required: false,
    default: () => [],
  },
  items: {
    type: Array,
    default: () => [],
  },
  itemsTotal: {
    type: Number,
    default: 0,
  },
  title: {
    type: String,
    default: '',
  },
  withExport: {
    type: Boolean,
    default: true,
  },
  exportName: {
    type: String,
    required: false,
    default: '',
  },
  htmlFields: {
    type: Array,
    required: false,
    default: () => [],
  },
  startDateHeader: {
    type: String,
    default: 'start_date',
  },
  endDateHeader: {
    type: String,
    default: 'end_date',
  },
  changeField: {
    type: String,
    default: 'change_type',
  },
  changeFieldLabel: {
    type: String,
    required: false,
    default: '',
  },
  simpleStyling: {
    type: Boolean,
    default: false,
  },
})
const emit = defineEmits(['close', 'refresh'])

const cleanedHeaders = computed(() => {
  let result = []
  const excludedHeaders = ['actions', 'user_initials', 'start_date']
  if (props.excludedHeaders) {
    for (const header of props.excludedHeaders) {
      excludedHeaders.push(header)
    }
  }
  for (const header of props.headers) {
    if (header.historyHeader) {
      header.key = header.historyHeader
    }
  }
  result = props.headers.filter((item) => {
    return !excludedHeaders.includes(item.key)
  })
  result.push({
    title: props.changeFieldLabel
      ? props.changeFieldLabel
      : t('HistoryTable.change_type'),
    key: props.changeField !== '' ? props.changeField : 'change_type',
  })
  result.push({
    title: t('_global.user'),
    key: 'user_initials',
  })
  result.push({
    title: t('HistoryTable.start_date'),
    key: props.startDateHeader,
  })
  result.push({
    title: t('HistoryTable.end_date'),
    key: props.endDateHeader,
  })
  return result
})
const exportFullName = computed(() => {
  let result = ''
  if (props.exportName) {
    result = props.exportName + '_'
  }
  result += 'history'
  return result
})

function getHighlight(header, item) {
  if (item) {
    if (
      header.key.indexOf('date') !== -1 ||
      header.key.indexOf('change_type') !== -1
    ) {
      return false
    } else if (item.changes) {
      if (header.key.indexOf('.') !== -1) {
        return item.changes[header.key.substring(0, header.key.indexOf('.'))]
      } else {
        return item.changes[header.key]
      }
    } else {
      return false
    }
  }
}
function getCellClasses(header, item) {
  if (props.simpleStyling) {
    return 'ml-3'
  }
  if (getHighlight(header, item)) {
    return 'bg-blue-lighten-4 difference ml-3'
  }
  return ''
}
function getTextClass(item) {
  if (props.simpleStyling) {
    return ''
  }
  if (item.change_type === 'Delete') {
    return 'text-red'
  } else if (!item.end_date) {
    return 'font-weight-black'
  } else {
    return ''
  }
}
function getDisplay(item, accessor) {
  const accessList = accessor.split('.')
  if (item) {
    let value = item
    for (const i in accessList) {
      const label = accessList[i]
      if (value) {
        value = value[label]
      }
    }
    if (accessor.toLowerCase().indexOf('date') !== -1) {
      if (value) {
        value = DateTime.fromISO(value)
          .setLocale('en')
          .toLocaleString(DateTime.DATETIME_MED)
      }
    }
    return value ? value.toString() : value
  }
}
</script>
