<template>
  <div class="pa-4 bg-white">
    <v-row>
      <v-col cols="4" class="d-flex align-center">
        <span class="text-h6">{{ $t('ProtocolFlowchart.title') }}</span>
        <span class="text-center font-italic flex-grow-1">{{
          loadingMessage
        }}</span>
      </v-col>
      <v-col cols="8" class="d-flex align-center">
        <v-spacer />
        <v-select
          v-model="layout"
          :label="$t('ProtocolFlowchart.layout')"
          :items="layouts"
          item-title="title"
          item-value="value"
          density="compact"
          :disabled="Boolean(loadingMessage)"
          class="layoutSelect mt-3 mr-4"
        />
        <v-switch
          v-model="soaPreferences.show_epochs"
          :label="$t('ProtocolFlowchart.show_epochs')"
          hide-details
          class="mr-4"
          color="primary"
          :disabled="disableSwitches"
          :readonly="soaContentLoadingStore.loading"
          :loading="soaContentLoadingStore.loading ? 'warning' : null"
          @update:model-value="updateSoaPreferences('show_epochs')"
        />
        <!-- <v-switch  // OFF for Release 1.6 ENABLE when Milestones get implemented
          v-model="soaPreferences.show_milestones"
          :label="$t('ProtocolFlowchart.show_milestones')"
          hide-details
          class="mr-4"
          color="primary"
          :disabled="disableSwitches ||
            selectedStudyVersion !== null
          "
          :readonly="soaContentLoadingStore.loading"
          :loading="soaContentLoadingStore.loading ? 'warning' : null"
          @update:model-value="updateSoaPreferences('show_milestones')"
        /> -->
        <v-menu rounded location="bottom">
          <template #activator="{ props }">
            <v-btn
              size="small"
              color="nnGreen1"
              class="ml-2 text-white"
              v-bind="props"
              :title="$t('DataTableExportButton.export')"
              icon="mdi-download-outline"
              :loading="soaContentLoadingStore.loading"
            />
          </template>
          <v-list>
            <v-list-item link @click="downloadCSV">
              <v-list-item-title>CSV</v-list-item-title>
            </v-list-item>
            <v-list-item link @click="downloadDocx">
              <v-list-item-title>DOCX</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>
      </v-col>
    </v-row>
    <div id="protocolFlowchart" class="mt-4" v-html="protocolFlowchart" />
  </div>
</template>

<script>
import { computed } from 'vue'
import study from '@/api/study'
import exportLoader from '@/utils/exportLoader'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useSoaContentLoadingStore } from '@/stores/soa-content-loading'
import unitConstants from '@/constants/units'
import units from '@/api/units'
import { useAccessGuard } from '@/composables/accessGuard'

