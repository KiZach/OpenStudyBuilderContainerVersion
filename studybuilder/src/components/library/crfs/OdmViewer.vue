<template>
  <div>
    <!-- <v-app-bar flat color="#e5e5e5" class="mt-2" style="height: 60px"> -->
    <v-row v-if="!doc" class="mt-2 ml-2">
      <v-col cols="2">
        <v-select
          v-model="params.target_type"
          :items="types"
          :label="$t('OdmViewer.odm_element_type')"
          density="compact"
          clearable
          item-title="name"
          item-value="value"
          class="mt-2"
          @update:model-value="setElements()"
        />
      </v-col>
      <v-col cols="2">
        <v-select
          v-model="params.target_uid"
          :items="elements"
          :label="$t('OdmViewer.odm_element_name')"
          density="compact"
          clearable
          class="mt-2"
          item-title="name"
          item-value="uid"
        />
      </v-col>
      <v-col cols="2">
        <v-select
          v-model="element_status"
          :items="element_statuses"
          :label="$t('OdmViewer.element_status')"
          :default="element_statuses[0]"
          density="compact"
          class="mt-2"
        />
      </v-col>
      <v-col cols="5">
        <v-row>
          <v-radio-group
            v-model="params.stylesheet"
            :label="$t('OdmViewer.stylesheet')"
            row
            class="mt-7"
          >
            <v-radio :label="$t('OdmViewer.blank')" value="blank" />
            <v-radio :label="$t('OdmViewer.sdtm')" value="sdtm" />
          </v-radio-group>
          <v-btn
            v-show="params.target_uid && params.stylesheet"
            class="mt-7"
            size="small"
            color="primary"
            :label="$t('_global.load')"
            @click="loadXml"
          >
            {{ $t('OdmViewer.load') }}
          </v-btn>
        </v-row>
      </v-col>
    </v-row>
    <v-row v-else class="mt-0 ml-2">
      <v-btn
        class="ml-2 mt-1"
        size="small"
        color="primary"
        :label="$t('_global.load')"
        @click="clearXml"
      >
        {{ $t('OdmViewer.load_another') }}
      </v-btn>
      <v-btn
        v-show="doc"
        size="small"
        color="nnGreen1"
        class="ml-4 white--text"
        :title="$t('DataTableExportButton.export_xml')"
        :loading="xmlDownloadLoading"
        icon="mdi-file-xml-box"
        @click="downloadXml"
      />
      <v-btn
        v-show="doc !== ''"
        size="small"
        color="nnGreen1"
        class="ml-4 white--text"
        :title="$t('DataTableExportButton.export_pdf')"
        :loading="pdfDownloadLoading"
        icon="mdi-file-pdf-box"
        @click="downloadPdf"
      />
      <v-btn
        v-show="doc !== ''"
        size="small"
        color="nnGreen1"
        class="ml-4 white--text"
        :title="$t('DataTableExportButton.export_html')"
        :loading="htmlDownloadLoading"
        icon="mdi-file-document-outline"
        @click="downloadHtml"
      />
    </v-row>
    <div v-show="loading">
      <v-row align="center" justify="center" style="text-align: -webkit-center">
        <v-col cols="12" sm="4">
          <div class="text-h5">
            {{ $t('OdmViewer.loading_message') }}
          </div>
          <v-progress-circular
            color="primary"
            indeterminate
            size="128"
            class="ml-4"
          />
        </v-col>
      </v-row>
    </div>
    <div v-show="doc" class="mt-4">
      <iframe />
    </div>
  </div>
</template>

