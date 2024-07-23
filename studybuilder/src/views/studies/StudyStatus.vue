<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('StudyStatusView.title') }} ({{ studiesGeneralStore.studyId }})
      <HelpButton width="800px">
        <div class="text-h6">
          {{ $t('_help.StudyStatus.core_attributes') }}
        </div>
        <div
          class="my-2"
          v-html="$t('_help.StudyStatus.core_attributes_body')"
        />
        <div class="text-h6">
          {{ $t('_help.StudyStatus.study_status') }}
        </div>
        <div class="my-2">
          {{ $t('_help.StudyStatus.content_line_1') }}
          <ul>
            <li v-html="$t('_help.StudyStatus.content_line_2')" />
            <li v-html="$t('_help.StudyStatus.content_line_3')" />
            <li v-html="$t('_help.StudyStatus.content_line_4')" />
          </ul>
          <p class="mt-2">
            {{ $t('_help.StudyStatus.content_line_5') }}
          </p>
          <p>{{ $t('_help.StudyStatus.content_line_6') }}</p>
        </div>
        <ul>
          <li>
            <span v-html="$t('_help.StudyStatus.content_line_7')" />
            <ul>
              <li v-html="$t('_help.StudyStatus.content_line_8')" />
            </ul>
          </li>
          <li>
            <span v-html="$t('_help.StudyStatus.content_line_9')" />
            <ul>
              <li v-html="$t('_help.StudyStatus.content_line_10')" />
            </ul>
          </li>
          <li>
            <span v-html="$t('_help.StudyStatus.content_line_11')" />
            <ul>
              <li v-html="$t('_help.StudyStatus.content_line_12')" />
            </ul>
          </li>
        </ul>

        <div class="text-h6 mt-2">
          {{ $t('_help.StudyStatus.study_sub_parts') }}
        </div>
        <div class="my-2">
          {{ $t('_help.StudyStatus.study_sub_parts_body') }}
        </div>
        <div class="text-h6">
          {{ $t('_help.StudyStatus.protocol_version') }}
        </div>
        <div class="my-2">
          {{ $t('_help.StudyStatus.protocol_version_body') }}
        </div>
      </HelpButton>
    </div>
    <v-tabs v-model="tab" bg-color="white">
      <v-tab v-for="item of tabs" :key="item.tab" :value="item.tab">
        {{ item.name }}
      </v-tab>
    </v-tabs>
    <v-window v-model="tab">
      <v-window-item value="core_attributes">
        <StudyIdentificationSummary />
      </v-window-item>
      <v-window-item value="study_status">
        <StudyStatusTable />
      </v-window-item>
      <v-window-item value="subparts">
        <StudySubpartsTable />
      </v-window-item>
      <v-window-item value="protocolversions">
        <UnderConstruction />
      </v-window-item>
    </v-window>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import HelpButton from '@/components/tools/HelpButton.vue'
import StudyIdentificationSummary from '@/components/studies/StudyIdentificationSummary.vue'
import StudyStatusTable from '@/components/studies/StudyStatusTable.vue'
import StudySubpartsTable from '@/components/studies/StudySubpartsTable.vue'
import UnderConstruction from '@/components/layout/UnderConstruction.vue'
import { useAppStore } from '@/stores/app'
import { useStudiesGeneralStore } from '@/stores/studies-general'

const appStore = useAppStore()
const studiesGeneralStore = useStudiesGeneralStore()
const { t } = useI18n()
const router = useRouter()
const route = useRoute()

const tab = ref(null)
const tabs = ref([
  { tab: 'core_attributes', name: t('StudyStatusView.tab1_title') },
  { tab: 'study_status', name: t('StudyStatusView.tab2_title') },
  { tab: 'subparts', name: t('StudyStatusView.tab3_title') },
  { tab: 'protocolversions', name: t('StudyStatusView.tab4_title') },
])

watch(tab, (newValue) => {
  const tabName = newValue
    ? tabs.value.find((el) => el.tab === newValue).name
    : tabs.value[0].name
  router.push({
    name: 'StudyStatus',
    params: { study_id: studiesGeneralStore.selectedStudy.uid, tab: newValue },
  })
  appStore.addBreadcrumbsLevel(
    tabName,
    {
      name: 'StudyStatus',
      params: { study_id: studiesGeneralStore.selectedStudy.uid, tab: tabName },
    },
    3,
    true
  )
})

tab.value = route.params.tab || tabs.value[0].tab
const tabName = tab.value
  ? tabs.value.find((el) => el.tab === tab.value).name
  : tabs.value[0].name
setTimeout(() => {
  appStore.addBreadcrumbsLevel(
    tabName,
    {
      name: 'StudyStatus',
      params: { study_id: studiesGeneralStore.selectedStudy.uid, tab: tabName },
    },
    3,
    true
  )
}, 100)
</script>
