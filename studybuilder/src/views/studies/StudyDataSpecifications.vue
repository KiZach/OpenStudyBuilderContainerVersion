<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('StudyDataSpecifications.title') }} ({{
        studiesGeneralStore.studyId
      }})
      <v-spacer/>
      <v-btn
        color="primary"
        size="small"
        icon="mdi-cog-outline"
        :disabled="lockSettings"
        :loading="soaContentLoadingStore.loading"
        @click="openSoaSettings"
      />
    </div>
    <v-tabs v-model="tab" bg-color="white">
      <v-tab v-for="item of tabs" :key="item.tab" :value="item.tab" :loading="(soaContentLoadingStore.loading && ['operational'].indexOf(item.tab) > -1) ? 'warning' : null">
        {{ item.name }}
      </v-tab>
    </v-tabs>
    <v-window v-model="tab">
      <v-window-item value="instances">
        <StudyActivityInstancesTable />
      </v-window-item>
      <v-window-item value="operational">
        <OperationalSoa :update="updateSoa"/>
      </v-window-item>
    </v-window>
    <v-dialog v-model="showSoaSettings" max-width="800px">
      <SoaSettingsForm
        @close="closeSoaSettings"
      />
    </v-dialog>
  </div>
</template>

<script setup>
import StudyActivityInstancesTable from '@/components/studies/StudyActivityInstancesTable.vue'
import OperationalSoa from '@/components/studies/OperationalSoa.vue'
import SoaSettingsForm from '@/components/studies/SoaSettingsForm.vue'
import { useAppStore } from '@/stores/app'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useI18n } from 'vue-i18n'
import { inject, computed, watch, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAccessGuard } from '@/composables/accessGuard'
import { useSoaContentLoadingStore } from '@/stores/soa-content-loading'

const appStore = useAppStore()
const studiesGeneralStore = useStudiesGeneralStore()
const soaContentLoadingStore = useSoaContentLoadingStore()
const accessGuard = useAccessGuard()
const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const roles = inject('roles')

const tab = ref(null)
const tabs = [
  { tab: 'instances', name: t('StudyDataSpecifications.tab1_title') },
  { tab: 'operational', name: t('StudyDataSpecifications.tab2_title') },
]
const showSoaSettings = ref(false)
const updateSoa = ref(0)

const lockSettings = computed(() => {
  if(!accessGuard.checkPermission(roles.STUDY_WRITE) || studiesGeneralStore.selectedStudyVersion !== null) {
    return true
  }
  return false
})

function openSoaSettings() {
  showSoaSettings.value = true
}

function closeSoaSettings() {
  updateSoa.value++
  showSoaSettings.value = false
}

watch(tab, (newValue) => {
  const tabName = newValue
    ? tabs.find((el) => el.tab === newValue).name
    : tabs[0].name
  router.push({
    name: 'StudyDataSpecifications',
    params: { study_id: studiesGeneralStore.selectedStudy.uid, tab: newValue },
  })
  appStore.addBreadcrumbsLevel(
    tabName,
    {
      name: 'StudyDataSpecifications',
      params: { study_id: studiesGeneralStore.selectedStudy.uid, tab: tabName },
    },
    3,
    true
  )
})

onMounted(() => {
  tab.value = route.params.tab || tabs[0].tab
  const tabName = tab.value
    ? tabs.find((el) => el.tab === tab.value).name
    : tabs[0].name
  setTimeout(() => {
    appStore.addBreadcrumbsLevel(
      tabName,
      {
        name: 'StudyDataSpecifications',
        params: {
          study_id: studiesGeneralStore.selectedStudy.uid,
          tab: tabName,
        },
      },
      3,
      true
    )
  }, 100)
})
</script>
