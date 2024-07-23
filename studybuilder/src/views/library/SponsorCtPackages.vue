<template>
  <div class="px-4">
    <div data-cy="page-title" class="page-title d-flex align-center">
      {{ $t('SponsorCtPackages.title') }}
      <HelpButton :help-text="$t('_help.CtSponsorPackagesTable.general')" />
    </div>
    <SponsorCtPackagesTable :package-name="route.params.package_name" />
  </div>
</template>

<script setup>
import { onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'
import SponsorCtPackagesTable from '@/components/library/SponsorCtPackagesTable.vue'
import HelpButton from '@/components/tools/HelpButton.vue'

const appStore = useAppStore()
const route = useRoute()

watch(
  () => route.params.package_name,
  (value) => {
    if (value) {
      updatePackageInBreadcrumbs(value, route.params.catalogue_name, true)
    } else {
      appStore.truncateBreadcrumbsFromLevel(4)
    }
  }
)

onMounted(() => {
  if (route.params.package_name) {
    updatePackageInBreadcrumbs(route.params.package_name)
  }
})

function updatePackageInBreadcrumbs(packageName, replace) {
  appStore.addBreadcrumbsLevel(
    packageName,
    { name: 'SponsorCtPackages', params: { package_name: packageName } },
    3,
    replace
  )
}
</script>
