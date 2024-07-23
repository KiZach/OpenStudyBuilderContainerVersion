<template>
  <div>
    <v-tabs v-model="activeTab">
      <v-tab v-for="tab of tabs" :key="tab.tab" :href="tab.tab">
        {{ tab.name }}
      </v-tab>
    </v-tabs>
    <v-tabs-items v-model="activeTab">
      <v-tab-item id="tab-0">
        <UnderConstruction />
      </v-tab-item>
      <v-tab-item id="tab-1">
        <UnderConstruction />
      </v-tab-item>
      <v-tab-item id="tab-2">
        <UnderConstruction />
      </v-tab-item>
      <v-tab-item id="tab-3">
        <UnderConstruction />
      </v-tab-item>
    </v-tabs-items>
  </div>
</template>

<script>
import UnderConstruction from '@/components/layout/UnderConstruction.vue'
import { useAppStore } from '@/stores/app'

export default {
  components: {
    UnderConstruction,
  },
  setup() {
    const appStore = useAppStore()
    return {
      addBreadcrumbsLevel: appStore.addBreadcrumbsLevel,
    }
  },
  data() {
    return {
      activeTab: null,
      tabs: [
        { tab: '#tab-0', name: this.$t('Sidebar.study.cdisc_ctr') },
        { tab: '#tab-1', name: this.$t('Sidebar.study.clinical_trials_gov') },
        { tab: '#tab-2', name: this.$t('Sidebar.study.eudra_ct') },
        { tab: '#tab-3', name: this.$t('Sidebar.study.who_ictrp') },
      ],
    }
  },
  watch: {
    activeTab(value) {
      localStorage.setItem('templatesTab', value)
      const tabName = value
        ? this.tabs.find((el) => el.tab.substring(1) === value).name
        : this.tabs[0].name
      this.addBreadcrumbsLevel({
        text: tabName,
        to: { name: 'StudyProperties', params: { tab: tabName } },
        index: 3,
        replace: true,
      })
    },
  },
  mounted() {
    this.activeTab = localStorage.getItem('templatesTab') || 'tab-0'
    const tabName = this.activeTab
      ? this.tabs.find((el) => el.tab.substring(1) === this.activeTab).name
      : this.tabs[0].name
    setTimeout(() => {
      this.addBreadcrumbsLevel({
        text: tabName,
        index: 3,
        replace: true,
      })
    }, 100)
  },
}
</script>