export default {
  props: {
    update: {
      type: Number,
      default: 0,
    },
  },
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    const soaContentLoadingStore = useSoaContentLoadingStore()
    return {
      ...useAccessGuard(),
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
      selectedStudyVersion: computed(
        () => studiesGeneralStore.selectedStudyVersion
      ),
      soaPreferredTimeUnit: computed(
        () => studiesGeneralStore.soaPreferredTimeUnit
      ),
      soaPreferences: computed(() => studiesGeneralStore.soaPreferences),
      setSoaPreferences: studiesGeneralStore.setSoaPreferences,
      soaContentLoadingStore,
    }
  },
  data() {
    return {
      protocolFlowchart: '',
      loadingMessage: '',
      layout: 'compact',
      layouts: [
        { value: 'compact', title: this.$t('ProtocolFlowchart.compact') },
        { value: 'detailed', title: this.$t('ProtocolFlowchart.detailed') },
        {
          value: 'operational',
          title: this.$t('ProtocolFlowchart.operational'),
        },
      ],
      preferredTimeUnit: null,
      preferredTimeUnits: [],
    }
  },
  computed: {
    disableSwitches() {
      if ((this.layout === 'compact' && this.checkPermission(this.$roles.STUDY_WRITE)) && !this.selectedStudyVersion) return false
      return true
    },
  },
  watch: {
    layout(newVal, oldVal) {
      if (newVal !== oldVal) this.updateFlowchart()
    },
    update(newVal, oldVal) {
      if (newVal !== oldVal) this.updateFlowchart()
    },
  },
  mounted() {
    this.updateFlowchart()
    units
      .getBySubset(unitConstants.TIME_UNIT_SUBSET_STUDY_PREFERRED_TIME_UNIT)
      .then((resp) => {
        this.preferredTimeUnits = resp.data.items
      })
    if (this.soaPreferredTimeUnit) {
      this.preferredTimeUnit = this.soaPreferredTimeUnit.time_unit_name
    }
  },
  methods: {
    updateSoaPreferences(key) {
      this.setSoaPreferences({ [key]: this.soaPreferences[key] }).then(() => {
        this.updateFlowchart()
      })
    },
    updateFlowchart() {
      this.loadingMessage = this.$t('ProtocolFlowchart.loading')
      this.soaContentLoadingStore.changeLoadingState()
      if (this.soaPreferredTimeUnit) {
        this.preferredTimeUnit = this.soaPreferredTimeUnit.time_unit_name
      }
      const params = {
        detailed: this.layout === 'detailed' ? true : null,
        operational: this.layout === 'operational' ? true : null,
        time_unit: this.preferredTimeUnit,
      }
      study
        .getStudyProtocolFlowchartHtml(this.selectedStudy.uid, params)
        .then((resp) => {
          this.protocolFlowchart = resp.data
        })
        .then(this.finally)
        .catch(this.finally)
    },
    downloadDocx() {
      this.loadingMessage = this.$t('ProtocolFlowchart.downloading')
      this.soaContentLoadingStore.changeLoadingState()
      const params = {
        detailed: this.layout === 'detailed' ? true : null,
        operational: this.layout === 'operational' ? true : null,
      }
      study
        .getStudyProtocolFlowchartDocx(this.selectedStudy.uid, params)
        .then((response) => {
          let filename =
            this.selectedStudy.current_metadata.identification_metadata.study_id
          filename += ` ${this.layout} SoA.docx`
          exportLoader.downloadFile(
            response.data,
            response.headers['content-type'] ||
              'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            filename
          )
        })
        .then(this.finally)
        .catch(this.finally)
    },
    downloadCSV() {
      this.soaContentLoadingStore.changeLoadingState()
      if (this.layout == 'operational') {
        study
          .exportStudyProtocolSoa(this.selectedStudy.uid)
          .then((response) => {
            const filename =
              this.selectedStudy.current_metadata.identification_metadata
                .study_id + ' protocol SoA.csv'
            exportLoader.downloadFile(
              response.data,
              response.headers['content-type'],
              filename
            )
          })
          .then(this.finally)
          .catch(this.finally)
      } else {
        study
          .exportStudyOperationalSoa(this.selectedStudy.uid)
          .then((response) => {
            const filename =
              this.selectedStudy.current_metadata.identification_metadata
                .study_id + ' operational SoA.csv'
            exportLoader.downloadFile(
              response.data,
              response.headers['content-type'],
              filename
            )
          })
          .then(this.finally)
          .catch(this.finally)
      }
    },
    finally(error) {
      this.loadingMessage = ''
      this.soaContentLoadingStore.changeLoadingState()
      if (error) throw error
    },
  },
}
</script>

<style lang="scss">
.layoutSelect {
  max-width: 200px;
}
#protocolFlowchart {
  table {
    width: 100%;
    border-collapse: collapse;
    table-layout: auto;
    resize: both;

    &,
    & th,
    & td {
      border: 1px solid #ebe8e5;
      padding: 1px 3px;
    }

    & thead {
      background-color: rgb(var(--v-theme-tableGray));

      & th {
        border-color: white;
      }

      & .header1:nth-child(n + 2) {
        vertical-align: top;
        text-orientation: mixed;
      }

      & th:first-child {
        text-align: left;
      }
    }

    & tbody {
      & th {
        text-align: left;
        font-weight: normal;
      }

      & tr td:nth-child(n + 2) {
        text-align: center;
        vertical-align: middle;
      }

      & .soaGroup {
        text-transform: uppercase;
        background-color: #b1d5f2;
        font-weight: bold;
      }

      & .soaGroup ~ td {
        background-color: #b1d5f2;
      }

      & .group {
        background-color: #d8eaf8;
        font-weight: bold;
      }

      & .group ~ td {
        background-color: #d8eaf8;
      }

      & .subGroup:first-child {
        font-weight: bold;
        padding-left: 1em;
      }

      & .activity:first-child {
        padding-left: 1em;
      }

      & .activityInstance:first-child {
        padding-left: 2em;
        font-style: italic;
      }
    }
  }

  dl.footnotes {
    margin: 1em;

    display: grid;
    grid-template-columns: 1em auto;

    dt {
      font-size: 70%;
      vertical-align: top;
    }
  }
}
</style>
