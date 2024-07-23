<template>
  <div>
    <NNTable
      :headers="headers"
      :items="formatedCompounds"
      :items-length="total"
      item-value="uid"
      density="compact"
      column-data-resource="concepts/compounds"
      export-data-url="concepts/compounds"
      export-object-label="compounds"
      @filter="fetchItems"
    >
      <template #actions="">
        <v-btn
          size="small"
          color="primary"
          :title="$t('CompoundForm.add_title')"
          :disabled="!checkPermission($roles.LIBRARY_WRITE)"
          icon="mdi-plus"
          @click.stop="showCompoundForm = true"
        />
      </template>
      <template #[`item.actions`]="{ item }">
        <ActionsMenu :actions="actions" :item="item" />
      </template>
      <template #[`item.name`]="{ item }">
        <router-link
          :to="{ name: 'CompoundOverview', params: { id: item.uid } }"
        >
          {{ item.name }}
        </router-link>
      </template>
      <template #[`item.start_date`]="{ item }">
        {{ $filters.date(item.start_date) }}
      </template>
      <template #[`item.status`]="{ item }">
        <StatusChip :status="item.status" />
      </template>
    </NNTable>
    <v-dialog
      v-model="showCompoundForm"
      fullscreen
      persistent
      content-class="fullscreen-dialog"
    >
      <CompoundForm
        :compound-uid="selectedCompound ? selectedCompound.uid : null"
        :form-shown="showCompoundForm"
        @close="closeCompoundForm"
        @created="fetchItems"
        @updated="fetchItems"
      />
    </v-dialog>
    <v-dialog
      v-model="showHistory"
      persistent
      :max-width="$globals.historyDialogMaxWidth"
      :fullscreen="$globals.historyDialogFullscreen"
      @keydown.esc="closeHistory"
    >
      <HistoryTable
        :title="historyTitle"
        :headers="headers"
        :items="historyItems"
        @close="closeHistory"
      />
    </v-dialog>
    <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
  </div>
</template>

<script>
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import CompoundForm from './CompoundForm.vue'
import compounds from '@/api/concepts/compounds'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import dataFormating from '@/utils/dataFormating'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import NNTable from '@/components/tools/NNTable.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import { useAccessGuard } from '@/composables/accessGuard'
import filteringParameters from '@/utils/filteringParameters'

