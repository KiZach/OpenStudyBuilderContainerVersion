<template>
  <div>
    <v-tabs v-model="tab" bg-color="white">
      <v-tab
        v-for="catalogue in allCatalogues"
        :key="catalogue.name"
        :value="catalogue.name"
      >
        {{ catalogue.name }}
      </v-tab>
    </v-tabs>
    <v-window v-model="tab" class="bg-white">
      <v-window-item
        v-for="catalogue in allCatalogues"
        :key="catalogue.name"
        :value="catalogue.name"
      >
        <CodelistTable
          :catalogue="catalogue.name"
          column-data-resource="ct/codelists"
          library="Sponsor"
          @open-codelist-terms="openCodelistTerms"
        />
      </v-window-item>
    </v-window>
  </div>
</template>

<script setup lang="js">
import { useCtCataloguesStore } from '@/stores/library-ctcatalogues'
import { ref, watch, watchEffect, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import CodelistTable from './CodelistTable.vue'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
const ctCataloguesStore = useCtCataloguesStore()
const allCatalogues = ref([])

watchEffect(() => {
  allCatalogues.value = [{ name: 'All' }].concat(ctCataloguesStore.catalogues)
})

const tab = ref(null)

const openCodelistTerms = ({ codelist, catalogueName }) => {
  router.push({
    name: 'CodelistTerms',
    params: {
      codelist_id: codelist.codelist_uid,
      catalogue_name: catalogueName,
    },
  })
}

watch(tab, (newValue) => {
  router.push({
    name: 'Sponsor',
    params: { tab: newValue },
  })
  appStore.addBreadcrumbsLevel(newValue, undefined, 3, true)
})

onMounted(() => {
  tab.value = route.params.tab || 'All'
  ctCataloguesStore.fetchCatalogues()
  setTimeout(() => {
    appStore.addBreadcrumbsLevel(tab, undefined, 3, true)
  }, 100)
})
</script>
