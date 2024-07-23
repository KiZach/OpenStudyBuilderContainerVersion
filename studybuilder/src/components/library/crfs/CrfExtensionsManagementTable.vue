<template>
  <div>
    <v-data-table
      :headers="selectedExtensionsHeaders"
      :items="selectedExtensions"
    >
      <template #bottom />
      <template #[`item.value`]="{ index }">
        <v-text-field
          v-model="selectedExtensions[index].value"
          :label="$t('_global.value')"
          density="compact"
          class="mt-3"
          :readonly="readOnly"
        />
      </template>
      <template #[`item.delete`]="{ item }">
        <v-btn
          icon="mdi-delete-outline"
          class="mt-1"
          variant="text"
          :disabled="readOnly"
          @click="removeExtension(item)"
        />
      </template>
    </v-data-table>
    <v-row>
      <v-col class="pt-0 mt-0">
        <NNTable
          :headers="extensionsHeaders"
          item-value="uid"
          :items="elements"
          :items-length="total"
          hide-export-button
          disable-filtering
          :modifiable-table="false"
          hide-default-switches
          additional-margin
          @filter="getExtensionData"
        >
          <template #item="{ item }">
            <tr>
              <td width="25%">
                {{ item.name }}
              </td>
              <td width="20%">
                {{ item.vendor_namespace ? item.vendor_namespace.name : '' }}
              </td>
              <td width="20%">
                {{ item.data_type }}
              </td>
              <td width="20%">
                <v-btn
                  icon="mdi-plus"
                  :disabled="readOnly"
                  variant="text"
                  @click="addExtension(item)"
                />
              </td>
            </tr>
          </template>
        </NNTable>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import crfs from '@/api/crfs'
import NNTable from '@/components/tools/NNTable.vue'
import filteringParameters from '@/utils/filteringParameters'

const props = defineProps({
  type: {
    type: String,
    default: null,
  },
  readOnly: Boolean,
  editExtensions: {
    type: Array,
    default: null,
  },
})

const { t } = useI18n()
const emit = defineEmits(['setExtensions'])

const elements = ref([])
const total = ref(0)
const selectedExtensions = ref([])
const extensionsHeaders = [
  { title: t('_global.name'), key: 'name' },
  { title: t('CrfExtensions.namespace'), key: 'vendor_namespace.name' },
  { title: t('CrfExtensions.data_type'), key: 'data_type' },
  { title: '', key: 'add' },
]
const selectedExtensionsHeaders = [
  { title: t('CrfExtensions.namespace'), key: 'vendor_namespace.name' },
  { title: t('_global.name'), key: 'name' },
  { title: t('CrfExtensions.data_type'), key: 'data_type' },
  { title: t('_global.value'), key: 'value' },
  { title: '', key: 'delete' },
]

watch(
  () => props.editExtensions,
  (value) => {
    selectedExtensions.value = value
  }
)

onMounted(async () => {
  await getExtensionData()
  if (props.editExtensions) {
    selectedExtensions.value = props.editExtensions
  }
})

function addExtension(item) {
  if (!selectedExtensions.value.some((el) => el.uid === item.uid)) {
    selectedExtensions.value.push(item)
  }
}

function removeExtension(item) {
  selectedExtensions.value = selectedExtensions.value.filter(
    (el) => el.uid !== item.uid
  )
  emit('setExtensions', selectedExtensions.value)
}

async function getExtensionData(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  await getAttributes(params)
}

async function getAttributes(params) {
  params.filters = { vendor_element: { v: [] } }
  await crfs.getAllAttributes(params).then((resp) => {
    elements.value = resp.data.items
    total.value = resp.data.total
  })
}
</script>
