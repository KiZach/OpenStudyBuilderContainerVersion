<template>
  <div>
    <v-row>
      <v-col cols="1">
        <v-timeline density="compact" class="timeline-height">
          <v-timeline-item
            v-for="model of models"
            :key="model.start_date"
            :dot-color="activeModel === model ? 'primary' : 'grey'"
            size="small"
            right
          >
            <v-btn
              variant="text"
              :color="activeModel === model ? 'primary' : 'default'"
              @click="chooseModelVersion(model)"
            >
              v{{ model.version_number }}
            </v-btn>
          </v-timeline-item>
        </v-timeline>
      </v-col>
      <v-spacer />
      <v-col cols="11">
        <v-card class="mt-2 mb-2" elevation="6" max-width="99%">
          <v-card-text>
            <v-row>
              <v-col cols="1">
                <div class="font-weight-bold">
                  {{ $t('DataModels.status') }}
                </div>
                <p class="font-weight-regular">
                  {{ activeModel.status }}
                </p>
              </v-col>
              <v-col cols="3">
                <div class="font-weight-bold">
                  {{ $t('DataModels.effective_date') }}
                </div>
                <p class="font-weight-regular">
                  {{
                    activeModel.start_date
                      ? activeModel.start_date.substring(0, 10)
                      : ''
                  }}
                </p>
              </v-col>
              <v-col cols="3">
                <div class="font-weight-bold">
                  {{ $t('DataModels.implemented_by') }}
                </div>
                <div
                  v-for="guide of activeModel.implementation_guides"
                  :key="guide.name"
                >
                  <a
                    href="#"
                    class="font-weight-regular"
                    @click="redirectToGuide(guide)"
                    >{{ guide.name }}</a
                  >
                </div>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
        <div class="title font-weight-bold mt-6">
          {{ $t('DataModels.classes') }}
        </div>
        <v-row class="mt-2">
          <v-tabs v-model="activeTab" light>
            <v-tab v-for="tab of datasetClasses" :key="tab.uid" :href="tab.tab">
              {{ tab.uid.replaceAll('_', ' ') }}
            </v-tab>
          </v-tabs>
          <v-window v-model="activeTab">
            <v-window-item v-for="tab of datasetClasses" :key="tab.uid">
              <div>
                <v-card class="mt-2 mb-2 ml-1" elevation="6" max-width="1440px">
                  <v-card-text>
                    <v-row>
                      <v-col cols="2">
                        <div class="font-weight-bold">
                          {{ $t('_global.name') }}
                        </div>
                        <p class="font-weight-regular">
                          {{ tab.label }}
                        </p>
                      </v-col>
                      <v-col cols="1">
                        <div class="font-weight-bold">
                          {{ $t('DataModels.ordinal') }}
                        </div>
                        <p class="font-weight-regular">
                          {{
                            tab.data_models[0] ? tab.data_models[0].ordinal : ''
                          }}
                        </p>
                      </v-col>
                      <v-col cols="9">
                        <div class="font-weight-bold">
                          {{ $t('_global.description') }}
                        </div>
                        <p class="font-weight-regular">
                          {{ tab.description }}
                        </p>
                      </v-col>
                    </v-row>
                  </v-card-text>
                </v-card>
                <v-data-table
                  :loading="loading"
                  density="compact"
                  :headers="headers"
                  :items="variables"
                >
                  <template #[`item.referenced_codelist.uid`]="{ item }">
                    <a
                      href="#"
                      @click="openCodelistTerms(item.referenced_codelist.uid)"
                      >{{
                        item.referenced_codelist
                          ? item.referenced_codelist.uid
                          : ''
                      }}</a
                    >
                  </template>
                </v-data-table>
              </div>
            </v-window-item>
          </v-window>
        </v-row>
      </v-col>
    </v-row>
  </div>
</template>

<script>
import standards from '@/api/standards'

export default {
  props: {
    uid: {
      type: String,
      default: null,
    },
    redirectModel: {
      type: Object,
      default: null,
    },
    redirectClass: {
      type: Object,
      default: null,
    },
    headers: {
      type: Array,
      default: null,
    },
  },
  emits: ['redirectToGuide'],
  data() {
    return {
      models: [],
      activeModel: {},
      datasetClasses: [],
      activeClass: {},
      activeTab: 0,
      datasetTab: null,
      variables: [],
      loading: false,
      variableFilter: false,
    }
  },
  watch: {
    activeTab(value) {
      if (!this.variableFilter) {
        this.getVariables(this.datasetClasses[value].label)
      }
      this.variableFilter = false
    },
    redirectModel(value) {
      if (value && value.implementation) {
        this.variableFilter = true
        this.activeModel = this.models.find(
          (model) => model.name === value.implementation.name
        )
        this.activeTab = this.datasetClasses.findIndex(
          (el) => el.label === value.data[0].dataset_class.dataset_class_name
        )
        this.variables = value.data
      } else if (value) {
        this.chooseModelVersion(
          this.models.find((model) => model.name === value.name)
        )
      }
    },
  },
  mounted() {
    const params = {
      filters: { uid: { v: [this.uid], op: 'eq' } },
    }
    standards.getAllModels(params).then((resp) => {
      this.models = resp.data.items
      this.chooseModelVersion(this.models[0])
    })
  },
  methods: {
    openCodelistTerms(codelistUid) {
      this.$router.push({
        name: 'CodelistTerms',
        params: { codelist_id: codelistUid, catalogue_name: 'All' },
      })
    },
    redirectToGuide(item) {
      this.$emit('redirectToGuide', item)
    },
    chooseModelVersion(model) {
      this.activeModel = model
      const params = {
        filters: {
          'data_models.data_model_name': {
            v: [this.activeModel.name],
            op: 'eq',
          },
        },
        page_size: 0,
      }
      standards.getDatasetClasses(params).then((resp) => {
        resp.data.items.forEach((element) => {
          if (element.data_models.length > 1) {
            element.data_models = element.data_models.filter((element) => {
              return element.data_model_name === this.activeModel.name
            })
          }
        })
        this.datasetClasses = resp.data.items
        this.activeTab = 0
        this.getVariables(this.datasetClasses[0].label)
      })
    },
    getVariables(className) {
      this.loading = true
      this.variables = []
      const params = {
        dataset_class_name: className,
        data_model_name: this.activeModel.uid,
        data_model_version: this.activeModel.version_number,
        page_size: 0,
      }
      standards.getClassVariables(params).then((resp) => {
        this.variables = resp.data.items
        this.loading = false
      })
    },
  },
}
</script>
<style>
.timeline-height {
  height: auto !important;
}
</style>
