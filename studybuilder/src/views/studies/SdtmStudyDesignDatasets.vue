<template>
  <div v-if="selectedStudyVersion === null" class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('Sidebar.study.sdtm_study') }}
      <HelpButton :help-text="$t('_help.SdtmSpecificationTable.general')" />
    </div>
    <v-tabs v-model="tab" bg-color="white">
      <v-tab v-for="item of tabs" :key="item.tab" :value="item.tab">
        {{ item.name }}
      </v-tab>
    </v-tabs>
    <v-window v-model="tab">
      <v-window-item value="tab-0">
        <SdtmDesignTable type="TA" />
      </v-window-item>
      <v-window-item value="tab-1">
        <SdtmDesignTable type="TE" />
      </v-window-item>
      <v-window-item value="tab-2">
        <SdtmDesignTable type="TV" />
      </v-window-item>
      <v-window-item value="tab-3">
        <SdtmDesignTable type="TI" />
      </v-window-item>
      <v-window-item value="tab-4">
        <SdtmDesignTable type="TDM" />
      </v-window-item>
      <v-window-item value="tab-5">
        <SdtmDesignTable type="TS" />
      </v-window-item>
    </v-window>
  </div>
  <div v-else>
    <UnderConstruction :message="$t('UnderConstruction.not_supported')" />
  </div>
</template>

<script>
import SdtmDesignTable from '@/components/studies/SdtmDesignTable.vue'
import HelpButton from '@/components/tools/HelpButton.vue'
import UnderConstruction from '@/components/layout/UnderConstruction.vue'
import { useAppStore } from '@/stores/app'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { computed } from 'vue'

export default {
  components: {
    SdtmDesignTable,
    HelpButton,
    UnderConstruction,
  },
  setup() {
    const appStore = useAppStore()
    const studiesGeneralStore = useStudiesGeneralStore()
    return {
      addBreadcrumbsLevel: appStore.addBreadcrumbsLevel,
      selectedStudyVersion: computed(
        () => studiesGeneralStore.selectedStudyVersion
      ),
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
    }
  },
  data() {
    return {
      tab: null,
      tabs: [
        { tab: 'tab-0', name: this.$t('SdtmDesignTable.trial_arm') },
        { tab: 'tab-1', name: this.$t('SdtmDesignTable.trial_elem') },
        { tab: 'tab-2', name: this.$t('SdtmDesignTable.trial_visits') },
        { tab: 'tab-3', name: this.$t('SdtmDesignTable.trial_incl_excl') },
        { tab: 'tab-4', name: this.$t('SdtmDesignTable.trial_disease') },
        { tab: 'tab-5', name: this.$t('SdtmDesignTable.trial_summary') },
      ],
    }
  },
  watch: {
    tab(newValue) {
      const tabName = newValue
        ? this.tabs.find((el) => el.tab === newValue).name
        : this.tabs[0].name
      this.$router.push({
        name: 'SdtmStudyDesignDatasets',
        params: { tab: tabName },
      })
      this.addBreadcrumbsLevel(
        tabName,
        { name: 'SdtmStudyDesignDatasets', params: { tab: tabName } },
        3,
        true
      )
    },
  },
  mounted() {
    this.tab = this.$route.params.tab || this.tabs[0].tab
    const tabName = this.tab
      ? this.tabs.find((el) => el.tab === this.tab).name
      : this.tabs[0].name
    setTimeout(() => {
      this.addBreadcrumbsLevel(
        tabName,
        { name: 'SdtmStudyDesignDatasets', params: { tab: tabName } },
        3,
        true
      )
    }, 100)
  },
}
</script>
