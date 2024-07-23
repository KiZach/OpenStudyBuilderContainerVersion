<template>
  <div>
    <div class="page-title d-flex align-center">
      {{ $t('DataModels.cdash') }}
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
          uid="CDASH"
          :redirect-model="redirectModel"
          @redirect-to-guide="redirectToGuide"
        />
      </v-window-item>
      <v-window-item value="guide">
        <DataExchangeStandardsGuideView
          :headers="igHeaders"
          uid="CDASHIG"
          :redirect-guide="redirectGuide"
          @redirect-to-model="redirectToModel"
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
  { tab: 'models', name: t('DataModels.cdash_models') },
  { tab: 'guide', name: t('DataModels.cdash_ig') },
])
const redirectModel = ref({})
const redirectGuide = ref({})
const modelsHeaders = ref([
  { title: t('DataModels.ordinal'), key: 'dataset_class.ordinal' },
  { title: t('_global.name'), key: 'uid' },
  { title: t('DataModels.label'), key: 'label' },
  { title: t('DataModels.definition'), key: 'description' },
  { title: t('DataModels.question_text'), key: 'question_text' },
  { title: t('DataModels.prompt'), key: 'prompt' },
  { title: t('DataModels.data_type'), key: 'simple_datatype' },
  { title: t('DataModels.impl_notes'), key: 'implementation_notes' },
  { title: t('DataModels.mapping_inst'), key: 'mapping_instructions' },
  { title: t('DataModels.mapping_targets'), key: 'has_mapping_target.uid' },
  { title: t('DataModels.code_list'), key: 'referenced_codelist.uid' },
])
const igHeaders = ref([
  { title: t('DataModels.ordinal'), key: 'dataset.ordinal' },
  { title: t('_global.name'), key: 'uid' },
  { title: t('DataModels.label'), key: 'label' },
  { title: t('DataModels.definition'), key: 'description' },
  { title: t('DataModels.question_text'), key: 'question_text' },
  { title: t('DataModels.prompt'), key: 'prompt' },
  { title: t('DataModels.data_type'), key: 'simple_datatype' },
  { title: t('DataModels.impl_notes'), key: 'implementation_notes' },
  { title: t('DataModels.mapping_inst'), key: 'mapping_instructions' },
  { title: t('DataModels.mapping_targets'), key: 'has_mapping_target.uid' },
  { title: t('DataModels.code_list'), key: 'referenced_codelist.uid' },
])

watch(tab, (newValue) => {
  const tabName = newValue
    ? tabs.value.find((el) => el.tab === newValue).name
    : tabs.value[0].name
  router.push({
    name: 'Cdash',
    params: { tab: newValue },
  })
  appStore.addBreadcrumbsLevel(
    tabName,
    { name: 'Cdash', params: { tab: tabName } },
    3,
    true
  )
})

function redirectToGuide(item) {
  redirectGuide.value = item
  tab.value = 'guide'
}
function redirectToModel(item) {
  redirectModel.value = item
  tab.value = 'models'
}

tab.value = route.params.tab || 'models'
</script>
