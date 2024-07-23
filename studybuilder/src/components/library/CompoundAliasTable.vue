<template>
  <div>
    <NNTable
      :headers="headers"
      :items="compoundAliases"
      :items-length="total"
      item-value="uid"
      density="compact"
      column-data-resource="concepts/compound-aliases"
      export-data-url="concepts/compound-aliases"
      export-object-label="compound-aliases"
      @filter="fetchItems"
    >
      <template #actions="">
        <v-btn
          size="small"
          color="primary"
          :title="$t('CompoundAliasForm.add_title')"
          :disabled="!checkPermission($roles.LIBRARY_WRITE)"
          icon="mdi-plus"
          @click.stop="showForm = true"
        />
      </template>
      <template #[`item.actions`]="{ item }">
        <ActionsMenu :actions="actions" :item="item" />
      </template>
      <template #[`item.is_preferred_synonym`]="{ item }">
        {{ $filters.yesno(item.is_preferred_synonym) }}
      </template>
      <template #[`item.name`]="{ item }">
        <router-link
          :to="{ name: 'CompoundOverview', params: { id: item.compound.uid } }"
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
      v-model="showForm"
      fullscreen
      persistent
      content-class="fullscreen-dialog"
    >
      <CompoundAliasForm
        :compound-alias-uid="selectedItem ? selectedItem.uid : null"
        :form-shown="showForm"
        @close="closeForm"
        @created="fetchItems"
        @updated="fetchItems"
      />
    </v-dialog>
    <v-dialog
      v-model="showHistory"
      persistent
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
import CompoundAliasForm from './CompoundAliasForm.vue'
import compoundAliases from '@/api/concepts/compoundAliases'
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
    CompoundAliasForm,
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
          click: this.editItem,
        },
        {
          label: this.$t('_global.approve'),
          icon: 'mdi-check-decagram',
          iconColor: 'success',
          condition: (item) =>
            item.possible_actions.find((action) => action === 'approve'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.approveItem,
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
          click: this.inactivateItem,
        },
        {
          label: this.$t('_global.reactivate'),
          icon: 'mdi-undo-variant',
          iconColor: 'primary',
          condition: (item) =>
            item.possible_actions.find((action) => action === 'reactivate'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.reactivateItem,
        },
        {
          label: this.$t('_global.delete'),
          icon: 'mdi-delete-outline',
          iconColor: 'error',
          condition: (item) =>
            item.possible_actions.find((action) => action === 'delete'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.deleteItem,
        },
        {
          label: this.$t('_global.history'),
          icon: 'mdi-history',
          click: this.openHistory,
        },
      ],
      compoundAliases: [],
      filters: {},
      headers: [
        { title: '', key: 'actions', width: '5%' },
        {
          title: this.$t('CompoundAliasTable.compound_name'),
          key: 'compound.name',
        },
        { title: this.$t('_global.name'), key: 'name' },
        {
          title: this.$t('_global.sentence_case_name'),
          key: 'name_sentence_case',
        },
        {
          title: this.$t('CompoundAliasTable.is_preferred_synonym'),
          key: 'is_preferred_synonym',
        },
        { title: this.$t('_global.definition'), key: 'definition' },
        { title: this.$t('_global.modified'), key: 'start_date' },
        { title: this.$t('_global.version'), key: 'version' },
        { title: this.$t('_global.status'), key: 'status' },
      ],
      historyItems: [],
      options: {},
      selectedItem: null,
      showForm: false,
      showHistory: false,
      total: 0,
    }
  },
  computed: {
    historyTitle() {
      if (this.selectedItem) {
        return this.$t('CompoundAliasTable.history_title', {
          compoundAlias: this.selectedItem.uid,
        })
      }
      return ''
    },
  },
  watch: {
    tabClickedAt() {
      this.fetchItems()
    },
    options: {
      handler() {
        this.fetchItems()
      },
      deep: true,
    },
  },
  mounted() {
    this.fetchItems()
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
      compoundAliases.getFiltered(params).then((resp) => {
        this.compoundAliases = resp.data.items
        this.total = resp.data.total
      })
    },
    closeForm() {
      this.showForm = false
      this.selectedItem = null
    },
    editItem(item) {
      this.selectedItem = item
      this.showForm = true
    },
    approveItem(item) {
      compoundAliases.approve(item.uid).then(() => {
        this.fetchItems()
        this.eventBusEmit('notification', {
          msg: this.$t('CompoundAliasTable.approve_success'),
          type: 'success',
        })
      })
    },
    async deleteItem(item) {
      const options = { type: 'warning' }
      const compoundAlias = item.name
      if (
        await this.$refs.confirm.open(
          this.$t('CompoundAliasTable.confirm_delete', { compoundAlias }),
          options
        )
      ) {
        await compoundAliases.deleteObject(item.uid)
        this.fetchItems()
        this.eventBusEmit('notification', {
          msg: this.$t('CompoundAliasTable.delete_success'),
          type: 'success',
        })
      }
    },
    createNewVersion(item) {
      compoundAliases.newVersion(item.uid).then(() => {
        this.fetchItems()
        this.eventBusEmit('notification', {
          msg: this.$t('CompoundAliasTable.new_version_success'),
          type: 'success',
        })
      })
    },
    inactivateItem(item) {
      compoundAliases.inactivate(item.uid).then(() => {
        this.fetchItems()
        this.eventBusEmit('notification', {
          msg: this.$t('CompoundAliasTable.inactivate_success'),
          type: 'success',
        })
      })
    },
    reactivateItem(item) {
      compoundAliases.reactivate(item.uid).then(() => {
        this.fetchItems()
        this.eventBusEmit('notification', {
          msg: this.$t('CompoundAliasTable.reactivate_success'),
          type: 'success',
        })
      })
    },
    async openHistory(item) {
      this.selectedItem = item
      const resp = await compoundAliases.getVersions(this.selectedItem.uid)
      this.historyItems = resp.data
      for (const historyItem of this.historyItems) {
        if (historyItem.is_preferred_synonym !== undefined) {
          historyItem.is_preferred_synonym = dataFormating.yesno(
            historyItem.is_preferred_synonym
          )
        }
      }
      this.showHistory = true
    },
    closeHistory() {
      this.showHistory = false
    },
  },
}
</script>
