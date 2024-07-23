<template>
  <PackageTimeline
    v-if="!loading"
    :package-name="packageName"
    :catalogue-packages="packages"
    :with-add-button="packages.length !== 0"
    @package-changed="updateUrl"
    @add-package="showCreationForm = true"
  >
    <template #default="{ selectedPackage }">
      <CodelistTable
        v-if="packages.length"
        ref="table"
        :package="selectedPackage"
        sponsor
        read-only
        column-data-resource="ct/codelists"
        :display-table-toolbar="false"
        :display-row-actions="false"
      >
        <template #beforeToolbar>
          <div v-if="selectedPackage" class="d-flex align-center my-2">
            {{ $t('SponsorCTPackagesTable.date') }}
            {{ selectedPackage.effective_date }}
            <v-spacer />
            {{ $t('SponsorCTPackagesTable.connected_to') }}
            {{ selectedPackage.extends_package }}
            <v-spacer />
          </div>
        </template>
      </CodelistTable>
      <v-card v-else class="pa-4">
        <v-card-text class="text-center">
          <p>{{ $t('SponsorCTPackagesTable.no_package_yet') }}</p>
          <v-btn color="primary" class="mt-4" @click="showCreationForm = true">
            {{ $t('SponsorCTPackagesTable.create_first_one') }}
          </v-btn>
        </v-card-text>
      </v-card>
    </template>
  </PackageTimeline>
  <SponsorCTPackageForm :open="showCreationForm" @close="closeCreationForm" />
</template>

<script setup>
import { ref } from 'vue'
import { DateTime } from 'luxon'
import { useRouter } from 'vue-router'
import controlledTerminology from '@/api/controlledTerminology'
import CodelistTable from './CodelistTable.vue'
import PackageTimeline from './PackageTimeline.vue'
import SponsorCTPackageForm from './SponsorCTPackageForm.vue'

const props = defineProps({
  packageName: {
    type: String,
    default: '',
  },
})
const router = useRouter()

const loading = ref(true)
const packages = ref([])
const showCreationForm = ref(false)
const table = ref()

function fetchPackages() {
  loading.value = true
  controlledTerminology.getSponsorPackages().then((resp) => {
    packages.value = resp.data
    for (const pkg of packages.value) {
      pkg.date = DateTime.fromISO(pkg.effective_date).toJSDate()
    }
    loading.value = false
  })
}

function updateUrl(pkg) {
  router.push({
    name: 'SponsorCtPackages',
    params: { package_name: pkg ? pkg.name : null },
  })
  table.value.refresh()
}

function closeCreationForm() {
  showCreationForm.value = false
  fetchPackages()
}

fetchPackages()
</script>
