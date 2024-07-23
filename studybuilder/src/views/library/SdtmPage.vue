<template>
  <div>
    <div class="page-title d-flex align-center">
      {{ $t('DataModels.sdtm') }}
      <HelpButton />
    </div>
    <v-tabs v-model="tab" bg-color="white">
      <v-tab v-for="item of tabs" :key="item.tab" :value="item.tab">
        {{ item.name }}
      </v-tab>
    </v-tabs>
    <v-window v-model="tab" class="bg-white">
      <v-window-item value="models">
        <DataExchangeStandardsModelsView
          :headers="modelsHeaders"
          uid="SDTM"
          :redirect-model="redirectModel"
          @redirect-to-guide="redirectToGuide"
        />
      </v-window-item>
      <v-window-item value="SDTMIG">
        <DataExchangeStandardsGuideView
          :headers="igHeaders"
          uid="SDTMIG"
          :redirect-guide="redirectGuide"
          @redirect-to-model="redirectToModel"
          @redirect-to-model-with-variable="redirectToModelWithVariable"
        />
      </v-window-item>
      <v-window-item value="SDTMIG__AP">
        <DataExchangeStandardsGuideView
          :headers="igHeaders"
          uid="SDTMIG__AP"
          :redirect-guide="redirectGuide"
          @redirect-to-model="redirectToModel"
          @redirect-to-model-with-variable="redirectToModelWithVariable"
        />
      </v-window-item>
      <v-window-item value="SDTMIG__MD">
        <DataExchangeStandardsGuideView
          :headers="igHeaders"
          uvalue="SDTMIG__MD"
          :redirect-guide="redirectGuide"
          @redirect-to-model="redirectToModel"
          @redirect-to-model-with-variable="redirectToModelWithVariable"
        />
      </v-window-item>
      <v-window-item value="SENDIG">
        <DataExchangeStandardsGuideView
          :headers="igHeaders"
          uvalue="SENDIG"
          :redirect-guide="redirectGuide"
          @redirect-to-model="redirectToModel"
          @redirect-to-model-with-variable="redirectToModelWithVariable"
        />
      </v-window-item>
      <v-window-item value="SENDIG__AR">
        <DataExchangeStandardsGuideView
          :headers="igHeaders"
          uvalue="SENDIG__AR"
          :redirect-guide="redirectGuide"
          @redirect-to-model="redirectToModel"
          @redirect-to-model-with-variable="redirectToModelWithVariable"
        />
      </v-window-item>
      <v-window-item value="SENDIG__DART">
        <DataExchangeStandardsGuideView
          :headers="igHeaders"
          uvalue="SENDIG__DART"
          :redirect-guide="redirectGuide"
          @redirect-to-model="redirectToModel"
          @redirect-to-model-with-variable="redirectToModelWithVariable"
        />
      </v-window-item>
      <v-window-item value="SENDIG__GENETOX">
        <DataExchangeStandardsGuideView
          :headers="igHeaders"
          uid="SENDIG__GENETOX"
          :redirect-guide="redirectGuide"
          @redirect-to-model="redirectToModel"
          @redirect-to-model-with-variable="redirectToModelWithVariable"
        />
      </v-window-item>
    </v-window>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import DataExchangeStandardsModelsView from '@/components/library/DataExchangeStandardsModelsView.vue'
import DataExchangeStandardsGuideView from '@/components/library/DataExchangeStandardsGuideView.vue'
import HelpButton from '@/components/tools/HelpButton.vue'

const appStore = useAppStore()
const { t } = useI18n()
const router = useRouter()
const route = useRoute()

const tab = ref(0)
const tabs = ref([
  { tab: 'models', name: t('DataModels.sdtm_models') },
  { tab: 'SDTMIG', name: t('DataModels.sdtm_ig') },
  { tab: 'SDTMIG__AP', name: t('DataModels.sdtmig_ap') },
  { tab: 'SDTMIG__MD', name: t('DataModels.sdtmig_md') },
  { tab: 'SENDIG', name: t('DataModels.sendig') },
  { tab: 'SENDIG__AR', name: t('DataModels.sendig_ar') },
  { tab: 'SENDIG__DART', name: t('DataModels.sendig_dart') },
  { tab: 'SENDIG__GENETOX', name: t('DataModels.sendig_genetox') },
])
const redirectModel = ref({})
const redirectGuide = ref({})
const modelsHeaders = ref([
  { title: t('DataModels.ordinal'), key: 'dataset_class.ordinal' },
  { title: t('_global.name'), key: 'uid' },
  { title: t('DataModels.label'), key: 'label' },
  { title: t('DataModels.data_type'), key: 'simple_datatype' },
  { title: t('DataModels.role'), key: 'role' },
  { title: t('DataModels.qualifies_variable'), key: 'qualifies_variable.uid' },
  {
    title: t('DataModels.described_value_domain'),
    key: 'described_value_domain',
  },
  { title: t('DataModels.notes'), key: 'notes' },
  { title: t('DataModels.usage_restrictions'), key: 'usage_restrictions' },
  { title: t('_global.description'), key: 'description' },
  { title: t('DataModels.c_code'), key: 'referenced_codelist.uid' },
  { title: t('DataModels.examples'), key: 'examples' },
])
const igHeaders = ref([
  { title: t('DataModels.ordinal'), key: 'dataset.ordinal' },
  { title: t('_global.name'), key: 'uid' },
  { title: t('DataModels.label'), key: 'label' },
  { title: t('DataModels.data_type'), key: 'simple_datatype' },
  { title: t('DataModels.role'), key: 'role' },
  { title: t('DataModels.core'), key: 'core' },
  { title: t('DataModels.codelist'), key: 'referenced_codelist.uid' },
  { title: t('DataModels.desc_value'), key: 'described_value_domain' },
  { title: t('DataModels.implements'), key: 'implements_variable.uid' },
  { title: t('DataModels.value_list'), key: 'value_list' },
  { title: t('_global.description'), key: 'description' },
])

watch(tab, (newValue) => {
  const tabName = newValue
    ? tabs.value.find((el) => el.tab === newValue).name
    : tabs.value[0].name
  router.push({
    name: 'Sdtm',
    params: { tab: newValue },
  })
  appStore.addBreadcrumbsLevel(
    tabName,
    { name: 'Sdtm', params: { tab: tabName } },
    3,
    true
  )
})

function redirectToGuide(item) {
  redirectGuide.value = item
  tab.value = tabs.value.indexOf(tabs.value.find((tab) => tab.tab === item.uid))
}
function redirectToModel(item) {
  redirectModel.value = item
  tab.value = 'models'
}
function redirectToModelWithVariable(data) {
  redirectModel.value = data
  tab.value = 'models'
}

tab.value = route.params.tab || 'models'
</script>