<script setup>
import crfs from '@/api/crfs'
import statuses from '@/constants/statuses'
import exportLoader from '@/utils/exportLoader'
import { DateTime } from 'luxon'
import { ref, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

const props = defineProps({
  typeProp: {
    type: String,
    default: null,
  },
  elementProp: {
    type: String,
    default: null,
  },
  refresh: {
    type: String,
    default: null,
  },
})
const emit = defineEmits(['clearUid'])
const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const element_statuses = [
  statuses.LATEST,
  statuses.FINAL,
  statuses.DRAFT,
  statuses.RETIRED,
]
const elements = ref([])
let xml = ''
const doc = ref(null)
const params = ref({
  target_type: 'study_event',
  stylesheet: 'sdtm',
  export_to: 'v1',
})
const loading = ref(false)
const xmlDownloadLoading = ref(false)
const pdfDownloadLoading = ref(false)
const htmlDownloadLoading = ref(false)
const types = [
  { name: t('OdmViewer.template'), value: 'study_event' },
  { name: t('OdmViewer.form'), value: 'form' },
  { name: t('OdmViewer.item_group'), value: 'item_group' },
  { name: t('OdmViewer.item'), value: 'item' },
]
const element_status = ref(statuses.LATEST)
let url = ''

watch(
  () => props.refresh,
  () => {
    if (props.refresh === 'odm-viewer' && url !== '') {
      const stateObj = { id: '100' }
      window.history.replaceState(stateObj, 'Loaded CRF', url)
    }
  }
)

watch(
  () => props.elementProp,
  () => {
    automaticLoad()
  }
)

onMounted(() => {
  automaticLoad()
})

function automaticLoad() {
  params.value.target_type = route.params.type
  params.value.target_uid = route.params.uid
  setElements()
  if (params.value.target_type && params.value.target_uid) {
    loadXml()
  }
}

function setElements() {
  if (params.value.target_type) {
    switch (params.value.target_type) {
      case 'study_event':
        crfs.get('study-events').then((resp) => {
          elements.value = resp.data.items
        })
        return
      case 'form':
        crfs.get('forms').then((resp) => {
          elements.value = resp.data.items
        })
        return
      case 'item_group':
        crfs.get('item-groups').then((resp) => {
          elements.value = resp.data.items
        })
        return
      case 'item':
        crfs.get('items').then((resp) => {
          elements.value = resp.data.items
        })
    }
  }
}

async function loadXml() {
  doc.value = ''
  loading.value = true
  params.value.status = element_status.value.toLowerCase()
  crfs.getXml(params.value).then((resp) => {
    const parser = new DOMParser()
    xml = parser.parseFromString(resp.data, 'application/xml')
    const xsltProcessor = new XSLTProcessor()
    crfs.getXsl(params.value.stylesheet).then((resp) => {
      const xmlDoc = parser.parseFromString(resp.data, 'text/xml')
      xsltProcessor.importStylesheet(xmlDoc)
      doc.value = new XMLSerializer().serializeToString(
        xsltProcessor.transformToDocument(xml)
      )

      var iframe = document.createElement('iframe')
      iframe.classList.add('frame')
      document.querySelector('iframe').replaceWith(iframe)
      var iframeDoc = iframe.contentDocument
      iframeDoc.write(doc.value)
      iframeDoc.close()

      loading.value = false
    })
  })
  router.push({
    name: 'Crfs',
    params: {
      tab: 'odm-viewer',
      type: params.value.target_type,
      uid: params.value.target_uid,
    },
  })
  url = `${window.location.href}`
  emit('clearUid')
}

function getDownloadFileName() {
  const stylesheet =
    params.value.stylesheet === 'odm_template_sdtmcrf.xsl'
      ? '_sdtm_crf_'
      : '_blank_crf_'
  const templateName = elements.value.filter(
    (el) => el.uid === params.value.target_uid
  )[0].name
  return `${templateName + stylesheet + DateTime.local().toFormat('yyyy-MM-dd HH:mm')}`
}

function downloadHtml() {
  htmlDownloadLoading.value = true
  exportLoader.downloadFile(doc, 'text/html', getDownloadFileName())
  htmlDownloadLoading.value = false
}

function downloadXml() {
  xmlDownloadLoading.value = true
  crfs.getXml(params.value).then((resp) => {
    exportLoader.downloadFile(resp.data, 'text/xml', getDownloadFileName())
    xmlDownloadLoading.value = false
  })
}

function downloadPdf() {
  pdfDownloadLoading.value = true
  crfs.getPdf(params.value).then((resp) => {
    exportLoader.downloadFile(
      resp.data,
      'application/pdf',
      getDownloadFileName()
    )
    pdfDownloadLoading.value = false
  })
}

function clearXml() {
  doc.value = null
  url = ''
  router.push({ name: 'Crfs', params: { tab: 'odm-viewer' } })
}
</script>
<style>
.frame {
  width: 100%;
  min-height: 1000px;
}
</style>
