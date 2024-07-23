<template>
  <v-menu rounded offset-y>
    <template #activator="{ props }">
      <v-btn
        size="small"
        color="nnGreen1"
        class="ml-2 white--text"
        v-bind="props"
        :title="$t('DataTableExportButton.export')"
        data-cy="table-export-button"
        icon="mdi-download-outline"
      />
    </template>
    <v-list>
      <v-list-item
        v-for="(format, index) in downloadFormats"
        :key="index"
        link
        @click="exportContent(format)"
      >
        <v-list-item-title>{{ format.name }}</v-list-item-title>
      </v-list-item>
    </v-list>
  </v-menu>
</template>

<script>
import { DateTime } from 'luxon'
import ExcelJS from 'exceljs'
import repository from '@/api/repository'
import exportLoader from '@/utils/exportLoader'

export default {
  props: {
    objectLabel: {
      type: String,
      default: '',
    },
    dataUrl: {
      type: String,
      default: '',
    },
    dataUrlParams: {
      type: Object,
      default: () => {},
    },
    headers: {
      type: Array,
      required: false,
      default: () => [],
    },
    items: {
      type: Array,
      required: false,
      default: () => [],
    },
  },
  emits: ['export'],
  data() {
    return {
      downloadFormats: [
        { name: 'CSV', mediaType: 'text/csv', extension: 'csv' },
        { name: 'JSON', mediaType: 'application/json', extension: 'json' },
        { name: 'XML', mediaType: 'text/xml', extension: 'xml' },
        {
          name: 'EXCEL',
          mediaType:
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
          extension: 'xlsx',
        },
      ],
    }
  },
  methods: {
    createDownloadLink(content, format) {
      const today = DateTime.local().toFormat('yyyyMMdd')
      const fileName = `MDRSB_Library_${this.objectLabel}_${today}.${format.extension}`
      exportLoader.downloadFile(content, format.mediaType, fileName)
    },
    getValue(header, item) {
      let value = item
      header.key.split('.').forEach((part) => {
        if (value !== undefined && value !== null) {
          value = value[part]
        }
      })
      if (value !== undefined) {
        if (typeof value === 'string') {
          return value.replace(/[\n]/g, '')
        }
        return value
      }
      return ''
    },
    convertHeaderLabelToName(label) {
      return label.toLowerCase().replace(/\s/g, '-')
    },
    exportToCSV() {
      const delimiter = ';'
      let csv =
        this.headers
          .filter((header) => header.key !== 'actions')
          .map((header) => header.title)
          .join(delimiter) + '\n'
      this.items.forEach((item) => {
        let row = ''
        this.headers.forEach((header) => {
          if (header.key === 'actions') {
            return
          }
          if (row !== '') {
            row += delimiter
          }
          const value = this.getValue(header, item)
          if (value !== undefined) {
            row += `"${value}"`
          }
        })
        csv += row + '\n'
      })
      return csv
    },
    async exportToXSLX() {
      const workbook = new ExcelJS.Workbook()
      const sheet = workbook.addWorksheet('Sheet 1')
      const headers = this.headers
        .filter((header) => header.key !== 'actions')
        .map((header) => {
          return { header: header.title, key: header.key }
        })
      const rows = []
      sheet.columns = headers
      this.items.forEach((item) => {
        const row = []
        this.headers.forEach((header) => {
          if (header.key === 'actions') {
            return
          }
          row.push(this.getValue(header, item))
        })
        rows.push(row)
      })
      sheet.addRows(rows)
      return await workbook.xlsx.writeBuffer()
    },
    /*
     ** Manual XML export.
     ** We could have used a DOM element and then use XMLSerializer() but the output is not formatted properly so...
     */
    exportToXML() {
      let result = '<items>\n'
      this.items.forEach((item) => {
        result += '  <item>\n'
        this.headers.forEach((header) => {
          if (header.key === 'actions') {
            return
          }
          const value = this.getValue(header, item)
          const name = this.convertHeaderLabelToName(header.title)
          result += `    <${name}>${value}</${name}>\n`
        })
        result += '  </item>\n'
      })
      result += '</items>\n'
      return result
    },
    exportToJSON() {
      const result = []
      this.items.forEach((item) => {
        const newItem = {}
        this.headers.forEach((header) => {
          if (header.key === 'actions') {
            return
          }
          const value = this.getValue(header, item)
          const name = this.convertHeaderLabelToName(header.title)
          newItem[name] = value
        })
        result.push(newItem)
      })
      return JSON.stringify(result)
    },
    async localExport(format) {
      let content = ''
      if (format.name === 'CSV') {
        content = this.exportToCSV()
      } else if (format.name === 'EXCEL') {
        content = await this.exportToXSLX()
      } else if (format.name === 'XML') {
        content = this.exportToXML()
      } else if (format.name === 'JSON') {
        content = this.exportToJSON()
      }
      this.createDownloadLink(content, format)
    },
    async exportContent(format) {
      const result = await new Promise((resolve) =>
        this.$emit('export', resolve)
      )
      if (!result) {
        return
      }
      if (this.items.length) {
        this.localExport(format)
        return
      }

      const headers = {}
      headers.Accept = format.mediaType
      const params = { ...this.dataUrlParams }
      if (params.page_size === undefined) {
        params.page_size = 0
      }
      repository
        .get(this.dataUrl, { params, headers, responseType: 'blob' })
        .then((response) => {
          this.createDownloadLink(response.data, format)
        })
    },
  },
}
</script>