export default {
  components: {
    ActionsMenu,
    CompoundForm,
    ConfirmDialog,
    HistoryTable,
    NNTable,
    StatusChip,
  },
  inject: ['eventBusEmit'],
  props: {
    tabClickedAt: {
      type: Number,
      default: null,
    },
  },
  setup() {
    const accessGuard = useAccessGuard()
    return {
      ...accessGuard,
    }
  },
  data() {
    return {
      actions: [
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil-outline',
          iconColor: 'primary',
          condition: (item) =>
            item.possible_actions.find((action) => action === 'edit'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.editCompound,
        },
        {
          label: this.$t('_global.approve'),
          icon: 'mdi-check-decagram',
          iconColor: 'success',
          condition: (item) =>
            item.possible_actions.find((action) => action === 'approve'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.approveCompound,
        },
        {
          label: this.$t('_global.new_version'),
          icon: 'mdi-plus-circle-outline',
          iconColor: 'primary',
          condition: (item) =>
            item.possible_actions.find((action) => action === 'new_version'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.createNewVersion,
        },
        {
          label: this.$t('_global.inactivate'),
          icon: 'mdi-close-octagon-outline',
          iconColor: 'primary',
          condition: (item) =>
            item.possible_actions.find((action) => action === 'inactivate'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.inactivateCompound,
        },
        {
          label: this.$t('_global.reactivate'),
          icon: 'mdi-undo-variant',
          iconColor: 'primary',
          condition: (item) =>
            item.possible_actions.find((action) => action === 'reactivate'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.reactivateCompound,
        },
        {
          label: this.$t('_global.delete'),
          icon: 'mdi-delete-outline',
          iconColor: 'error',
          condition: (item) =>
            item.possible_actions.find((action) => action === 'delete'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.deleteCompound,
        },
        {
          label: this.$t('_global.history'),
          icon: 'mdi-history',
          click: this.openHistory,
        },
      ],
      compounds: [],
      filters: {},
      headers: [
        { title: '', key: 'actions', width: '5%' },
        {
          title: this.$t('CompoundTable.sponsor_compound'),
          key: 'is_sponsor_compound',
        },
        { title: this.$t('CompoundTable.compound_name'), key: 'name' },
        { title: this.$t('CompoundTable.is_name_inn'), key: 'is_name_inn' },
        {
          title: this.$t('CompoundTable.nnc_number_long'),
          key: 'nnc_long_number',
        },
        {
          title: this.$t('CompoundTable.nnc_number_short'),
          key: 'nnc_short_number',
        },
        {
          title: this.$t('CompoundTable.analyte_number'),
          key: 'analyte_number',
        },
        { title: this.$t('_global.definition'), key: 'definition' },
        { title: this.$t('CompoundTable.brand_name'), key: 'brands' },
        { title: this.$t('CompoundTable.substance_name'), key: 'substances' },
        {
          title: this.$t('CompoundTable.pharmacological_class'),
          key: 'pharmacological_classes',
        },
        { title: this.$t('CompoundTable.dose'), key: 'dose_keys' },
        { title: this.$t('CompoundTable.strength'), key: 'strength_keys' },
        { title: this.$t('CompoundTable.dosage_form'), key: 'dosage_forms' },
        {
          title: this.$t('CompoundTable.route_of_admin'),
          key: 'routes_of_administration',
        },
        {
          title: this.$t('CompoundTable.dose_frequency'),
          key: 'dose_frequencies',
        },
        { title: this.$t('CompoundTable.dispensed_in'), key: 'dispensers' },
        {
          title: this.$t('CompoundTable.delivery_device'),
          key: 'delivery_devices',
        },
        { title: this.$t('CompoundTable.half_life'), key: 'half_life' },
        { title: this.$t('CompoundTable.lag_time'), key: 'lag_times' },
        { title: this.$t('_global.modified'), key: 'start_date' },
        { title: this.$t('_global.version'), key: 'version' },
        { title: this.$t('_global.status'), key: 'status' },
      ],
      historyItems: [],
      selectedCompound: null,
      showCompoundForm: false,
      showHistory: false,
      total: 0,
    }
  },
  computed: {
    historyTitle() {
      if (this.selectedCompound) {
        return this.$t('CompoundTable.compound_history_title', {
          compound: this.selectedCompound.uid,
        })
      }
      return ''
    },
    formatedCompounds() {
      return this.transformItems(this.compounds)
    },
  },
  watch: {
    tabClickedAt() {
      this.fetchItems(this.filters, this.sort)
    },
    options: {
      handler() {
        this.fetchItems()
      },
      deep: true,
    },
  },
  methods: {
    fetchItems(filters, options, filtersUpdated) {
      if (filters !== undefined) {
        this.filters = filters
      }
      const params = filteringParameters.prepareParameters(
        options,
        filters,
        filtersUpdated
      )
      compounds.getFiltered(params).then((resp) => {
        this.compounds = resp.data.items
        this.total = resp.data.total
      })
    },
    closeCompoundForm() {
      this.showCompoundForm = false
      this.selectedCompound = null
    },
    editCompound(item) {
      // Make sure to edit the orignal compound, not the formated one
      const orignalItem = this.compounds.find(
        (compound) => compound.uid === item.uid
      )
      this.selectedCompound = orignalItem
      this.showCompoundForm = true
    },
    approveCompound(item) {
      compounds.approve(item.uid).then(() => {
        this.fetchItems()
        this.eventBusEmit('notification', {
          msg: this.$t('CompoundTable.approve_success'),
          type: 'success',
        })
      })
    },
    async deleteCompound(item) {
      const options = { type: 'warning' }
      const compound = item.name
      if (
        await this.$refs.confirm.open(
          this.$t('CompoundTable.confirm_delete', { compound }),
          options
        )
      ) {
        await compounds.deleteObject(item.uid)
        this.fetchItems()
        this.eventBusEmit('notification', {
          msg: this.$t('CompoundTable.delete_success'),
          type: 'success',
        })
      }
    },
    createNewVersion(item) {
      compounds.newVersion(item.uid).then(() => {
        this.fetchItems()
        this.eventBusEmit('notification', {
          msg: this.$t('CompoundTable.new_version_success'),
          type: 'success',
        })
      })
    },
    inactivateCompound(item) {
      compounds.inactivate(item.uid).then(() => {
        this.fetchItems()
        this.eventBusEmit('notification', {
          msg: this.$t('CompoundTable.inactivate_success'),
          type: 'success',
        })
      })
    },
    reactivateCompound(item) {
      compounds.reactivate(item.uid).then(() => {
        this.fetchItems()
        this.eventBusEmit('notification', {
          msg: this.$t('CompoundTable.reactivate_success'),
          type: 'success',
        })
      })
    },
    async openHistory(item) {
      this.selectedCompound = item
      const resp = await compounds.getVersions(this.selectedCompound.uid)
      this.historyItems = this.transformItems(resp.data)
      this.showHistory = true
    },
    closeHistory() {
      this.showHistory = false
    },
    transformItems(items) {
      const result = []
      for (const item of items) {
        const newItem = { ...item }
        newItem.is_sponsor_compound = dataFormating.yesno(
          newItem.is_sponsor_compound
        )
        newItem.is_name_inn = dataFormating.yesno(newItem.is_name_inn)
        newItem.brands = dataFormating.names(newItem.brands)
        newItem.substances = dataFormating.substances(item.substances)
        newItem.pharmacological_classes = dataFormating.pharmacologicalClasses(
          item.substances
        )
        newItem.dose_values = dataFormating.numericValues(newItem.dose_values)
        newItem.strength_values = dataFormating.numericValues(
          newItem.strength_values
        )
        newItem.dosage_forms = dataFormating.names(newItem.dosage_forms)
        newItem.routes_of_administration = dataFormating.names(
          newItem.routes_of_administration
        )
        newItem.dose_frequencies = dataFormating.names(newItem.dose_frequencies)
        newItem.dispensers = dataFormating.names(newItem.dispensers)
        newItem.delivery_devices = dataFormating.names(newItem.delivery_devices)
        if (newItem.half_life) {
          newItem.half_life = dataFormating.numericValue(newItem.half_life)
        }
        newItem.lag_times = dataFormating.lagTimes(newItem.lag_times)
        result.push(newItem)
      }
      return result
    },
  },
}
</script>
