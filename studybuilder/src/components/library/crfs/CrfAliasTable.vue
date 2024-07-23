<template>
  <div>
    <NNTable
      :headers="headers"
      :items="aliases"
      item-value="uid"
      :items-length="total"
      column-data-resource="concepts/odms/aliases"
      export-data-url="concepts/odms/aliases"
      export-object-label="CRFAliases"
      @filter="getAliases"
    >
      <template #actions="">
        <v-btn
          class="ml-2"
          fab
          size="small"
          color="primary"
          icon="mdi-plus"
          :title="$t('CrfAliases.add_alias')"
          :disabled="!checkPermission($roles.LIBRARY_WRITE)"
          @click.stop="openForm"
        />
      </template>
      <template #[`item.actions`]="{ item }">
        <ActionsMenu :actions="actions" :item="item" />
      </template>
    </NNTable>
    <CrfAliasForm :open="showForm" :edited-item="editItem" @close="closeForm" />
    <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
  </div>
</template>

<script>
import NNTable from '@/components/tools/NNTable.vue'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import crfs from '@/api/crfs'
import CrfAliasForm from '@/components/library/crfs/CrfAliasForm.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import filteringParameters from '@/utils/filteringParameters'
import { useAccessGuard } from '@/composables/accessGuard'

export default {
  components: {
    NNTable,
    CrfAliasForm,
    ActionsMenu,
    ConfirmDialog,
  },
  inject: ['eventBusEmit'],
  setup() {
    return {
      ...useAccessGuard(),
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
          click: this.edit,
        },
        {
          label: this.$t('_global.delete'),
          icon: 'mdi-delete-outline',
          iconColor: 'error',
          condition: (item) =>
            item.possible_actions.find((action) => action === 'delete'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.delete,
        },
      ],
      headers: [
        { title: '', key: 'actions' },
        { title: this.$t('CrfAliases.context'), key: 'context' },
        { title: this.$t('_global.name'), key: 'name' },
      ],
      showForm: false,
      filters: '',
      total: 0,
      aliases: [],
      editItem: {},
    }
  },
  watch: {
    options: {
      handler() {
        this.getAliases()
      },
      deep: true,
    },
  },
  methods: {
    async delete(item) {
      const options = {
        type: 'warning',
        cancelLabel: this.$t('_global.cancel'),
        agreeLabel: this.$t('_global.continue'),
      }
      if (
        await this.$refs.confirm.open(
          this.$t('CrfAliases.delete_approve'),
          options
        )
      ) {
        crfs.deleteAlias(item.uid).then(() => {
          this.eventBusEmit('notification', {
            msg: this.$t('CrfAliases.alias_deleted'),
          })
          this.getAliases()
        })
      }
    },
    edit(item) {
      this.editItem = item
      this.showForm = true
    },
    openForm() {
      this.showForm = true
    },
    closeForm() {
      this.showForm = false
      this.editItem = {}
      this.getAliases()
    },
    getAliases(filters, options, filtersUpdated) {
      const params = filteringParameters.prepareParameters(
        options,
        filters,
        filtersUpdated
      )
      crfs.getAllAliases(params).then((resp) => {
        this.aliases = resp.data.items
        this.total = resp.data.total
      })
    },
  },
}
</script>
