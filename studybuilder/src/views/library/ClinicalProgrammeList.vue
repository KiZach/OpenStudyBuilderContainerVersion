<template>
  <NNTable
    :headers="headers"
    :items="items"
    :items-length="total"
    only-text-search
    hide-default-switches
    item-value="name"
    @filter="fetchProgrammes"
  >
    <template #actions="">
      <slot name="extraActions" />
      <v-btn
        size="small"
        color="primary"
        data-cy="add-clinical-programme"
        :title="$t('ClinicalProgrammeForm.title')"
        icon="mdi-plus"
        @click.stop="showForm"
      />
    </template>
  </NNTable>
  <ClinicalProgrammeForm :open="showClinicalProgrammeForm" @close="closeForm" />
</template>

<script>
import NNTable from '@/components/tools/NNTable.vue'
import programmes from '@/api/clinicalProgrammes'
import ClinicalProgrammeForm from '@/components/library/ClinicalProgrammeForm.vue'
import filteringParameters from '@/utils/filteringParameters'

export default {
  components: {
    NNTable,
    ClinicalProgrammeForm,
  },
  data() {
    return {
      headers: [{ title: this.$t('ClinicalProgrammes.name'), key: 'name' }],
      items: [],
      options: {},
      total: 0,
      filters: '',
      showClinicalProgrammeForm: false,
    }
  },
  watch: {
    options() {
      this.fetchProgrammes()
    },
  },
  methods: {
    fetchProgrammes(filters, options, filtersUpdated) {
      if (!filters && this.filters) {
        filters = this.filters
      }
      const params = filteringParameters.prepareParameters(
        options,
        filters,
        filtersUpdated
      )
      this.filters = filters
      programmes.get(params).then((resp) => {
        this.items = resp.data.items
        this.total = resp.data.total
      })
    },
    showForm() {
      this.showClinicalProgrammeForm = true
    },
    closeForm() {
      this.showClinicalProgrammeForm = false
      this.fetchProgrammes()
    },
  },
}
</script>
