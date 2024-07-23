<template>
  <div>
    <NNTable
      ref="table"
      :headers="headers"
      :items="units"
      :items-length="total"
      item-value="uid"
      sort-desc
      export-data-url="concepts/unit-definitions"
      export-object-label="Units"
      column-data-resource="concepts/unit-definitions"
      @filter="getUnits"
    >
      <template #actions="">
        <v-btn
          class="ml-2"
          size="small"
          color="primary"
          data-cy="add-unit"
          :title="$t('UnitForm.add_title')"
          :disabled="!checkPermission($roles.LIBRARY_WRITE)"
          icon="mdi-plus"
          @click.stop="showForm = true"
        />
      </template>
      <template #[`item.master_unit`]="{ item }">
        {{ $filters.yesno(item.master_unit) }}
      </template>
      <template #[`item.display_unit`]="{ item }">
        {{ $filters.yesno(item.display_unit) }}
      </template>
      <template #[`item.unit_subsets`]="{ item }">
        {{ displayList(item.unit_subsets) }}
      </template>
      <template #[`item.ct_units`]="{ item }">
        {{ displayList(item.ct_units) }}
      </template>
      <template #[`item.convertible_unit`]="{ item }">
        {{ $filters.yesno(item.convertible_unit) }}
      </template>
      <template #[`item.si_unit`]="{ item }">
        {{ $filters.yesno(item.si_unit) }}
      </template>
      <template #[`item.us_conventional_unit`]="{ item }">
        {{ $filters.yesno(item.us_conventional_unit) }}
      </template>
      <template #[`item.status`]="{ item }">
        <StatusChip :status="item.status" />
      </template>
      <template #[`item.start_date`]="{ item }">
        {{ $filters.date(item.start_date) }}
      </template>
      <template #[`item.ucum_unit`]="{ item }">
        <v-edit-dialog v-model:return-value="item.ucum_unit">
          <span v-if="item.ucum_unit">{{ item.ucum_unit.code }}</span>
          <v-icon v-else> mdi-table-search </v-icon>
          <template #input>
            <ucum-unit-field v-model="item.ucum_unit" />
          </template>
        </v-edit-dialog>
      </template>
      <template #[`item.actions`]="{ item }">
        <ActionsMenu :actions="actions" :item="item" />
      </template>
    </NNTable>
    <UnitForm :open="showForm" :unit="activeUnit" @close="close()" />
  </div>
</template>

<script>
import NNTable from '@/components/tools/NNTable.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import UnitForm from '@/components/library/UnitForm.vue'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import StudybuilderUCUMField from '@/components/tools/StudybuilderUCUMField.vue'
import units from '@/api/units'
import { useAccessGuard } from '@/composables/accessGuard'
import { useUnitsStore } from '@/stores/units'
import filteringParameters from '@/utils/filteringParameters'
import { computed } from 'vue'

export default {
  components: {
    NNTable,
    StatusChip,
    'ucum-unit-field': StudybuilderUCUMField,
    UnitForm,
    ActionsMenu,
  },
  setup() {
    const unitsStore = useUnitsStore()

    return {
      fetchUnits: unitsStore.fetchUnits,
      total: computed(() => unitsStore.total),
      units: computed(() => unitsStore.units),
      ...useAccessGuard(),
    }
  },
  data() {
    return {
      headers: [
        { title: '', key: 'actions', width: '5%' },
        { title: this.$t('_global.library'), key: 'library_name' },
        { title: this.$t('_global.name'), key: 'name' },
        { title: this.$t('UnitTable.master_unit'), key: 'master_unit' },
        { title: this.$t('UnitTable.display_unit'), key: 'display_unit' },
        {
          title: this.$t('UnitTable.unit_subsets'),
          key: 'unit_subsets',
          filteringName: 'unit_subsets.name',
        },
        { title: this.$t('UnitTable.ucum_unit'), key: 'ucum.name' },
        {
          title: this.$t('UnitTable.ct_units'),
          key: 'ct_units',
          filteringName: 'ct_units.name',
          width: '10%',
        },
        {
          title: this.$t('UnitTable.convertible_unit'),
          key: 'convertible_unit',
        },
        { title: this.$t('UnitTable.si_unit'), key: 'si_unit' },
        {
          title: this.$t('UnitTable.us_conventional_unit'),
          key: 'us_conventional_unit',
        },
        {
          title: this.$t('UnitTable.unit_dimension'),
          key: 'unit_dimension.name',
        },
        { title: this.$t('UnitTable.legacy_code'), key: 'legacy_code' },
        {
          title: this.$t('UnitTable.molecular_weight'),
          key: 'molecular_weight_conv_expon',
        },
        {
          title: this.$t('UnitTable.conversion_factor'),
          key: 'conversion_factor_to_master',
        },
        { title: this.$t('_global.modified'), key: 'start_date' },
        { title: this.$t('_global.status'), key: 'status' },
        { title: this.$t('_global.version'), key: 'version' },
      ],
      actions: [
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil-outline',
          iconColor: 'primary',
          condition: (item) => item.status === 'Draft',
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.editUnit,
        },
        {
          label: this.$t('_global.delete'),
          icon: 'mdi-delete-outline',
          iconColor: 'error',
          condition: (item) =>
            item.status === 'Draft' && parseFloat(item.version) < 1,
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.deleteUnit,
        },
        {
          label: this.$t('_global.new_version'),
          icon: 'mdi-plus-circle-outline',
          iconColor: 'primary',
          condition: (item) => item.status === 'Final',
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.newUnitVersion,
        },
        {
          label: this.$t('_global.approve'),
          icon: 'mdi-check-decagram',
          iconColor: 'success',
          condition: (item) => item.status === 'Draft',
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.approveUnit,
        },
        {
          label: this.$t('_global.inactivate'),
          icon: 'mdi-close-octagon-outline',
          iconColor: 'primary',
          condition: (item) => item.status === 'Final',
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.inactivateUnit,
        },
        {
          label: this.$t('_global.reactivate'),
          icon: 'mdi-undo-variant',
          iconColor: 'primary',
          condition: (item) => item.status === 'Retired',
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.reactivateUnit,
        },
      ],
      showForm: false,
      filters: '',
      activeUnit: {},
    }
  },
  methods: {
    displayList(items) {
      return items.map((item) => item.name).join(', ')
    },
    getUnits(filters, options, filtersUpdated) {
      if (filters) {
        this.filters = filters
      }
      const params = filteringParameters.prepareParameters(
        options,
        filters,
        filtersUpdated
      )
      this.fetchUnits(params)
    },
    editUnit(item) {
      this.activeUnit = item
      this.showForm = true
    },
    deleteUnit(item) {
      units.delete(item.uid).then(() => {
        this.$refs.table.filterTable()
      })
    },
    newUnitVersion(item) {
      units.newVersion(item.uid).then(() => {
        this.$refs.table.filterTable()
      })
    },
    approveUnit(item) {
      units.approve(item.uid).then(() => {
        this.$refs.table.filterTable()
      })
    },
    inactivateUnit(item) {
      units.inactivate(item.uid).then(() => {
        this.$refs.table.filterTable()
      })
    },
    reactivateUnit(item) {
      units.reactivate(item.uid).then(() => {
        this.$refs.table.filterTable()
      })
    },
    close() {
      this.showForm = false
      this.activeUnit = {}
      this.$refs.table.filterTable()
    },
  },
}
</script>
