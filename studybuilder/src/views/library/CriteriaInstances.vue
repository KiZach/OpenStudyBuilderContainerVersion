<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('CriteriaView.title') }}
      <HelpButton :help-text="$t('_help.ObjectivesTable.general')" />
    </div>
    <v-tabs v-model="tab" bg-color="white">
      <v-tab
        v-for="type in criteriaTypes"
        :key="type.term_uid"
        :value="type.name.sponsor_preferred_name"
      >
        {{ type.name.sponsor_preferred_name }}
      </v-tab>
    </v-tabs>
    <v-window v-model="tab">
      <v-window-item
        v-for="type in criteriaTypes"
        :key="type.term_uid"
        :value="type.name.sponsor_preferred_name"
      >
        <CriteriaTable :key="type.refreshKey" :criteria-type="type" />
      </v-window-item>
    </v-window>
  </div>
</template>

<script>
import CriteriaTable from '@/components/library/CriteriaTable.vue'
import HelpButton from '@/components/tools/HelpButton.vue'
import terms from '@/api/controlledTerminology/terms'
import { useAppStore } from '@/stores/app'

export default {
  components: {
    CriteriaTable,
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
      criteriaTypes: [],
      tab: 0,
    }
  },
  watch: {
    tab(newValue) {
      for (const type of this.criteriaTypes) {
        if (type.name.sponsor_preferred_name === newValue) {
          type.refreshKey++
          break
        }
      }
      this.$router.push({
        name: 'CriteriaInstances',
        params: { tab: newValue },
      })
      this.addBreadcrumbsLevel(newValue, undefined, 3, true)
    },
  },
  mounted() {
    terms.getByCodelist('criteriaTypes').then((resp) => {
      this.criteriaTypes = resp.data.items.map((item) => {
        return { ...item, refreshKey: 1 }
      })
      this.tab =
        this.$route.params.tab ||
        this.criteriaTypes[0].name.sponsor_preferred_name
    })
  },
}
</script>
