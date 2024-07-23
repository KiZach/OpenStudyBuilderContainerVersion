<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('CriteriaTemplatesView.title') }}
      <HelpButton :help-text="$t('_help.CriteriaTemplatesTable.general')" />
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
        <CriteriaTemplateTable
          :ref="(el) => (tableRefs[type.name.sponsor_preferred_name] = el)"
          :key="type.term_uid"
          :criteria-type="type"
        />
      </v-window-item>
    </v-window>
  </div>
</template>

<script setup>
import { nextTick, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import CriteriaTemplateTable from '@/components/library/CriteriaTemplateTable.vue'
import HelpButton from '@/components/tools/HelpButton.vue'
import terms from '@/api/controlledTerminology/terms'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
const route = useRoute()
const router = useRouter()

const criteriaTypes = ref([])
const tab = ref(null)
const tableRefs = ref({})

watch(tab, (newValue) => {
  const params = { type: newValue }
  router.push({
    name: 'CriteriaTemplates',
    params,
  })
  appStore.addBreadcrumbsLevel(newValue, undefined, 3, true)
})

watch(
  () => route.params.type,
  (newValue) => {
    tab.value = newValue
    nextTick(() => {
      if (tableRefs.value[newValue]) {
        tableRefs.value[newValue].restoreTab()
      }
    })
  }
)

terms.getByCodelist('criteriaTypes').then((resp) => {
  criteriaTypes.value = resp.data.items
  criteriaTypes.value.forEach((type) => {
    type.name.sponsor_preferred_name = type.name.sponsor_preferred_name.replace(
      ' Criteria',
      ''
    )
  })
  if (route.params.type) {
    tab.value = route.params.type
  } else {
    tab.value = criteriaTypes.value[0].name.sponsor_preferred_name
  }
  appStore.addBreadcrumbsLevel(tab.value, undefined, 3, true)
})
</script>

<style scoped>
.v-window {
  min-height: 50vh;
}
</style>
