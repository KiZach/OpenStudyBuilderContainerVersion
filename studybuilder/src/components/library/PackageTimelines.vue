<template>
  <v-tabs v-model="tab" bg-color="dfltBackground">
    <v-tab
      v-for="(pckgs, catalogue) in packages"
      :key="catalogue"
      :value="catalogue"
      :data-cy="catalogue"
    >
      {{ catalogue }}
    </v-tab>
  </v-tabs>
  <v-window v-model="tab">
    <v-window-item
      v-for="(cataloguePackages, catalogue) in packages"
      :key="catalogue"
      :value="catalogue"
    >
      <PackageTimeline
        :ref="(el) => (timelineRefs[catalogue] = el)"
        :catalogue-packages="cataloguePackages"
        @package-changed="(pkg) => emit('packageChanged', catalogue, pkg)"
      >
        <template v-for="(_, slot) of $slots" #[slot]="scope">
          <slot :name="slot" v-bind="scope" :catalogue_name="catalogue" />
        </template>
      </PackageTimeline>
    </v-window-item>
  </v-window>
</template>

<script setup>
import { nextTick, ref, onMounted, watch } from 'vue'
import { useCtCataloguesStore } from '@/stores/library-ctcatalogues'
import { DateTime } from 'luxon'
import controlledTerminology from '@/api/controlledTerminology'
import PackageTimeline from './PackageTimeline.vue'

const props = defineProps({
  catalogueName: {
    type: String,
    default: null,
    required: false,
  },
  packageName: {
    type: String,
    default: null,
    required: false,
  },
  sponsor: {
    type: Boolean,
    default: false,
  },
})
const emit = defineEmits(['catalogueChanged', 'packageChanged'])
const ctCataloguesStore = useCtCataloguesStore()

const packages = ref([])
const tab = ref(null)
const timelineRefs = ref({})

watch(tab, (newValue, oldValue) => {
  if (oldValue) {
    emit('catalogueChanged', newValue)
  }
  if (newValue !== props.catalogueName) {
    ctCataloguesStore.currentCataloguePage = 1
  }
  nextTick(() => {
    if (timelineRefs.value[newValue]) {
      timelineRefs.value[newValue].restorePackage()
    }
  })
})

onMounted(() => {
  controlledTerminology.getPackages().then((resp) => {
    packages.value = sortPackages(resp.data)
    if (props.catalogueName) {
      tab.value = props.catalogueName
    } else {
      tab.value = Object.keys(packages.value)[0]
    }
  })
})

function sortPackages(packages) {
  const result = {}
  packages.forEach((pkg) => {
    if (result[pkg.catalogue_name] === undefined) {
      result[pkg.catalogue_name] = []
    }
    const date = DateTime.fromISO(pkg.effective_date).toJSDate()
    result[pkg.catalogue_name].push({
      date,
      name: pkg.name,
      selectedPackage: null,
    })
  })
  for (const catalogue in result) {
    result[catalogue].sort((a, b) => {
      return b.date - a.date
    })
  }
  return result
}
</script>
