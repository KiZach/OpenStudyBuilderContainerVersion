<template>
  <SimpleFormDialog
    ref="formRef"
    :title="$t('RegistryIdentifiersForm.title')"
    :help-items="helpItems"
    :open="open"
    @close="cancel"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <v-container>
          <template
            v-for="(identifier, index) in studyConstants.REGISTRY_IDENTIFIERS"
            :key="index"
          >
            <NotApplicableField
              :clean-function="() => clear(identifier)"
              :checked="nullValueSet(identifier)"
            >
              <template #mainField="{ notApplicable }">
                <v-text-field
                  :id="identifier"
                  v-model="form[identifier]"
                  :data-cy="$t(`RegistryIdentifiersForm.${identifier}`)"
                  :label="$t(`RegistryIdentifiersForm.${identifier}`)"
                  density="compact"
                  clearable
                  :disabled="notApplicable"
                  autocomplete="off"
                />
              </template>
            </NotApplicableField>
          </template>
        </v-container>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script setup>
import { inject, ref, watch } from 'vue'
import _isEqual from 'lodash/isEqual'
import NotApplicableField from '@/components/tools/NotApplicableField.vue'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useStudiesManageStore } from '@/stores/studies-manage'
import studyConstants from '@/constants/study'
import { i18n } from '@/plugins/i18n'

const props = defineProps({
  identifiers: {
    type: Object,
    default: undefined,
  },
  open: Boolean,
})
const emit = defineEmits(['close', 'updated'])
const eventBusEmit = inject('eventBusEmit')
const studiesGeneralStore = useStudiesGeneralStore()
const studiesManageStore = useStudiesManageStore()

const form = ref({})
const formRef = ref()
const observer = ref()

const helpItems = [
  'NullFlavorSelect.label',
  'RegistryIdentifiersForm.ct_gov_id',
  'RegistryIdentifiersForm.eudract_id',
  'RegistryIdentifiersForm.universal_trial_number_utn',
  'RegistryIdentifiersForm.japanese_trial_registry_id_japic',
]

watch(
  () => props.identifiers,
  (value) => {
    form.value = JSON.parse(JSON.stringify(value))
  }
)

function getIdentifierNullValueKey(identifier) {
  return `${identifier}_null_value_code`
}

function clear(identifier) {
  const nullValueKey = getIdentifierNullValueKey(identifier)
  form.value[identifier] = null
  if (form.value[nullValueKey]) {
    form.value[nullValueKey] = null
  } else {
    form.value[nullValueKey] = {
      term_uid: i18n.t('_global.na_uid'),
      name: i18n.t('_global.not_applicable_full_name'),
    }
  }
}

function nullValueSet(identifier) {
  const nullValueKey = getIdentifierNullValueKey(identifier)
  return (
    form.value[nullValueKey] !== undefined && form.value[nullValueKey] !== null
  )
}

function close() {
  emit('close')
  observer.value.resetValidation()
}

async function cancel() {
  if (_isEqual(props.identifiers, form.value)) {
    close()
    return
  }
  const options = {
    type: 'warning',
    cancelLabel: i18n.t('_global.cancel'),
    agreeLabel: i18n.t('_global.continue'),
  }
  if (await formRef.value.confirm(i18n.t('_global.cancel_changes'), options)) {
    close()
  }
}

async function submit() {
  if (_isEqual(props.identifiers, form.value)) {
    eventBusEmit('notification', {
      msg: i18n.t('_global.no_changes'),
      type: 'info',
    })
    close()
    return
  }
  const data = {
    registry_identifiers: form.value,
  }
  try {
    await studiesManageStore.editStudyIdentification(
      studiesGeneralStore.selectedStudy.uid,
      data
    )
    emit('updated', form.value)
    eventBusEmit('notification', {
      msg: i18n.t('RegistryIdentifiersForm.update_success'),
    })
    close()
  } finally {
    formRef.value.working = false
  }
}
</script>
