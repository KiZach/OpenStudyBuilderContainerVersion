<template>
  <NNTable
    ref="tableRef"
    :headers="headers"
    :items="namespaces"
    item-value="uid"
    :items-length="total"
    column-data-resource="concepts/odms/namespaces"
    export-data-url="concepts/odms/namespaces"
    export-object-label="CRFNamespaces"
    @filter="getNamespaces"
  >
    <template #actions="">
      <v-btn
        class="ml-2"
        fab
        size="small"
        icon="mdi-plus"
        color="primary"
        :title="$t('CrfExtensions.new_namespace')"
        :disabled="!accessGuard.checkPermission($roles.LIBRARY_WRITE)"
        @click.stop="openCreateForm"
      />
    </template>
    <template #[`item.actions`]="{ item }">
      <ActionsMenu :actions="actions" :item="item" />
    </template>
    <template #[`item.status`]="{ item }">
      <StatusChip :status="item.status" />
    </template>
  </NNTable>
  <CrfExtensionsCreateForm
    :edit-item="editItem"
    :open="showCreateForm"
    @close="closeCreateForm"
  />
  <CrfExtensionsEditForm
    :edit-item="editItem"
    :open="showEditForm"
    fullscreen-form
    @close="closeEditForm"
  />
  <ConfirmDialog ref="confirmRef" :text-cols="6" :action-cols="5" />
</template>

<script setup>
import { inject, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import NNTable from '@/components/tools/NNTable.vue'
import crfs from '@/api/crfs'
import filteringParameters from '@/utils/filteringParameters'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import CrfExtensionsCreateForm from '@/components/library/crfs/CrfExtensionsCreateForm.vue'
import CrfExtensionsEditForm from '@/components/library/crfs/CrfExtensionsEditForm.vue'
import actionsConst from '@/constants/actions'
import { useAccessGuard } from '@/composables/accessGuard'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'

const accessGuard = useAccessGuard()
const eventBusEmit = inject('eventBusEmit')
const roles = inject('roles')
const { t } = useI18n()
const tableRef = ref()
const confirmRef = ref()

const actions = [
  {
    label: t('CrfExtensions.edit_extension'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === actionsConst.EDIT),
    accessRole: roles.LIBRARY_WRITE,
    click: openEditForm,
  },
  {
    label: t('CrfExtensions.edit_namespace'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === actionsConst.EDIT),
    accessRole: roles.LIBRARY_WRITE,
    click: openCreateForm,
  },
  {
    label: t('_global.approve'),
    icon: 'mdi-check-decagram',
    iconColor: 'success',
    condition: (item) =>
      item.possible_actions.find((action) => action === actionsConst.APPROVE),
    accessRole: roles.LIBRARY_WRITE,
    click: approve,
  },
  {
    label: t('_global.new_version'),
    icon: 'mdi-plus-circle-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find(
        (action) => action === actionsConst.NEW_VERSION
      ),
    accessRole: roles.LIBRARY_WRITE,
    click: newVersion,
  },
  {
    label: t('_global.inactivate'),
    icon: 'mdi-close-octagon-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find(
        (action) => action === actionsConst.INACTIVATE
      ),
    accessRole: roles.LIBRARY_WRITE,
    click: inactivate,
  },
  {
    label: t('_global.reactivate'),
    icon: 'mdi-undo-variant',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find(
        (action) => action === actionsConst.REACTIVATE
      ),
    accessRole: roles.LIBRARY_WRITE,
    click: reactivate,
  },
  {
    label: t('_global.delete'),
    icon: 'mdi-delete-outline',
    iconColor: 'error',
    condition: (item) =>
      item.possible_actions.find((action) => action === actionsConst.DELETE),
    accessRole: roles.LIBRARY_WRITE,
    click: deleteNamespace,
  },
]
const headers = [
  { title: '', key: 'actions', width: '5%' },
  { title: t('_global.name'), key: 'name' },
  { title: t('CrfExtensions.prefix'), key: 'prefix' },
  { title: t('CrfExtensions.url'), key: 'url' },
  { title: t('_global.status'), key: 'status' },
  { title: t('_global.version'), key: 'version' },
]
const total = ref(0)
const namespaces = ref([])
const showCreateForm = ref(false)
const showEditForm = ref(false)
const editItem = ref({})

function getNamespaces(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  crfs.getAllNamespaces(params).then((resp) => {
    namespaces.value = resp.data.items
    total.value = resp.data.total
  })
}

function approve(item) {
  crfs.approve('vendor-namespaces', item.uid).then(() => {
    tableRef.value.filterTable()
  })
}

function inactivate(item) {
  crfs.inactivate('vendor-namespaces', item.uid).then(() => {
    tableRef.value.filterTable()
  })
}

function reactivate(item) {
  crfs.reactivate('vendor-namespaces', item.uid).then(() => {
    tableRef.value.filterTable()
  })
}

function newVersion(item) {
  crfs.newVersion('vendor-namespaces', item.uid).then(() => {
    tableRef.value.filterTable()
  })
}
async function deleteNamespace(item) {
  const options = {
    type: 'warning',
    cancelLabel: t('_global.cancel'),
    agreeLabel: t('_global.delete'),
  }
  if (
    await confirmRef.value.open(
      t('CrfExtensions.namespace_delete_warning'),
      options
    )
  ) {
    crfs.delete('vendor-namespaces', item.uid).then(() => {
      eventBusEmit('notification', {
        msg: t('CrfExtensions.namespace_deleted'),
      })
      tableRef.value.filterTable()
    })
  }
}

function openCreateForm(item) {
  editItem.value = item.uid ? item : {}
  showCreateForm.value = true
}

function closeCreateForm() {
  editItem.value = {}
  showCreateForm.value = false
  tableRef.value.filterTable()
}

function openEditForm(item) {
  editItem.value = item
  showEditForm.value = true
}

function closeEditForm() {
  editItem.value = {}
  showEditForm.value = false
  tableRef.value.filterTable()
}
</script>
