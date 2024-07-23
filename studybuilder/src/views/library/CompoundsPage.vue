<template>
  <div class="px-4">
    <div class="d-flex page-title">
      {{ $t('CompoundsView.title') }}
      <HelpButton
        :title="$t('_global.definition')"
        :help-text="$t('_help.CompoundsView.general')"
      />
    </div>
    <v-tabs v-model="tab">
      <v-tab v-for="item of tabs" :key="item.tab" :value="item.tab">
        {{ item.name }}
      </v-tab>
    </v-tabs>
    <v-window v-model="tab">
      <v-window-item value="compounds">
        <CompoundTable :tab-clicked-at="compoundsTabClickedAt" />
      </v-window-item>
      <v-window-item value="aliases">
        <CompoundAliasTable :tab-clicked-at="compoundAliasesTabClickedAt" />
      </v-window-item>
    </v-window>
  </div>
</template>

<script>
import CompoundAliasTable from '@/components/library/CompoundAliasTable.vue'
import CompoundTable from '@/components/library/CompoundTable.vue'
import HelpButton from '@/components/tools/HelpButton.vue'
import { useAppStore } from '@/stores/app'

export default {
  components: {
    CompoundAliasTable,
    CompoundTable,
    HelpButton,
  },
  setup() {
    const appStore = useAppStore()
    return {
      addBreadcrumbsLevel: appStore.addBreadcrumbsLevel,
    }
  },
  data() {
    return {
      tab: 0,
      compoundAliasesTabClickedAt: 0,
      compoundsTabClickedAt: 0,
      tabs: [
        { tab: 'compounds', name: this.$t('CompoundsView.tab1_title') },
        { tab: 'aliases', name: this.$t('CompoundsView.tab2_title') },
      ],
    }
  },
  watch: {
    tab(newValue) {
      switch (newValue) {
        case 'compounds':
          this.compoundsTabClickedAt = Date.now()
          break
        case 'aliases':
          this.compoundAliasesTabClickedAt = Date.now()
          break
      }
      const tab = newValue || this.tabs[0].tab
      this.$router.push({
        name: 'Compounds',
        params: { tab },
      })
      const tabName = this.tabs.find((el) => el.tab === tab).name
      this.addBreadcrumbsLevel(
        tabName,
        { name: 'Compounds', params: { tab } },
        3,
        true
      )
    },
  },
  mounted() {
    const tabName = this.tab
      ? this.tabs.find((el) => el.tab === this.tab).name
      : this.tabs[0].name
    setTimeout(() => {
      this.addBreadcrumbsLevel(tabName, undefined, 3, true)
    }, 1100)
  },
}
</script>
